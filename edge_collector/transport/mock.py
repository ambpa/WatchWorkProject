import asyncio
from transport.base import BaseTransport
from ble.events import Event


class MockTransport:

    def __init__(self, state_machine):
        self.sm = state_machine

    async def scan(self):
        print("[Transport] mock scanning")
        await asyncio.sleep(1)
        await self.sm.event_queue.put(Event.DEVICE_FOUND)

    async def connect(self):
        print("[Transport] mock connect")
        await asyncio.sleep(1)
        await self.sm.event_queue.put(Event.CONNECT_OK)

    async def discover_services(self):
        print("[Transport] mock services discovered")
        await asyncio.sleep(1)
        await self.sm.event_queue.put(Event.SERVICES_OK)

    async def subscribe(self):
        print("[Transport] mock subscribed")
        await asyncio.sleep(1)
        await self.sm.event_queue.put(Event.SUBSCRIBE_OK)

    async def disconnect(self):
        print("[Transport] mock disconnected")
        await self.sm.event_queue.put(Event.DISCONNECTED)


