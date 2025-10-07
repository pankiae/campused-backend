from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    """

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email=email)
        extra_fields.setdefault(
            "is_active", False
        )  # Ensure users are not active by default, need email verification
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)  # Ensures correct database usage
        return user
