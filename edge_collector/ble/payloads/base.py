# ble/payloads/base.py
from abc import ABC, abstractmethod


class BLEPayloadDecoder(ABC):
    payload_type: str

    @abstractmethod
    def decode(self, payload: bytes) -> dict:
        pass
