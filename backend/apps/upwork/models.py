from django.db import models


class JobFeed(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(
        null=True,
        blank=True,
    )
    url = models.URLField(max_length=1000)
    last_polled = models.DateTimeField(
        blank=True,
        null=True,
    )
    recipients = models.CharField(max_length=1000)
    active = models.BooleanField(default=True)
    assistant_id = models.CharField(
        max_length=250,
        null=True,
        blank=True,
    )
    assistant_instructions = models.TextField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name
