# users/utils.py

from datetime import timedelta

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from .send_html_email import _send_html_email


def send_activation_email(user, request):
    """
    Generate a 1-day JWT (with user_id), build activation URL,
    then call _send_html_email(...) to deliver the “Activate Account” email.
    """
    # 1) Create a 1-day JWT for this user
    token = AccessToken.for_user(user)
    token.set_exp(lifetime=timedelta(days=1))
    token_str = str(token)

    # 2) Build activation link: https://<domain>/api/verify-email?token=<jwt>
    frontend_url = settings.FRONTEND_URL  # Get the frontend URL from settings
    activation_url = f"{frontend_url}/verify-email?token={token_str}"

    # 3) Prepare context & subject
    subject = "Activate Your Account"
    context = {
        "name": user.first_name,
        "activation_url": activation_url,
        "current_year": timezone.now().year,
    }

    # 4) Use the shared helper
    _send_html_email(
        subject=subject,
        template_filename="activation_email.html",
        context=context,
        recipient_email=user.email,
    )
