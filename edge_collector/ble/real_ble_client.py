import asyncio
from bleak import BleakScanner, BleakClient
from .events import Event

DEVICE_NAME = "WatchWorks"
CHAR_UUID_NOTIFY = "00000201-8e22-4541-9d4c-21edae82ed19"
CHAR_UUID_TX = "00000202-8e22-4541-9d4c-21edae82ed19"  # cambia con la tua reale

class RealBLEClient:
    def __init__(self, event_queue, data_pipeline):
        self.event_queue = event_queue
        self.data_pipeline = data_pipeline
        self.client: BleakClient | None = None
        self.device = None
        self.running = False

    async def scan(self):
        # Retry loop per trovare il device
        for attempt in range(3):
            devices = await BleakScanner.discover(timeout=5)
            device = next((d for d in devices if d.name == DEVICE_NAME), None)
            if device:
                self.device = device
                print(f"[BLE] device found: {device.address}")
                await self.event_queue.put(Event.DEVICE_FOUND)
                return
            print(f"[BLE] scan attempt {attempt+1} - device not found")
        # Timeout
        await self.event_queue.put(Event.TIMEOUT)

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
        # Bleak gestisce automaticamente le services discovery
        await self.event_queue.put(Event.SERVICES_OK)

    async def subscribe(self):
        if not self.client or not self.client.is_connected:
            print("[BLE] cannot subscribe, client not connected")
            return

        await self.client.start_notify(
            CHAR_UUID_NOTIFY,
            self._notification_handler
        )
        self.running = True
        await self.event_queue.put(Event.SUBSCRIBE_OK)

        # Dopo subscription, possiamo far partire command loop
        print("[BLE] subscribed and ready for commands")

    def _notification_handler(self, sender, data: bytearray):
        # Callback BLE -> pipeline
        asyncio.create_task(
            self.data_pipeline.handle_payload(bytes(data))
        )

    async def send_command(self, command: bytes):
        if not self.client or not self.client.is_connected:
            print("[BLE] cannot send, client not connected")
            return

        await self.client.write_gatt_char(CHAR_UUID_TX, command)
        print(f"[BLE] command sent to device: {command}")

    async def cleanup(self):
        self.running = False
        if self.client:
            await self.client.disconnect()
            print("[BLE] disconnected")
