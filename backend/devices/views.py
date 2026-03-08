from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now
from .models import Device, DeviceSession
from .serializers import DeviceSerializer


class DeviceViewSet(ModelViewSet):
    queryset = Device.objects.all().order_by("-created_at")
    serializer_class = DeviceSerializer


class StartSessionView(APIView):
    def post(self, request):
        device_id = request.data.get("device_id")

        if not device_id:
            return Response({"error": "device_id required"}, status=400)

        device, _ = Device.objects.get_or_create(device_id=device_id)

        session = DeviceSession.objects.create(device=device)

        device.last_seen = now()
        device.save()

        return Response(
            {"session_id": session.id},
            status=status.HTTP_201_CREATED,
        )


class HeartbeatView(APIView):
    def post(self, request):
        session_id = request.data.get("session_id")

        try:
            session = DeviceSession.objects.get(id=session_id, is_active=True)
        except DeviceSession.DoesNotExist:
            return Response({"error": "invalid session"}, status=404)

        session.last_heartbeat = now()
        session.device.last_seen = now()

        session.save()
        session.device.save()

        return Response({"ok": True})


class StopSessionView(APIView):
    def post(self, request):
        session_id = request.data.get("session_id")

        try:
            session = DeviceSession.objects.get(id=session_id, is_active=True)
        except DeviceSession.DoesNotExist:
            return Response({"error": "invalid session"}, status=404)

        session.is_active = False
        session.ended_at = now()
        session.save()

        return Response({"ok": True})
