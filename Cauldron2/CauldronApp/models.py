from django.db import models
from django.contrib.auth.models import User


class GithubUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    token = models.CharField(max_length=100)


class Dashboard(models.Model):
    name = models.CharField(max_length=255, unique=True)
    creator = models.ForeignKey(GithubUser,
                                on_delete=models.SET_NULL,
                                blank=True,
                                null=True)


class Repository(models.Model):
    url_gh = models.URLField()
    url_git = models.URLField()
    dashboards = models.ManyToManyField(Dashboard)


class Task(models.Model):
    """
    When a worker takes one:
    - Update the worker ID
    - Update the started date
    When a worker finishes one:
    - Create a completedTask
    - Delete this task
    """
    repository = models.OneToOneField(Repository, on_delete=models.CASCADE)
    gh_user = models.ForeignKey(GithubUser, on_delete=models.CASCADE)
    worker_id = models.CharField(max_length=255, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(null=True)


class CompletedTask(models.Model):
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    gh_user = models.ForeignKey(GithubUser, on_delete=models.SET_NULL, blank=True, null=True)
    created = models.DateTimeField()
    started = models.DateTimeField()
    completed = models.DateTimeField()
    status = models.CharField(max_length=255)
