from django.db.models import OuterRef, Subquery
from django.shortcuts import render
from .models import Device, DeviceSession
from django.shortcuts import get_object_or_404
from measurements.models import Measurement
import asyncio
from edge_collector.ble.real_ble_client import RealBLEClient  # o dove si trova realmente

from django.http import JsonResponse
from django.utils.dateparse import parse_datetime

def device_list_view(request):

    last_session = DeviceSession.objects.filter(
        device=OuterRef("pk")
    ).order_by("-started_at")

    devices = Device.objects.annotate(
        last_started_at=Subquery(last_session.values("started_at")[:1]),
        last_ended_at=Subquery(last_session.values("ended_at")[:1]),
        last_session_active=Subquery(last_session.values("is_active")[:1]),
    ).order_by("-created_at")

    return render(request, "dashboard/device_list.html", {
        "devices": devices
    })

def device_detail_view(request, device_id):
    device = get_object_or_404(Device, id=device_id)

    # Recupera BLE device dalla sessione
    ble_name = request.session.get("ble_device_name")
    ble_address = request.session.get("ble_device_address")

    sessions = device.sessions.order_by("-started_at")
    data_types = Measurement.objects.filter(device=device).values_list("data_type", flat=True).distinct()

    # Se il device BLE è presente, connettiamo il client (edge_collector)
    if ble_address:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        RealBLEClient.device = type("BLEDevice", (), {"name": ble_name, "address": ble_address})()
        loop.run_until_complete(RealBLEClient.connect())
        loop.run_until_complete(RealBLEClient.subscribe())

    return render(request, "dashboard/device_detail.html", {
        "device": device,
        "sessions": sessions,
        "data_types": data_types,
    })

# def device_detail_view2(request, device_id):
#     device = get_object_or_404(Device, id=device_id)
#
#     sessions = device.sessions.order_by("-started_at")
#
#     data_types = (
#         Measurement.objects
#         .filter(device=device)
#         .values_list("data_type", flat=True)
#         .distinct()
#     )
#
#     return render(request, "dashboard/device_detail.html", {
#         "device": device,
#         "sessions": sessions,
#         "data_types": data_types,
#     })


def device_measurements_chart(request, device_id):
    device = get_object_or_404(Device, id=device_id)
    data_type = request.GET.get("data_type")
    since = request.GET.get("since")

    if not data_type:
        return JsonResponse({"labels": [], "datasets": []})

    measurements = Measurement.objects.filter(
        device=device,
        data_type=data_type
    )

    if since:
        measurements = measurements.filter(timestamp__gt=parse_datetime(since))

    measurements = measurements.order_by("timestamp")

    labels = [m.timestamp.isoformat() for m in measurements]

    datasets = []

    ACC_SCALE = 8192

    if data_type in ("raw_motion", "processed_motion"):
        for axis in ("ax", "ay", "az"):
            datasets.append({
                "label": axis.upper(),
                "data": [m.payload.get(axis, 0) / ACC_SCALE for m in measurements]
            })

    else:
        datasets.append({
            "label": data_type,
            "data": [m.payload for m in measurements]
        })

    return JsonResponse({
        "labels": labels[-100:],
        "datasets": datasets[-100:]
    })