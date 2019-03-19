from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError, HttpResponseRedirect
from django.contrib.auth import login, logout
from django.contrib.auth.models import User

import requests
from github import Github

from Cauldron2.settings_secret import GH_CLIENT_ID, GH_CLIENT_SECRET
from CauldronApp.models import GithubToken, Task


GH_ACCESS_OAUTH = 'https://github.com/login/oauth/access_token'
GH_REDIRECT_URI = 'http://localhost:8000/github-login'


# Create your views here.
def homepage(request):
    # TODO: Check if we have the user authenticated
    context = dict()
    if request.user.is_authenticated:
        context['authenticated'] = True
        context['authenticated_username'] = request.user.username
    else:
        context['authenticated'] = False

    context['gh_uri_identity'] = "https://github.com/login/oauth/authorize"
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
        print('ERROR GitHub API', r.status_code, r.reason, r.text)
        return HttpResponseServerError('Error: GitHub endpoint')
    token = r.json().get('access_token', None)
    if not token:
        print('ERROR GitHub Token not found', r.text)
        return HttpResponseServerError("Error. Couldn't retrieve a valid token")

    # Authenticate/register an user, and login
    gh = Github(token)
    gh_user = gh.get_user()
    dj_user = User.objects.filter(username=gh_user.login).first()
    if dj_user:
        print('This user was already here!')
    else:
        print('New user!')
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


# TODO: @login_required
def create_dashboard(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Only allow POST')
    if not request.user.is_authenticated:
        return HttpResponse('Log in with your github account first <a href="/">go homepage</a>')  # TODO: More detailed error
    repo_url = request.POST.get('url', None)
    if not repo_url:
        return HttpResponseBadRequest('We need a URL for analyzing')

    obj, created = Task.objects.get_or_create(
        url=repo_url,
        defaults={'status': 'PENDING', 'gh_token': request.user.githubtoken},
    )
    # run_mordred(repo_url, request.user.githubtoken.token)

    if obj:
        # TODO: Change to another ID (random)?
        return HttpResponseRedirect('/dashboard/{}'.format(obj.id))
    else:
        # TODO: More detailed errors
        return HttpResponseServerError('Something wrong happens')


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
        context['dash_status'] = dash_task.status
    else:
        context['dash_status'] = "There was an error. No information about this dashboard. Try to reload."

    return render(request, 'dashboard.html', context=context)
