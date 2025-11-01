import uuid
from enum import Enum

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .manager import UserManager


class Provider(Enum):
    EMAIL = "EMAIL"
    GOOGLE = "GOOGLE"
    APPLE = "APPLE"

    @classmethod
    def choices(cls):
        return [(i.name, i.value) for i in cls]


class Gender(Enum):
    male = "MALE"
    female = "FEMALE"

    @classmethod
    def choices(cls):
        return [(i.name, i.value) for i in cls]


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    gender = models.CharField(
        max_length=7, choices=Gender.choices(), default=Gender.male.value
    )
    nickname = models.CharField(max_length=10, blank=True)
    preparing_for = models.CharField(max_length=20, blank=True)
    provider = models.CharField(
        max_length=10,
        choices=Provider.choices(),
        default=Provider.EMAIL.value,
    )

    # 🔹 Required Django fields for admin access
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)  # Required for admin site
    is_superuser = models.BooleanField(default=False)  # Required for permissions
    email_verified = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "user"
        indexes = [models.Index(fields=["email"])]

    def save(self, *args, **kwargs):
        """Automatically sync `is_verified` and `is_active`."""
        self.is_verified = self.email_verified
        if self.is_superuser or self.is_staff:
            self.is_active = True  # Always active for admins
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} - {self.first_name} {self.last_name} | last login: {self.last_login}"


class UserCredit(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_tokens = models.IntegerField(default=0)  # Lifetime added
    used_tokens = models.IntegerField(default=0)  # Lifetime used
    remaining_tokens = models.IntegerField(default=0)  # Available to use
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_credits"
