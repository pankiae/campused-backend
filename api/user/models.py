import uuid
from enum import Enum

from django.contrib.auth.models import AbstractBaseUser
from django.db import models

from .manager import UserManager


class Provider(Enum):
    EMAIL = "EMAIL"
    GOOGLE = "GOOGLE"
    APPLE = "APPLE"

    @classmethod
    def choices(cls):
        return [(i.name, i.value) for i in cls]


class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    provider = models.CharField(
        max_length=10,
        choices=Provider.choices(),
        default=Provider.EMAIL.value,  # Default to email provider
    )
    is_active = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    phone_number_verified = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone_number"]

    class Meta:
        db_table = "user"
        indexes = [models.Index(fields=["email", "phone_number"])]

    def save(self, *args, **kwargs):
        """Automatically set `is_verified` when both email and phone are verified."""
        self.is_verified = self.email_verified and self.phone_number_verified
        self.is_active = True if self.is_verified else False
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.email}/{self.phone_number} : {self.created_at} - {self.is_active}"
        )
