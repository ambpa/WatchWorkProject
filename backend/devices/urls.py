from rest_framework.routers import DefaultRouter
from .views import DeviceViewSet, StartSessionView, HeartbeatView, StopSessionView
from django.urls import path
from .views_dashboard import device_list_view, device_detail_view, device_measurements_chart


router = DefaultRouter()
router.register(r"devices", DeviceViewSet, basename="device")

urlpatterns = router.urls

urlpatterns += [
    path("sessions/start/", StartSessionView.as_view()),
    path("sessions/heartbeat/", HeartbeatView.as_view()),
    path("sessions/stop/", StopSessionView.as_view()),
]

urlpatterns += [
    path("dashboard/devices/", device_list_view, name="device_list"),
    path("dashboard/devices/<int:device_id>/", device_detail_view, name="device_detail"),

]

urlpatterns += [
    path(
        "dashboard/devices/<int:device_id>/chart/",device_measurements_chart, name="device_chart",),
]

