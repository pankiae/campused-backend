from rest_framework import serializers

from .models import Channel


class ChannelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['id', 'title']