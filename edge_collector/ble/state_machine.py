import asyncio
from enum import Enum, auto
from .events import Event
from backend_client.session import BackendSessionClient

class State(Enum):
    IDLE = auto()
    SCANNING = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    SUBSCRIBED = auto()
    ACTIVE = auto()
    ERROR = auto()

class BLEStateMachine:
    def __init__(self, ble_client, command_queue, device_id: str):
        self.state = State.IDLE
        self.event_queue = asyncio.Queue()
        self.retry = 0
        self.ble = ble_client
        self.command_queue = command_queue

        self.backend_session = BackendSessionClient(
            base_url="http://127.0.0.1:8000",
            device_id=device_id,
        )

    async def start(self):
        print("State machine started")
        await self._transition(State.SCANNING)

        while True:
            event = await self.event_queue.get()
            await self._handle_event(event)

    async def _handle_event(self, event: Event):
        print(f"[EVENT] {event.name} in state {self.state.name}")

        if self.state == State.SCANNING and event == Event.DEVICE_FOUND:
            await self._transition(State.CONNECTING)

        elif self.state == State.CONNECTING:
            if event == Event.CONNECT_OK:
                await self._transition(State.CONNECTED)
            elif event in (Event.CONNECT_FAIL, Event.TIMEOUT):
                await self._transition(State.ERROR)

        elif self.state == State.CONNECTED:
            if event == Event.SERVICES_OK:
                await self._transition(State.SUBSCRIBED)
            elif event == Event.DISCONNECTED:
                await self._transition(State.ERROR)

        elif self.state == State.SUBSCRIBED:
            if event == Event.SUBSCRIBE_OK:
                await self._transition(State.ACTIVE)
            elif event == Event.DISCONNECTED:
                await self._transition(State.ERROR)

        elif self.state == State.ACTIVE and event == Event.DISCONNECTED:
            await self._transition(State.ERROR)

        elif self.state == State.ERROR:
            await asyncio.sleep(min(2 ** self.retry, 10))
            self.retry += 1
            await self._transition(State.SCANNING)

    async def _transition(self, new_state: State):
        old_state = self.state
        self.state = new_state
        print(f"[STATE] {old_state.name} → {new_state.name}")

        if new_state == State.SCANNING:
            asyncio.create_task(self.ble.scan())

        elif new_state == State.CONNECTING:
            asyncio.create_task(self.ble.connect())

        elif new_state == State.CONNECTED:
            asyncio.create_task(self.ble.discover_services())

        elif new_state == State.SUBSCRIBED:
            asyncio.create_task(self.ble.subscribe())

        elif new_state == State.ACTIVE:
            self.retry = 0
            # Start backend session
            await self.backend_session.start()
            asyncio.create_task(self._heartbeat_loop())

            # Flush offline data
            asyncio.create_task(self.on_active())

        elif new_state == State.ERROR:
            await self.backend_session.stop()
            await self.ble.cleanup()

    async def _command_loop(self):
        print("[COMMAND_LOOP] started")
        while self.state == State.ACTIVE:
            command = await self.command_queue.get()
            if getattr(self.ble, "client", None) and self.ble.client.is_connected:
                await self.ble.send_command(command)
            else:
                print("[COMMAND_LOOP] Cannot send command, BLE client not connected")

    async def on_active(self):
        if hasattr(self.ble, "data_pipeline"):
            await self.ble.data_pipeline.flush()

    async def _heartbeat_loop(self):
        while self.state == State.ACTIVE:
            await asyncio.sleep(10)
            await self.backend_session.heartbeat()
