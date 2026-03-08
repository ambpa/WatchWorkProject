# measurement/serializers.py

from rest_framework import serializers

class MeasurementInSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    data_type = serializers.CharField()
    timestamp = serializers.DateTimeField()
    payload = serializers.JSONField()
