from django.contrib import admin
from .models import Measurement


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ("device", "data_type", "timestamp")
    list_filter = ("data_type", "device")
    ordering = ("-timestamp",)
