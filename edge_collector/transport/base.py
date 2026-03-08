from abc import ABC, abstractmethod
from typing import Callable

class BaseTransport(ABC):
    """
    Interfaccia astratta per il trasporto dati.
    """

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def write(self, data: bytes):
        pass

    @abstractmethod
    def set_notify_callback(self, callback: Callable[[bytes], None]):
        """
        Imposta la funzione da chiamare quando arrivano dati dal device
        """
        pass
