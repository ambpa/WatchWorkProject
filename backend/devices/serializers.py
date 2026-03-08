from rest_framework import serializers
from .models import Device, DeviceSession


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = "__all__"


class DeviceSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceSession
        fields = "__all__"
        read_only_fields = ("started_at", "ended_at", "last_heartbeat", "is_active")