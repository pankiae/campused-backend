import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class SubscriptionPlan(models.Model):
    PLAN_CHOICES = [
        ("basic", "Basic"),
        ("pro", "Pro"),
        ("enterprise", "Enterprise"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    token_limit = models.IntegerField()  # e.g., 30000, 100000, 300000
    price_inr = models.FloatField()
    description = models.CharField(max_length=255, blank=True)
    features = models.JSONField(default=list)

    class Meta:
        db_table = "subscription_plans"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    amount = models.FloatField()
    currency = models.CharField(max_length=10, default="INR")
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "subscriptions_orders"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user"])]
