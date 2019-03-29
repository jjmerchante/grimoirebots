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
from CauldronApp.models import GithubToken, Task


GH_ACCESS_OAUTH = 'https://github.com/login/oauth/access_token'
GH_URI_IDENTITY = 'https://github.com/login/oauth/authorize'


def homepage(request):
    context = dict()
    if request.user.is_authenticated:
        context['authenticated'] = True
        context['authenticated_username'] = request.user.username
    else:
        context['authenticated'] = False

    tasks = Task.objects.filter()
    context['dashboards'] = tasks
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
    previous_token = GithubToken.objects.filter(user=dj_user).first()
    if previous_token:
        previous_token.delete()
    token_entry = GithubToken(user=dj_user, token=token)
    token_entry.save()

    login(request, dj_user)

    return HttpResponseRedirect('/')


def github_logout(request):
    # TODO: Delete the token?
    logout(request)
    return HttpResponseRedirect('/')


def create_dashboard(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Only allow POST')
    if not request.user.is_authenticated:
        return HttpResponse('Log in with your github account first <a href="/">go homepage</a>')  # TODO: More detailed error
    repo_url = request.POST.get('url', None)
    if not repo_url:
        return HttpResponseBadRequest('We need a URL for analyzing')

    obj, _ = Task.objects.get_or_create(
        url=repo_url,
        defaults={'status': 'PENDING', 'gh_token': request.user.githubtoken},
    )
    # run_mordred(repo_url, request.user.githubtoken.token)

    if obj:
        # TODO: Change to another ID? User / repository name
        return HttpResponseRedirect('/dashboard/{}'.format(obj.id))
    else:
        # TODO: More detailed error
        return HttpResponseServerError('Something wrong happens')


@ensure_csrf_cookie
def show_dashboard_info(request, dash_id):
    dash_task = Task.objects.filter(id=dash_id).first()
    # CREATE RESPONSE
    context = dict()
    if request.user.is_authenticated:
        context['authenticated'] = True
        context['authenticated_username'] = request.user.username
    else:
        context['authenticated'] = False

    if dash_task:
        context['dashboard'] = dash_task

    return render(request, 'dashboard.html', context=context)


def dash_logs(request, dash_id):
    logfile = 'MordredManager/dashboards_logs/dashboard_{}.log'.format(dash_id)
    task = Task.objects.filter(id=dash_id).first()
    if not task:
        return JsonResponse({'exists': False})
    if not os.path.isfile(logfile):
        # File not found but there is a task
        return JsonResponse({'exists': True,
                            'ready': False})
    logs = {
        'exists': True,
        'ready': True,
        'dash_id': dash_id,
        'content': open(logfile, 'r').read(),
        'more': True if task.status in ('RUNNING', 'PENDING') else False
    }
    return JsonResponse(logs)


def dash_status(request, dash_id):
    task = Task.objects.filter(id=dash_id).first()
    if not task:
        return JsonResponse({'status': 'UNKNOWN'})
    return JsonResponse({'status': task.status})
