from uuid import uuid4

from django.db import models

from api.user.models import User

# Create your models here.

class Channel(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    context = models.JSONField(default=list)
    title = models.CharField(max_length=20)

    class Meta:
        db_table = "channel"
        indexes = [models.Index(fields=["user"])]
