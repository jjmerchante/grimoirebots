from django.db import models
from django.contrib.auth.models import User

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_status(status):
    if status not in ('PENDING', 'RUNNING', 'COMPLETED', 'ERROR'):
        raise ValidationError(
            _('%(status)s is not a valid status'),
            params={'status': status},
        )


# Create your models here.
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
    """
    status: PENDING, RUNNING, COMPLETED, ERROR
    """
    url_gh = models.URLField()
    url_git = models.URLField()
    dashboards = models.ManyToManyField(Dashboard)
    last_modified = models.DateTimeField(auto_now=True)
    gh_token = models.ForeignKey(GithubUser, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, validators=[validate_status])
