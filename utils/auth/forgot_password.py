from datetime import timedelta

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from .send_html_email import _send_html_email


def send_password_reset_email(user, request):
    """
    Generate a 1-hour “password_reset” JWT, build reset URL,
    then call _send_html_email(...) to send the “Reset Password” email.
    """
    # 1) Create a 1-hour JWT and mark it with a custom claim
    token = AccessToken.for_user(user)
    token["password_reset"] = True
    token.set_exp(lifetime=timedelta(hours=1))
    token_str = str(token)

    # 2) Build the password-reset URL to be included in the email
    frontend_url = settings.FRONTEND_URL  # Get the frontend URL from settings
    reset_url = f"{frontend_url}/reset-password?token={token_str}"

    # 3) Prepare context & subject
    subject = "Reset Your Password"
    context = {
        "name": user.first_name,
        "reset_url": reset_url,
        "current_year": timezone.now().year,
    }

    # 4) Use the shared helper
    _send_html_email(
        subject=subject,
        template_filename="reset_password_email.html",
        context=context,
        recipient_email=user.email,
    )
