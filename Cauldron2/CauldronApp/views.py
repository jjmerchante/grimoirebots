from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import ensure_csrf_cookie

import os
import logging
import requests
from urllib.parse import urlparse
from github import Github

from Cauldron2.settings import GH_CLIENT_ID, GH_CLIENT_SECRET
from CauldronApp.models import GithubUser, Dashboard, Repository, Task, CompletedTask
from CauldronApp.githubsync import GitHubSync


GH_ACCESS_OAUTH = 'https://github.com/login/oauth/access_token'
GH_URI_IDENTITY = 'https://github.com/login/oauth/authorize'

DASHBOARD_LOGS = '/dashboard_logs'

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


def github_login_callback(request):
    # Github authentication
    code = request.GET.get('code', None)
    if not code:
        return render(request, 'error.html', status=400,
                      context={'title': 'Bad Request',
                               'description': "The isn't a code in the GitHub callback"})

    r = requests.post(GH_ACCESS_OAUTH,
                      data={'client_id': GH_CLIENT_ID,
                            'client_secret': GH_CLIENT_SECRET,
                            'code': code},
                      headers={'Accept': 'application/json'})
    if r.status_code != requests.codes.ok:
        logging.error('GitHub API error %s %s %s', r.status_code, r.reason, r.text)
        return render(request, 'error.html', status=500,
                      context={'title': 'GitHub error',
                               'description': "GitHub API error"})
    token = r.json().get('access_token', None)
    if not token:
        logging.error('ERROR GitHub Token not found. %s', r.text)
        return render(request, 'error.html', status=500,
                      context={'title': 'GitHub error',
                               'description': "Error getting the token from GitHub endpoint"})

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
        return render(request, 'error.html', status=405,
                      context={'title': 'Method Not Allowed',
                               'description': "Only POST methods allowed"})
    if not request.user.is_authenticated:
        return render(request, 'error.html', status=403,
                      context={'title': 'Log in first',
                               'description': "Log in with your github account first <a href="/">go homepage</a>"})
    repo_url = request.POST.get('url', None)
    org_name = request.POST.get('gh-org', None)

    if repo_url:
        # TODO: owner/repository format
        if not valid_github_url(repo_url):
            return render(request, 'error.html', status=400,
                          context={'title': 'Invalid URL',
                                   'description': "Are you sure it's a GitHub URL? Don't try to break me :)"})
        owner, repo_name = parse_gh_url(repo_url)
        dash_name = "{}-{}".format(owner, repo_name)

        dash, created = Dashboard.objects.get_or_create(name=dash_name, defaults={'creator': request.user.githubuser})
        if created:
            fill_dashboard(dash, [repo_url + '.git'], [repo_url], request.user.githubuser)
        return HttpResponseRedirect('/dashboard/' + dash.name)

    elif org_name:
        # TODO: Check valid org_name
        dash, created = Dashboard.objects.get_or_create(name=org_name, defaults={'creator': request.user.githubuser})
        if created:
            gh_sync = GitHubSync(request.user.githubuser.token)
            git_list, github_list = gh_sync.get_repo(org_name, False)
            fill_dashboard(dash, git_list, github_list, request.user.githubuser)
        return HttpResponseRedirect('/dashboard/' + dash.name)
    else:
        return render(request, 'error.html', status=404,
                      context={'title': 'URL/owner not found',
                               'description': "We need URL, user or organization for analyzing"})


def fill_dashboard(dash, git_list, gh_list, githubuser):
    """
    Add a list of repositories to a dashboard
    :param dash: Dashboard row from db
    :param git_list: List of git repositories
    :param gh_list: List of GitHub repositories
    :param githubuser: GitHubUser row from db
    :return: None
    """
    assert len(git_list) == len(gh_list), 'Git and Github lists are not the same length for ' + dash.name
    for repo_git, repo_gh in zip(git_list, gh_list):
        repo_obj = Repository.objects.filter(url_git=repo_git).first()
        if not repo_obj:
            # Create the repo and the task
            repo_obj = Repository(url_git=repo_git, url_gh=repo_gh)
            repo_obj.save()
            task = Task(repository=repo_obj, gh_user=githubuser)
            task.save()
        # Add the repo to the dashboard
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
        status_repo = get_repo_status(repo)

        status['repos'].append({'id': repo.id, 'status': status_repo})
        if status_repo == 'RUNNING':
            status['general'] = 'RUNNING'
        elif status_repo == 'PENDING' and (status['general'] != 'RUNNING'):
            status['general'] = 'PENDING'
        elif (status_repo == 'ERROR') and (status['general'] not in ('RUNNING', 'PENDING')):
            status['general'] = 'ERROR'
        elif (status_repo == 'COMPLETED') and (status['general'] not in ('RUNNING', 'PENDING', 'ERROR')):
            status['general'] = 'COMPLETED'
    return status


@ensure_csrf_cookie  # For Ajax, just in case
def show_dashboard(request, dash_name):
    if request.method != 'GET':
        return render(request, 'error.html', status=405,
                      context={'title': 'Method Not Allowed',
                               'description': "Only GET methods allowed"})
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
        return render(request, 'error.html', status=405,
                      context={'title': 'Method Not Allowed',
                               'description': "Only GET methods allowed"})
    repos = Repository.objects.filter(dashboards__name=dash_name)
    if len(repos) == 0:
        return JsonResponse({'exists': False})
    for repo in repos:
        repo_status = get_repo_status(repo)
        logfile = '{}/repository_{}.log'.format(DASHBOARD_LOGS, repo.id)
        output += "<strong>{}</strong>\n".format(repo.url_gh)
        if not os.path.isfile(logfile):
            output += "{}\n".format(repo_status)
            continue
        output += open(logfile, 'r').read() + '\n'
        if repo_status in ('PENDING', 'RUNNING'):
            more = True

    response = {
        'exists': True,
        'content': output,
        'more': more
    }

    return JsonResponse(response)


def repo_status(request, repo_id):
    if request.method != 'GET':
        return render(request, 'error.html', status=405,
                      context={'title': 'Method Not Allowed',
                               'description': "Only GET methods allowed"})
    repo = Repository.objects.filter(id=repo_id).first()
    if not repo:
        return JsonResponse({'status': 'UNKNOWN'})
    return JsonResponse({'status': get_repo_status(repo)})


def dash_status(request, dash_name):
    status = get_dashboard_status(dash_name)
    return JsonResponse({'status': status})


def parse_gh_url(url):
    """
    Should be validated by valid_github_url
    :param url:
    :return:
    """
    o = urlparse(url)
    return o.path.split('/')[1:]


def valid_github_url(url):
    o = urlparse(url)
    print(o)
    return (o.scheme == 'https' and
            o.netloc == 'github.com' and
            len(o.path.split('/')) == 3)


def get_repo_status(repo):
    """
    Check if there is a task associated or it has been completed
    :param repo: Repository object from the database
    :return: status (PENDING, RUNNING, COMPLETED)
    """
    if hasattr(repo, 'task'):
        # PENDING OR RUNNING
        if repo.task.worker_id:
            return 'RUNNING'
        else:
            return 'PENDING'
    else:
        return 'COMPLETED'
