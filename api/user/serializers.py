# serializers.py
from datetime import timedelta

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import (
    AccessToken,
    RefreshToken,
)

from utils.auth.forgot_password import send_password_reset_email

User = get_user_model()


class EmailRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={
            "input_type": "password"
        },  # optional, makes DRF’s browsable API show dots
    )

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "password",
            "gender",
            "nickname",
            "preparing_for",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        # Ensure email is stored in lowercase
        return value.strip().lower()

    def validate_preparing_for(self, value):
        return value.upper() if value else value

    def validate_gender(self, value):
        return value.upper() if value else value

    def create(self, validated_data):
        # Remove password from validated_data, then call your UserManager.create_user()
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     exclude_fields = self.context.get("exclude_fields", [])
    #     for field in exclude_fields:
    #         data.pop(field, None)
    #     return data


class EmailLoginSerializer(serializers.Serializer):
    """
    Accepts: { "email": "...", "password": "..." }
    Returns on success: { "refresh": "...", "access": "..." }
    Raises AuthenticationFailed if: no such user, bad password, or not active.
    """

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    # These fields will be returned on successful login
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def validate(self, attrs):
        email = attrs.get("email", "").strip().lower()
        password = attrs.get("password", "")

        # 1) Check that a user with this email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed("Invalid credentials.")

        # 2) Verify password
        if not user.check_password(password):
            raise AuthenticationFailed("Invalid credentials.")

        # 3) Ensure user.is_active
        if not user.is_active:
            raise AuthenticationFailed(
                "Account is not activated. Please verify your email before logging in."
            )

        # 4) If all good, create JWT tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        access.set_exp(lifetime=timedelta(days=1))
        name = user.first_name + " " + user.last_name if user.last_name else ""
        return {
            # "refresh": str(refresh),
            "message": "Login successful.",
            "access_token": str(access),
            "name": name,
        }


class ForgotPasswordSerializer(serializers.Serializer):
    """
    Accepts:
        { "email": "user@example.com" }

    - Validates that an active user with that email exists.
    - In `save()`, calls send_password_reset_email(user, request).
    """

    email = serializers.EmailField(write_only=True)

    def validate_email(self, value):
        email = value.strip().lower()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise ValidationError("No account is registered with this email.")
        if not user.is_active:
            raise ValidationError(
                "Account is not activated. Please verify your email first."
            )
        # Store user for use in save()
        self.user = user
        return email

    def save(self, **kwargs):
        """
        Send the reset‐password email by calling the helper.
        We expect `self.user` to have been set in validate_email().
        """
        request = self.context.get("request")
        send_password_reset_email(self.user, request)


class ResetPasswordSerializer(serializers.Serializer):
    """
    Accepts:
        {
            "token": "<jwt>",
            "new_password": "...",
            "confirm_password": "..."
        }
    - Validates that new_password and confirm_password match and meet length requirements.
    - Validates the token (signature, expiry, and 'password_reset' claim).
    - In save(), sets user.set_password(new_password).
    """

    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True, min_length=8, trim_whitespace=False
    )
    confirm_password = serializers.CharField(
        write_only=True, min_length=8, trim_whitespace=False
    )

    def validate_token(self, value):
        try:
            access_token = AccessToken(value)
        except (TokenError, InvalidToken):
            raise ValidationError("Invalid or expired token.")

        if not access_token.get("password_reset", False):
            raise ValidationError("This token cannot be used for password reset.")

        user_id = access_token.get("user_id")
        if not user_id:
            raise ValidationError("Token payload missing user information.")
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise ValidationError("User not found for this token.")

        self.user = user
        return value

    def validate(self, attrs):
        new_pw = attrs.get("new_password")
        confirm_pw = attrs.get("confirm_password")
        if new_pw != confirm_pw:
            raise ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def save(self, **kwargs):
        new_password = self.validated_data["new_password"]
        self.user.set_password(new_password)
        self.user.save()
