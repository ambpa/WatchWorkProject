# measurement/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from devices.models import DeviceSession
from .models import Measurement
from .serializers import MeasurementInSerializer


@api_view(["POST"])
def receive_data(request):
    serializer = MeasurementInSerializer(data=request.data)
    #print("Received data: ", serializer.data)
    if not serializer.is_valid():
        print("VALIDATION ERROR:", serializer.errors)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    session_id = serializer.validated_data["session_id"]

    try:
        session = DeviceSession.objects.get(id=session_id, is_active=True)
    except DeviceSession.DoesNotExist:
        return Response(
            {"error": "Invalid or inactive session"},
            status=status.HTTP_400_BAD_REQUEST
        )

    measurement = Measurement.objects.create(
        device=session.device,
        data_type=serializer.validated_data["data_type"],
        timestamp=serializer.validated_data["timestamp"],
        payload=serializer.validated_data["payload"]
    )

    return Response({"status": "ok", "id": measurement.id})
