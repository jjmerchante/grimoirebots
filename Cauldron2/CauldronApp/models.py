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
class GithubToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)


class Task(models.Model):
    """
    status: PENDING, RUNNING, COMPLETED
    """
    url = models.URLField()
    status = models.CharField(max_length=15, validators=[validate_status])
    last_modified = models.DateTimeField(auto_now=True)
    gh_token = models.ForeignKey(GithubToken, on_delete=models.CASCADE)

