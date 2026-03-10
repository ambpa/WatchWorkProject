# devices/views_ble.py
import asyncio
from django.http import JsonResponse
from bleak import BleakScanner

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import asyncio
from django.shortcuts import render, redirect

from edge_collector.ble.real_ble_client import RealBLEClient  # o dove si trova realmente
from edge_collector.data.pipeline import DataPipeline
from edge_collector.ble.events import Event as EventQueue
from edge_collector.storage.local_store import LocalStore
import requests

# Variabili globali per demo (puoi sostituire con gestione più robusta)
ble_client: RealBLEClient | None = None
store = LocalStore()
data_pipeline = DataPipeline(store)
event_queue = asyncio.Queue()

EDGE_URL = "http://127.0.0.1:9000"


@csrf_exempt
def connect_device(request):

    body = json.loads(request.body)

    address = body.get("address")

    r = requests.post(f"{EDGE_URL}/connect", json={"address": address})

    return JsonResponse({"status": "ok"})

async def scan_devices(request):
    """
    Scansiona i dispositivi BLE visibili e restituisce JSON con name e address.
    """
    devices = await BleakScanner.discover(timeout=5)
    print(devices)
    result = [
        {"name": d.name or "Unknown", "address": d.address}
        for d in devices
        if d.name  # Filtra solo i device con nome
    ]
    print(result)
    return JsonResponse(result, safe=False)

# --- Views ---

def ble_device_list_view(request):
    """
    Mostra i BLE devices disponibili e permette di selezionarne uno.
    """
    devices = []

    async def scan_devices():
        found = []
        # scan BLE usando BleakScanner
        from bleak import BleakScanner
        ble_devices = await BleakScanner.discover(timeout=5)
        for d in ble_devices:
            found.append({"name": d.name or "Unknown", "address": d.address})
        return found

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    devices = loop.run_until_complete(scan_devices())

    return render(request, "dashboard/ble_device_list.html", {"devices": devices})

def devices_dashboard(request):

    r = requests.get(f"{EDGE_URL}/devices")

    devices = r.json().get("devices", [])

    return render(
        request,
        "dashboard/devices.html",
        {"devices": devices}
    )

import requests
from django.http import JsonResponse


def devices(request):

    r = requests.get(f"{EDGE_URL}/devices")

    return JsonResponse(r.json())

@csrf_exempt
def disconnect_device(request):

    address = request.POST.get("address")

    requests.post(
        f"{EDGE_URL}/disconnect",
        json={"address": address}
    )

    return redirect("/devices")

@csrf_exempt
def toggle_characteristic(request):

    data = json.loads(request.body)

    address = data["address"]
    char = data["characteristic"]
    enabled = data["enabled"]

    r = requests.post(
        f"{EDGE_URL}/characteristic",
        json={
            "address": address,
            "characteristic": char,
            "enabled": enabled
        }
    )

    return JsonResponse(r.json())


@csrf_exempt
def toggle_characteristic2(request):

    address = request.POST.get("address")
    char = request.POST.get("characteristic")
    action = request.POST.get("action")

    enabled = action == "enable"

    requests.post(
        f"{EDGE_URL}/characteristic",
        json={
            "address": address,
            "characteristic": char,
            "enabled": enabled
        }
    )

    return redirect("/api/dashboard/devices/")

# def select_ble_device(request):
#     """
#     Salva nella sessione il BLE device scelto dall'utente
#     """
#     print(request)
#     if request.method == "POST":
#         request.session["ble_device_name"] = request.POST.get("name")
#         request.session["ble_device_address"] = request.POST.get("address")
#         return redirect("device_detail", device_id=request.POST.get("device_id"))
#
#     return JsonResponse({"error": "Metodo non valido"}, status=400)

# def api_ble_scan(request):
#     """Endpoint AJAX per scansionare dispositivi BLE."""
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(ble_client.scan())
#     device = ble_client.device
#     print(device)
#     if device:
#         return JsonResponse({
#             "name": device.name,
#             "address": device.address
#         })
#     return JsonResponse({"name": None, "address": None})