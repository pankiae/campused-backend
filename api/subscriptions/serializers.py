from rest_framework import serializers

from .models import SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for listing all subscription plans."""

    class Meta:
        model = SubscriptionPlan
        fields = ["id", "name", "token_limit", "price_inr", "description", "features"]
