import asyncio
import random
from .events import Event


class FakeBLEClient:
    """
    Simula un device BLE reale.
    NON decide stati.
    Produce solo eventi.
    """

    def __init__(self, event_queue, data_pipeline):
        self.event_queue = event_queue
        self.data_pipeline = data_pipeline
        self.running = False
        self.data_pipeline = data_pipeline

    async def scan(self):
        await asyncio.sleep(1)
        print("[BLE] device found")
        await self.event_queue.put(Event.DEVICE_FOUND)

    async def connect(self):
        await asyncio.sleep(1)

        if random.random() < 0.8:
            print("[BLE] connect ok")
            await self.event_queue.put(Event.CONNECT_OK)
        else:
            print("[BLE] connect fail")
            await self.event_queue.put(Event.CONNECT_FAIL)

    async def discover_services(self):
        await asyncio.sleep(0.5)
        print("[BLE] services discovered")
        await self.event_queue.put(Event.SERVICES_OK)

    async def subscribe(self):
        await asyncio.sleep(0.5)
        print("[BLE] subscribed to notify")
        self.running = True
        await self.event_queue.put(Event.SUBSCRIBE_OK)
        asyncio.create_task(self._notify_loop())

    async def simulate_disconnect(self):
        await asyncio.sleep(3)
        print("[BLE] device disconnected")
        await self.event_queue.put(Event.DISCONNECTED)

    async def cleanup(self):
        print("[BLE] cleanup")
        self.running = False

    async def _notify_loop(self):
        while self.running:
            await asyncio.sleep(1)
            payload = b"\x01\x02\x03\x04\x05\x06"  # finto dato binario
            print("[BLE] notify payload")
            await self.data_pipeline.handle_payload(payload)

    async def send_command(self, command: str):
        print(f"[BLE] command sent to device: {command}")
        await asyncio.sleep(0.2)

    async def simulate_notify(self):
        await asyncio.sleep(1)  # piccolo delay
        payload = b'\x01\x02\x03\x04\x05\x06'  # esempio 6 byte ProcessedMotion
        print(f"[BLE] notify payload")
        await self.data_pipeline.handle_payload(payload)