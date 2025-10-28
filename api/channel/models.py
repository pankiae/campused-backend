from uuid import uuid4

from django.db import models
from django.utils import timezone

from api.user.models import User

# Create your models here.


class Channel(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    context = models.JSONField(default=list)
    title = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    token_cost = models.JSONField(default={})

    class Meta:
        db_table = "channel"
        indexes = [models.Index(fields=["user"])]
