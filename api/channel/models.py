from uuid import uuid4

from django.db import models
from django.utils import timezone

from api.user.models import User

# Create your models here.


class Channel(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    context = models.JSONField(default=list)
    title = models.CharField(max_length=50)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    token_cost = models.JSONField(default=dict)

    class Meta:
        db_table = "channel"
        indexes = [models.Index(fields=["user"])]


class Exam(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.CharField(max_length=20)
    subject = models.CharField(max_length=20)
    difficulty = models.CharField(max_length=10)
    language = models.CharField(max_length=20)
    mode = models.CharField(max_length=20)
    questions_answers = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    token_cost = models.JSONField(default=dict)

    class Meta:
        db_table = "exam"
        indexes = [models.Index(fields=["user"])]

    def __str__(self):
        return f"{self.id} - {self.user} - {self.updated_at}"
