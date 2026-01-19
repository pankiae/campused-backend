import hashlib
import hmac
import json
import logging

import razorpay
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.subscription_logic.main import activate_subscription

from .models import Order, SubscriptionPlan
from .serializers import SubscriptionPlanSerializer

logger = logging.getLogger(__name__)


class SubscriptionPlanListView(APIView):
    """Public API to list all available subscription plans."""

    permission_classes = [AllowAny]

    def get(self, request):
        plans = SubscriptionPlan.objects.all().order_by("token_limit")
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # amount = request.data.get("amount")  # in rupees
        plan_id = request.data.get("plan_id")  # from frontend
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        razorpay_order = client.order.create(
            {
                "amount": int(plan.price_inr * 100),  # in paise
                "currency": "INR",
                "payment_capture": 1,
            }
        )
        logger.info("Razor pay oder: %s", razorpay_order)
        fetch_razorpay_order = client.order.fetch(razorpay_order["id"])
        logger.info("Fetched razor pay order: %s", fetch_razorpay_order)

        order = Order.objects.create(
            user=request.user,
            amount=plan.price_inr,
            currency="INR",
            plan=plan,
            razorpay_order_id=razorpay_order["id"],
        )
        logger.info("Order created in DB: %s", order)
        return Response(
            {
                "order_id": razorpay_order["id"],
                "amount": razorpay_order["amount"],
                "currency": razorpay_order["currency"],
                "key": settings.RAZORPAY_KEY_ID,
                "plan": plan.name,
            }
        )


class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        logger.info("Verifying payment with data: %s", data)
        try:
            client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": data["razorpay_order_id"],
                    "razorpay_payment_id": data["razorpay_payment_id"],
                    "razorpay_signature": data["razorpay_signature"],
                }
            )
            logger.info("Payment signature verified successfully")
        except razorpay.errors.SignatureVerificationError:
            logger.error("Signature verification failed")
            return Response(
                {"status": "failure", "message": "Invalid signature"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order = Order.objects.get(razorpay_order_id=data["razorpay_order_id"])
            if not order.is_paid:  # avoid double activation
                order.is_paid = True
                order.razorpay_payment_id = data["razorpay_payment_id"]
                order.save()

                # ✅ Activate tokens on webhook too
                activate_subscription(order)

        except Order.DoesNotExist:
            pass
        logger.info("Order updated successfully: %s", order)
        return Response({"status": "success"})


class RazorpayWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        received_sig = request.headers.get("X-Razorpay-Signature")
        body = request.body.decode("utf-8")
        logger.info("received the signature %s", received_sig)
        logger.info("request body: %s", body)
        # Verify signature
        generated_sig = hmac.new(
            webhook_secret.encode(), body.encode(), hashlib.sha256
        ).hexdigest()

        logger.info("generate signature: %s", generated_sig)
        if not hmac.compare_digest(received_sig, generated_sig):
            logger.error("Invalid signature")
            return HttpResponse(status=400)  # Invalid signature

        event = json.loads(body)
        event_type = event.get("event")
        logger.info("event captured: %s", event_type)

        if event_type == "payment.captured":
            payment = event["payload"]["payment"]["entity"]
            logger.info("payment obj: %s", payment)
            razorpay_order_id = payment.get("order_id")
            razorpay_payment_id = payment.get("id")

            try:
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                if not order.is_paid:  # avoid double activation
                    order.is_paid = True
                    order.razorpay_payment_id = razorpay_payment_id
                    order.save()

                    # ✅ Activate tokens on webhook too
                    activate_subscription(order)

            except Order.DoesNotExist:
                pass

        logger.info("successful")
        return HttpResponse(status=200)
