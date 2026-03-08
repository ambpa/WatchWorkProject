from django.contrib import admin
from .models import Device, DeviceSession


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("device_id", "name", "model", "is_active", "last_seen")
    search_fields = ("device_id", "name", "model")


@admin.register(DeviceSession)
class DeviceSessionAdmin(admin.ModelAdmin):
    list_display = ("device", "started_at", "ended_at", "is_active")
    list_filter = ("is_active", "device")