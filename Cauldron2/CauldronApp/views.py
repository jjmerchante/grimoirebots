from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError, HttpResponseRedirect, JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import ensure_csrf_cookie

import os
import logging
import requests
from github import Github

from Cauldron2.settings_secret import GH_CLIENT_ID, GH_CLIENT_SECRET
from CauldronApp.models import GithubUser, Dashboard, Repository
from CauldronApp.githubsync import GitHubSync


GH_ACCESS_OAUTH = 'https://github.com/login/oauth/access_token'
GH_URI_IDENTITY = 'https://github.com/login/oauth/authorize'


def homepage(request):
    context = dict()
    if request.user.is_authenticated:
        context['auth_user'] = request.user

    dashboards = Dashboard.objects.filter()
    context_dbs = []
    for db in dashboards:
        status = get_dashboard_status(db.name)

        completed = sum(1 for repo in status['repos'] if repo['status'] == 'COMPLETED')
        context_dbs.append({'status': status['general'],
                            'name': db.name,
                            'completed': completed,
                            'total': len(status['repos'])})

    context['dashboards'] = context_dbs
    context['gh_uri_identity'] = GH_URI_IDENTITY
    context['gh_client_id'] = GH_CLIENT_ID

    return render(request, 'index.html', context=context)


# TODO: Make templates for bad request and errors from GitHub endpoint
def github_login_callback(request):
    # Github authentication
    code = request.GET.get('code', None)
    if not code:
        return HttpResponseBadRequest("There isn't a code in the request")
    r = requests.post(GH_ACCESS_OAUTH,
                      data={'client_id': GH_CLIENT_ID,
                            'client_secret': GH_CLIENT_SECRET,
                            'code': code},
                      headers={'Accept': 'application/json'})
    if r.status_code != requests.codes.ok:
        logging.error('GitHub API error %s %s %s', r.status_code, r.reason, r.text)
        return HttpResponseServerError('Error: GitHub endpoint')
    token = r.json().get('access_token', None)
    if not token:
        logging.error('ERROR GitHub Token not found. %s', r.text)
        return HttpResponseServerError("Error. Couldn't retrieve a valid token")

    # Authenticate/register an user, and login
    gh = Github(token)
    gh_user = gh.get_user()
    dj_user = User.objects.filter(username=gh_user.login).first()
    if not dj_user:
        dj_user = User.objects.create_user(username=gh_user.login)
        dj_user.set_unusable_password()
        dj_user.save()

    # Delete previous token and Update/Add the new token
    previous_token = GithubUser.objects.filter(user=dj_user).first()
    if previous_token:
        previous_token.token = token
        previous_token.save()
    else:
        token_entry = GithubUser(user=dj_user, token=token)
        token_entry.save()

    login(request, dj_user)

    return HttpResponseRedirect('/')


def github_logout(request):
    logout(request)
    return HttpResponseRedirect('/')


def create_dashboard(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Only allow POST')
    if not request.user.is_authenticated:
        return HttpResponse('Log in with your github account first <a href="/">go homepage</a>')  # TODO: template?
    repo_url = request.POST.get('url', None)
    org_name = request.POST.get('gh-org', None)

    if repo_url:
        owner, repo_name = parse_gh_url(repo_url)
        dash_name = "{}-{}".format(owner, repo_name)

        dash, created = Dashboard.objects.get_or_create(name=dash_name, defaults={'creator': request.user.githubuser})
        if created:
            fill_dashboard(dash, [repo_url + '.git'], [repo_url], request.user.githubuser)
        return HttpResponseRedirect('/dashboard/' + dash.name)

    elif org_name:
        gh_sync = GitHubSync(request.user.githubuser.token)
        git_list, github_list = gh_sync.get_repo(org_name, False)
        dash, created = Dashboard.objects.get_or_create(name=org_name, defaults={'creator': request.user.githubuser})
        if not created:
            return HttpResponseRedirect('/dashboard/' + dash.name)
        fill_dashboard(dash, git_list, github_list, request.user.githubuser)
        return HttpResponseRedirect('/dashboard/' + dash.name)
    else:
        return HttpResponseBadRequest('We need URL, user or organization for analyzing')


def fill_dashboard(dash, git_list, gh_list, githubuser):
    assert len(git_list) == len(gh_list), 'Git and Github lists are not the same length for ' + dash.name
    for repo_git, repo_gh in zip(git_list, gh_list):
        repo_obj = Repository.objects.filter(url_git=repo_git).first()
        if not repo_obj:
            repo_obj = Repository(
                url_git=repo_git,
                url_gh=repo_gh,
                gh_token=githubuser,
                status='PENDING')
            repo_obj.save()
            repo_obj.dashboards.add(dash)
        else:
            repo_obj.dashboards.add(dash)


def get_dashboard_status(dash_name):
    """
    General status:
    If no repos -> UNKNOWN
    1. If any repo is running -> return RUNNING
    2. Else if any repo pending -> return PENDING
    3. Else if any repo error -> return ERROR
    4. Else -> return COMPLETED
    :param dash_name: name of the dashboard
    :return: Status of the dashboard depending on the the previous rules
    """
    repos = Repository.objects.filter(dashboards__name=dash_name)
    if len(repos) == 0:
        return {
            'repos': [],
            'general': 'UNKNOWN',
            'exists': False
        }
    status = {
        'repos': [],
        'general': 'UNKNOWN',
        'exists': True
    }
    for repo in repos:
        status['repos'].append({'id': repo.id, 'status': repo.status})
        if repo.status == 'RUNNING':
            status['general'] = 'RUNNING'
            break  # Nothing more to do, it is running
        elif repo.status == 'PENDING':
            status['general'] = 'PENDING'
        elif (repo.status == 'ERROR') and (status != 'PENDING'):
            status['general'] = 'ERROR'
        elif (repo.status == 'COMPLETED') and (status not in ('PENDING', 'ERROR')):
            status['general'] = 'COMPLETED'
    return status


@ensure_csrf_cookie
def show_dashboard(request, dash_name):
    if request.method != 'GET':
        return HttpResponseBadRequest('Only allow GET')
    dash = Dashboard.objects.filter(name=dash_name).first()
    # CREATE RESPONSE
    context = dict()
    if request.user.is_authenticated:
        context['auth_user'] = request.user

    if dash:
        context['dashboard'] = dash
        context['dashboard_status'] = get_dashboard_status(dash_name)['general']
        context['repositories'] = Repository.objects.filter(dashboards__name=dash_name)

    return render(request, 'dashboard.html', context=context)


def dash_logs(request, dash_name):
    output = ""
    more = False
    if request.method != 'GET':
        return HttpResponseBadRequest('Only allow GET')
    repos = Repository.objects.filter(dashboards__name=dash_name)
    if len(repos) == 0:
        return JsonResponse({'exists': False})
    for repo in repos:
        logfile = 'MordredManager/dashboards_logs/repository_{}.log'.format(repo.id)
        output += "<strong>{}</strong>\n".format(repo.url_gh)
        if not os.path.isfile(logfile):
            output += "{}\n".format(repo.status)
            continue
        output += open(logfile, 'r').read() + '\n'
        if repo.status in ('PENDING', 'RUNNING'):
            more = True

    response = {
        'exists': True,
        'content': output,
        'more': more
    }

    return JsonResponse(response)


def repo_status(request, repo_id):
    if request.method != 'GET':
        return HttpResponseBadRequest('Only allow GET')
    repo = Repository.objects.filter(id=repo_id).first()
    if not repo:
        return JsonResponse({'status': 'UNKNOWN'})
    return JsonResponse({'status': repo.status})


def dash_status(request, dash_name):
    status = get_dashboard_status(dash_name)
    return JsonResponse({'status': status})


def parse_gh_url(url):
    owner = url.split('/')[-2]
    repo = url.split('/')[-1]
    return owner, repo
