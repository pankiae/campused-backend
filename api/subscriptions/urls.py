from django.urls import path

from .views import CreateOrderView, RazorpayWebhookView, VerifyPaymentView

urlpatterns = [
    path("create-order", CreateOrderView.as_view(), name="create-order"),
    path("verify-payment", VerifyPaymentView.as_view(), name="verify-payment"),
    path("webhook/razorpay", RazorpayWebhookView.as_view(), name="webhook-razorpay"),
]
