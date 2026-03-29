import asyncio
from enum import Enum, auto
from .events import Event
from ..backend_client.session import BackendSessionClient


class State(Enum):
    IDLE = auto()
    WAIT_DEVICE = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    SUBSCRIBED = auto()
    ACTIVE = auto()
    ERROR = auto()


class BLEStateMachine:

    def __init__(self, ble_client, command_queue, device_id: str, state_callback=None):

        self.state = State.IDLE
        self.state_callback = state_callback

        # UNICA EVENT QUEUE
        self.event_queue = asyncio.Queue()

        self.retry = 0

        self.ble = ble_client
        self.command_queue = command_queue

        # 🔴 CRITICO
        # passiamo la queue al ble client
        self.ble.event_queue = self.event_queue
        self.device_address = None

        self.backend_session = BackendSessionClient(
            base_url="http://127.0.0.1:8000",
            device_id=device_id
        )

    async def set_device(self, address):
        print("[BLE] device selected:", address)
        # salva address reale
        self.device_address = address
        print("address ", address)
        self.ble.device = type("DeviceStub", (), {"address": address})()
        await self.event_queue.put(Event.DEVICE_SELECTED)

    async def start(self):

        print("State machine started")

        await self._transition(State.WAIT_DEVICE)

        while True:

            event = await self.event_queue.get()

            await self._handle_event(event)


    async def _handle_event(self, event):

        print(f"[EVENT] {event.name} in state {self.state.name}")

        if self.state == State.WAIT_DEVICE:

            if event == Event.DEVICE_SELECTED:

                await self._transition(State.CONNECTING)

        elif self.state == State.CONNECTING:

            if event == Event.CONNECT_OK:

                await self._transition(State.CONNECTED)

            elif event == Event.CONNECT_FAIL:

                await self._transition(State.ERROR)

        elif self.state == State.CONNECTED:

            if event == Event.SERVICES_OK:

                await self._transition(State.SUBSCRIBED)

        elif self.state == State.SUBSCRIBED:

            if event == Event.SUBSCRIBE_OK:

                await self._transition(State.ACTIVE)

        elif self.state == State.ACTIVE:

            if event == Event.DISCONNECTED:

                await self._transition(State.ERROR)

        elif self.state == State.ERROR:

            await asyncio.sleep(min(2 ** self.retry, 10))

            self.retry += 1

            await self._transition(State.CONNECTING)

    async def _transition(self, new_state):

        old_state = self.state
        self.state = new_state

        print(f"[STATE] {old_state.name} → {new_state.name}")

        # 🔴 aggiorna dashboard
        if self.state_callback:
            await self.state_callback(self.state)


        if new_state == State.CONNECTING:

            asyncio.create_task(self.ble.connect())

        elif new_state == State.CONNECTED:

            asyncio.create_task(self.ble.discover_services())

        elif new_state == State.SUBSCRIBED:

            asyncio.create_task(self.ble.subscribe())

        elif new_state == State.ACTIVE:

            self.retry = 0

            print("[BLE] device active, receiving data")

            await self.backend_session.start()

            # 🔴 collega pipeline al backend

            if hasattr(self.ble, "data_pipeline"):
                self.ble.data_pipeline.backend_client = self.backend_session

            asyncio.create_task(self._heartbeat_loop())

            asyncio.create_task(self.on_active())

            asyncio.create_task(self._ble_keepalive())

        elif new_state == State.ERROR:

            await self.backend_session.stop()

            await self.ble.cleanup()

    async def on_active(self):

        if hasattr(self.ble, "data_pipeline"):

            await self.ble.data_pipeline.flush()

    async def _heartbeat_loop(self):

        while self.state == State.ACTIVE:

            await asyncio.sleep(10)

            await self.backend_session.heartbeat()

    async def _ble_keepalive(self):

        while self.state == State.ACTIVE:

            await asyncio.sleep(1)

    async def write_characteristic(self, char, enabled):

        if self.state != State.ACTIVE:
            print("Device not active")
            return

        byte_map = {
            "motion": 0,
            "biometric": 1,
            "air": 2,
            "gnss": 3
        }

        index = byte_map[char]

        value = bytearray(4)

        if enabled:
            value[index] = 1
        else:
            value[index] = 0

        print("Writing characteristic:", list(value))

        await self.ble.write_raw_enable_realtime(value)

    async def write_raw_enable_realtime(self, value):

        if not self.ble:
            print("[SM] no BLE client")
            return

        await self.ble.write_raw_enable_realtime(value)