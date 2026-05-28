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

        # PARAMETRI RICONNESSIONE POST CADUTA BLE
        self.manual_disconnect = False
        self.max_retries = 2
        self.retry_delay = 1

        self.reconnect_task = None

        self.device_configs = {}

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

    async def disconnect(self):

        print("[BLE] manual disconnect")

        self.manual_disconnect = True

        # 🔥 STEP 1: spegni stream
        if self.state == State.ACTIVE:
            await self.stop_all_streams()
            await asyncio.sleep(0.2)  # piccolo delay sicurezza

        # 🔥 STEP 2: trigger state machine
        await self.event_queue.put(Event.DISCONNECTED)

    async def _reconnect_loop(self):

        print("[BLE] starting reconnect loop")

        if self.retry >= self.max_retries:
            print("[BLE] max retries reached → IDLE")
            await self._transition(State.IDLE)
            return

        delay = min(self.retry_delay * (2 ** self.retry), 10)

        print(f"[BLE] retry {self.retry + 1}/{self.max_retries} in {delay}s")

        await asyncio.sleep(delay)

        if self.manual_disconnect:
            print("[BLE] reconnect aborted (manual disconnect)")
            return

        print("[BLE] trying reconnect...")

        await self._transition(State.CONNECTING)

    async def stop_all_streams(self):

        print("[BLE] stopping all streams")

        value = bytearray([0, 0, 0, 0])

        try:
            await self.ble.write_raw_enable_realtime(value)
            print("[BLE] all streams disabled")

        except Exception as e:
            print("[BLE] failed to stop streams:", e)

    def get_current_config(self):

        return self.device_configs.get(
            self.device_address,
            {
                "motion": False,
                "biometric": False,
                "air": False,
                "gnss": False
            }
        )

    async def _handle_event(self, event):

        print(f"[EVENT] {event.name} in state {self.state.name}")

        if self.state == State.WAIT_DEVICE:

            if event == Event.DEVICE_SELECTED:

                await self._transition(State.CONNECTING)

        elif self.state == State.CONNECTING:

            if event == Event.CONNECT_OK:

                self.retry = 0  # reset
                await self._transition(State.CONNECTED)

            elif event == Event.CONNECT_FAIL:

                self.retry += 1  # QUI
                await self._transition(State.ERROR)

        elif self.state == State.CONNECTED:
            if event == Event.SERVICES_OK:

                await self._transition(State.SUBSCRIBED)

        elif self.state == State.SUBSCRIBED:

            if event == Event.SUBSCRIBE_OK:

                await self._transition(State.ACTIVE)

        elif self.state == State.ACTIVE:
            #reimposto parametri reconnect post caduta BLE
            if event != Event.DISCONNECTED:
                self.retry = 0
                self.manual_disconnect = False

            if event == Event.DISCONNECTED:

                if self.manual_disconnect:
                    print("[BLE] manual disconnect → IDLE")

                    await self.backend_session.stop()
                    await self.ble.cleanup()

                    await self._transition(State.IDLE)
                else:
                    print("[BLE] unexpected disconnect → ERROR")
                    await self._transition(State.ERROR)

        elif self.state == State.IDLE:

            if event == Event.DEVICE_SELECTED:
                print("[BLE] restarting from IDLE")

                self.manual_disconnect = False
                self.retry = 0

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

            # collega pipeline al backend

            if hasattr(self.ble, "data_pipeline"):
                self.ble.data_pipeline.backend_client = self.backend_session


            config = self.get_current_config()

            value = bytearray([
                1 if config["motion"] else 0,
                1 if config["biometric"] else 0,
                1 if config["air"] else 0,
                1 if config["gnss"] else 0
            ])

            print("[BLE] restoring config:", list(value))

            await self.ble.write_raw_enable_realtime(value)


            asyncio.create_task(self._heartbeat_loop())

            asyncio.create_task(self.on_active())

            asyncio.create_task(self._ble_keepalive())

        elif new_state == State.ERROR:

            await self.backend_session.stop()

            await self.ble.cleanup()

            # 🔥 avvia retry automatico
            if not self.manual_disconnect:
                if self.reconnect_task is None or self.reconnect_task.done():
                    self.reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def on_active(self):

        if hasattr(self.ble, "data_pipeline"):

            await self.ble.data_pipeline.flush()

    async def _heartbeat_loop(self):

        while self.state == State.ACTIVE:
            # if self.state.is_connected:
            print("[BLE] connected")
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