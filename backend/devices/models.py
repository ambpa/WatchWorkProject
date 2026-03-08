from django.db import models


class Device(models.Model):
    device_id = models.CharField(
        max_length=64,
        unique=True,
        help_text="ID univoco del dispositivo (BLE MAC o UUID)",
    )
    name = models.CharField(
        max_length=128,
        blank=True,
        help_text="Nome leggibile assegnato dall'utente",
    )
    model = models.CharField(
        max_length=64,
        blank=True,
        help_text="Modello hardware",
    )
    firmware_version = models.CharField(
        max_length=32,
        blank=True,
    )

    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or self.device_id


class DeviceSession(models.Model):
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="sessions"
    )

    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    last_heartbeat = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.device} @ {self.started_at}"
