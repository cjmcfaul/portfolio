import uuid

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property


class BaseModel(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )
    modified = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        abstract = True

    @cached_property
    def get_content_type(self):
        return ContentType.objects.get_for_model(self)
