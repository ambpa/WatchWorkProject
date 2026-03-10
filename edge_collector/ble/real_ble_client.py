import asyncio
from bleak import BleakClient
from .events import Event

CHAR_NOTIFY_UUIDS = [
    "00000201-8e22-4541-9d4c-21edae82ed19",  # RawMotion
    "00000202-8e22-4541-9d4c-21edae82ed19",  # RawBiometric
]

#Scrivre
RAW_ENABLE_REALTIME_UUID = "00000205-8e22-4541-9d4c-21edae82ed19"

class RealBLEClient:

    def __init__(self, event_queue=None, data_pipeline=None):

        self.event_queue = event_queue
        self.data_pipeline = data_pipeline

        self.client: BleakClient | None = None
        self.device = None
        self.running = False

    async def connect(self):

        if not self.device:
            print("[BLE] cannot connect, no device")
            await self.event_queue.put(Event.CONNECT_FAIL)
            return

        try:

            self.client = BleakClient(self.device.address)

            await self.client.connect()

            print("[BLE] connect ok")

            await self.event_queue.put(Event.CONNECT_OK)

        except Exception as e:

            print("[BLE] connect fail:", e)

            await self.event_queue.put(Event.CONNECT_FAIL)

    async def discover_services(self):

        if not self.client:
            return

        # attende che bleak carichi le services
        for _ in range(10):

            if self.client.services:
                break

            await asyncio.sleep(0.2)

        services = self.client.services

        if services:
            print("[BLE] services discovered:")#, len(services))
        else:
            print("[BLE] warning: services still empty")

        await self.event_queue.put(Event.SERVICES_OK)

    async def subscribe(self):

        for uuid in CHAR_NOTIFY_UUIDS:

            try:

                await self.client.start_notify(
                    uuid,
                    self._notification_handler
                )

                print(f"[BLE] notifications enabled for {uuid}")

            except Exception as e:

                print(f"[BLE] cannot subscribe {uuid}: {e}")

        await self.event_queue.put(Event.SUBSCRIBE_OK)

    def _notification_handler(self, sender, data):

        print(f"[BLE] notification from {sender}: {data}")

        if self.data_pipeline:

            asyncio.create_task(
                self.data_pipeline.handle_payload(bytes(data))
            )

    async def write_raw_enable_realtime(self, value: bytearray):

        if not self.client or not self.client.is_connected:
            print("[BLE] write failed: device not connected")
            return

        try:

            print("[BLE] writing Raw_Enable_RealTime:", list(value))

            await self.client.write_gatt_char(
                RAW_ENABLE_REALTIME_UUID,
                value,
                response=False
            )

            print("[BLE] write success")

        except Exception as e:

            print("[BLE] write failed:", e)

    async def cleanup(self):

        if self.client:
            await self.client.disconnect()

            print("[BLE] disconnected")