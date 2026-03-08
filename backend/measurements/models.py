from django.db import models
from devices.models import Device


class Measurement(models.Model):
    class DataType(models.TextChoices):
        RAW_MOTION = "raw_motion"
        RAW_BIOMETRIC = "raw_biometric"
        RAW_AIR = "raw_air"
        RAW_GNSS = "raw_gnss"

        PROCESSED_MOTION = "processed_motion"
        PROCESSED_BIOMETRIC = "processed_biometric"
        PROCESSED_AIR = "processed_air"

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="measurements",
    )

    data_type = models.CharField(
        max_length=32,
        choices=DataType.choices,
    )

    timestamp = models.DateTimeField(
        help_text="Epoch o timestamp del dato"
    )

    payload = models.JSONField(
        help_text="Dati decodificati dalla caratteristica BLE"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["device", "data_type", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.device} - {self.data_type} @ {self.timestamp}"
