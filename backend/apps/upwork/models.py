from django.db import models


class JobFeed(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    url = models.URLField(max_length=1000)
    last_polled = models.DateTimeField(
        blank=True,
        null=True,
    )
    recipients = models.CharField(max_length=1000)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
