from django.db import models
from django.utils.translation import gettext_lazy as _


class RequestMethodTypes(models.IntegerChoices):
    GET = 0, _("GET")
    POST = 1, _("POST")


class Page(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    url = models.URLField()
    request_method = models.PositiveSmallIntegerField(
        choices=RequestMethodTypes.choices,
    )
    response_status_code = models.PositiveSmallIntegerField()
    last_checked = models.DateTimeField()
    last_success = models.DateTimeField()
    last_failure = models.DateTimeField()
    last_notified = models.DateTimeField()

    def __str__(self):
        return self.name
