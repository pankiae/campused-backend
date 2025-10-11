from datetime import timedelta

from django.utils import timezone
from google.auth.transport import requests
from google.oauth2 import id_token as google_id_token
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from campused.settings import GOOGLE_CLIENT_ID
from utils.account_activation import send_activation_email

from .models import Provider, User
from .serializers import (
    EmailLoginSerializer,
    EmailRegistrationSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)


class SignUPView(GenericAPIView):
    serializer_class = EmailRegistrationSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get("email", "").strip().lower()
        if not email:
            return Response(
                {"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        now = timezone.now()

        try:
            existing = User.objects.get(email=email)
        except User.DoesNotExist:
            existing = None

        if existing:
            # If already verified → email is taken
            if existing.is_verified:
                return Response(
                    {"error": "A user with this email already exists and is active."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Not verified yet:
            age = now - existing.created_at
            if age > timedelta(hours=24):
                # It’s been more than 24 hours since they signed up, but they never clicked
                # “activate.” Let’s treat this as “refresh”:
                #   1) update created_at so that we can give them another 24 hours window, and
                #   2) resend the activation email.
                existing.created_at = now
                existing.save(update_fields=["created_at"])

                send_activation_email(existing, request)
                return Response(
                    {
                        "detail": (
                            "Your previous activation link expired. "
                            "We’ve generated a fresh link (valid for 24 hours) and sent it to your email. "
                            "You can only request a new link once every 24 hours."
                        )
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                # They signed up less than 24 hours ago and haven’t verified yet:
                return Response(
                    {
                        "detail": (
                            "You haven’t activated your account yet. "
                            "Please check your email for the activation link. "
                            "A new link can only be generated once every 24 hours."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # If we reach here → no existing user, or we purposely “refreshed” above
        try:
            serializer = self.get_serializer(
                data=request.data,
                context={"exclude_fields": ["id"]},
            )
            serializer.is_valid(raise_exception=True)
            user = (
                serializer.save()
            )  # new user (or you could reuse existing if you deleted it)
            send_activation_email(user, request)

            return Response(
                {
                    "detail": (
                        "Registration successful. Check your email to activate your account. "
                        "This activation link can only be generated once every 24 hours."
                    )
                },
                status=status.HTTP_201_CREATED,
            )

        except ValidationError as e:
            return Response(
                {"error": "Validation failed", "details": e.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyEmailAPIView(APIView):
    """
    GET /api/auth/verify-email/?token=<jwt>
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        token_str = request.query_params.get("token", None)
        if token_str is None:
            return Response(
                {"detail": "Token not provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 1) Decode + verify signature + expiry
            access_token = AccessToken(token_str)
            print(access_token)
            # If signature is invalid or expired, this will raise TokenError / InvalidToken
        except (TokenError, InvalidToken) as e:
            print(e)
            return Response(
                {"detail": "Activation link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2) Extract user_id from token payload
        user_id = access_token.get("user_id")
        print(user_id)
        if user_id is None:
            return Response(
                {"detail": "Token payload missing user information."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3) Activate the user (if they exist)
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User does not exist."}, status=status.HTTP_404_NOT_FOUND
            )

        if user.is_active:
            # Perhaps the user already clicked once
            return Response(
                {"detail": "Account is already active."}, status=status.HTTP_200_OK
            )

        # 4) Mark as active
        user.email_verified = True
        user.save()

        return Response(
            {"detail": "Email verified successfully. Your account is now active."},
            status=status.HTTP_200_OK,
        )


class EmailLoginAPIView(GenericAPIView):
    """
    POST /api/auth/login/
    Body: { "email": "...", "password": "..." }
    Returns: { "refresh": "...", "access": "..." } if credentials and is_active=True.
    """

    serializer_class = EmailLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # This will call EmailLoginSerializer.validate(...)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class GoogleAuthView(GenericAPIView):
    def post(self, request, *args, **kwargs):
        id_token_value = request.data.get("id_token")
        print("ID Token:", id_token_value)
        if not id_token_value:
            return Response(
                {"message": "Google ID token is required.", "status": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Verify and decode the token
            idinfo = google_id_token.verify_oauth2_token(
                id_token_value, requests.Request(), GOOGLE_CLIENT_ID
            )
            print("ID Info:", idinfo)
            email = idinfo.get("email")
            name = idinfo.get("name")
            email_verified = idinfo.get("email_verified", False)

            if not email:
                return Response(
                    {
                        "message": "Email is missing in the Google ID token.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Split name into first/last
            if name and " " in name:
                first_name, last_name = name.split(" ", 1)
            else:
                first_name = name or ""
                last_name = ""

            # Create or fetch the user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email_verified": email_verified,
                    "provider": Provider.GOOGLE.value,
                },
            )

            # If the user already existed but your app wants to mark email_verified=True:
            if not created and not user.email_verified and email_verified:
                user.email_verified = True
                user.save(update_fields=["email_verified"])

            # Build a new RefreshToken for this user
            refresh = RefreshToken.for_user(user)
            access_token_str = str(refresh.access_token)
            name = user.first_name + " " + user.last_name if user.last_name else ""
            return Response(
                {
                    "message": "Google OAuth2 successful.",
                    "access_token": access_token_str,
                    "name": name,
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            # Raised by google_id_token.verify_oauth2_token on invalid/expired token
            return Response(
                {
                    "message": "Invalid Google ID token.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {
                    "message": "An error occurred while processing the Google ID token.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ForgotPasswordAPIView(GenericAPIView):
    """
    POST /api/auth/forgot-password/
    Body: { "email": "user@example.com" }

    - If the email is valid and belongs to an active user, sends a reset link.
    - Returns 200 with a generic “link sent” message.
    """

    serializer_class = ForgotPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Password reset link has been sent to your email."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordAPIView(GenericAPIView):
    """
    POST /api/auth/reset-password/
    Body: { "token": "<jwt>", "new_password": "..." }

    - Validates the token and new_password.
    - If valid, updates the user’s password.
    - Returns 200 on success.
    """

    serializer_class = ResetPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )
