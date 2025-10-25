import hashlib
import hmac
import json
import logging

import razorpay
from django.conf import settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order

logger = logging.getLogger(__name__)


class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")  # in rupees
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        logger.info("razor pay client initiated: %s", client)

        razorpay_order = client.order.create(
            {
                "amount": int(amount * 100),  # Razorpay expects paise
                "currency": "INR",
                "payment_capture": 1,
            }
        )
        logger.info("Razor pay oder: %s", razorpay_order)
        fetch_razorpay_order = client.order.fetch(razorpay_order["id"])
        logger.info("Fetched razor pay order: %s", fetch_razorpay_order)

        # order = Order.objects.create(
        #     user=request.user,
        #     amount=amount,
        #     currency="INR",
        #     razorpay_order_id=razorpay_order["id"],
        # )
        # logger.info("Order created in DB: %s", order)
        return Response(
            {
                "order_id": razorpay_order["id"],
                "amount": razorpay_order["amount"],
                "currency": razorpay_order["currency"],
                "key": settings.RAZORPAY_KEY_ID,
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

        order = Order.objects.get(razorpay_order_id=data["razorpay_order_id"])
        logger.info("Fetched order from DB: %s", order)
        logger.info("Updating order status for order: %s", order)
        order.is_paid = True
        order.razorpay_payment_id = data["razorpay_payment_id"]
        order.razorpay_signature = data["razorpay_signature"]
        order.save()
        logger.info("Order updated successfully: %s", order)
        return Response({"status": "success"})


class RazorpayWebhookView(APIView):
    authentication_classes = []  # Razorpay won't send JWT
    permission_classes = []  # Keep public but verify signature!

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

        # Example: payment.captured
        if event_type == "payment.captured":
            payment = event["payload"]["payment"]["entity"]
            logger.info("payment obj: %s", payment)
            razorpay_order_id = payment.get("order_id")
            razorpay_payment_id = payment.get("id")

            try:
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                order.is_paid = True
                order.razorpay_payment_id = razorpay_payment_id
                order.save()
            except Order.DoesNotExist:
                pass

        logger.info("successful")
        return HttpResponse(status=200)
