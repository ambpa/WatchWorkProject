import asyncio
from edge_collector.ble.real_ble_client import RealBLEClient
from edge_collector.ble.state_machine import BLEStateMachine
from edge_collector.data.pipeline import DataPipeline
from edge_collector.storage.local_store import LocalStore
from edge_collector.ble.events import Event as EventQueue

# Store e pipeline condivisi
store = LocalStore()
data_pipeline = DataPipeline(store)
event_queue = asyncio.Queue()

# Client BLE globale
ble_client = RealBLEClient(event_queue, data_pipeline)

# Command queue globale
command_queue = asyncio.Queue()

# Istanziamo la state machine
state_machine = BLEStateMachine(ble_client, command_queue, device_id="demo_device")