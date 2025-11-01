from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    EmailLoginAPIView,
    ForgotPasswordAPIView,
    GoogleAuthView,
    ResetPasswordAPIView,
    SignUPView,
    UserCreditView,
    VerifyEmailAPIView,
)

urlpatterns = [
    path("signup", SignUPView.as_view(), name="signup"),
    path("signin", EmailLoginAPIView.as_view(), name="signin"),
    path("verify-email", VerifyEmailAPIView.as_view(), name="verify-email"),
    path("google-auth", GoogleAuthView.as_view(), name="google-auth"),
    path("forgot-password", ForgotPasswordAPIView.as_view(), name="forgot-password"),
    path("reset-password", ResetPasswordAPIView.as_view(), name="reset-password"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("user/credits/", UserCreditView.as_view(), name="user-credit-details"),
]
