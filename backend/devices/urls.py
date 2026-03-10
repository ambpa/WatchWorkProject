from rest_framework.routers import DefaultRouter
from .views import DeviceViewSet, StartSessionView, HeartbeatView, StopSessionView
from django.urls import path
from .views_dashboard import device_list_view, device_detail_view, device_measurements_chart
from . import views_ble

router = DefaultRouter()
router.register(r"devices", DeviceViewSet, basename="device")

urlpatterns = router.urls

urlpatterns += [
    path("sessions/start/", StartSessionView.as_view()),
    path("sessions/heartbeat/", HeartbeatView.as_view()),
    path("sessions/stop/", StopSessionView.as_view()),
]

urlpatterns += [
    path("dashboard/devices2/", device_list_view, name="device_list"),
    path("dashboard/devices/<int:device_id>/", device_detail_view, name="device_detail"),

]

urlpatterns += [
    path(
        "dashboard/devices/<int:device_id>/chart/",device_measurements_chart, name="device_chart",),
        path("dashboard/devices/", views_ble.devices_dashboard, name="devices_dashboard"),
        path("dashboard/devices_connected/", views_ble.devices, name="devices_api"),


]


urlpatterns += [
    path('ble/scan/', views_ble.scan_devices, name='ble_scan'),
    path('ble/connect/', views_ble.connect_device, name='ble_connect'),
    path('ble/devices/', views_ble.ble_device_list_view, name="ble_device_list"),
    path("ble/toggle_characteristic/", views_ble.toggle_characteristic, name="toggle_characteristic"),

    # path('ble/select/', views_ble.select_ble_device, name="select_ble_device"),
]