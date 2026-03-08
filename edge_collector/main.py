# main.py
import asyncio
from edge_collector.ble.real_ble_client import RealBLEClient
from edge_collector.ble.state_machine import BLEStateMachine
from edge_collector.data.pipeline import DataPipeline
from edge_collector.storage.local_store import LocalStore
from backend_client.session import BackendSessionClient


async def main():
    # --- STORAGE LOCALE ---
    store = LocalStore()

    # --- BACKEND CLIENT ---
    backend_client = BackendSessionClient(
        base_url="http://localhost:8000",
        device_id="DEVICE_001"
    )

    await backend_client.start()   # 🔥 importantissimo

    # --- PIPELINE DATI ---
    data_pipeline = DataPipeline(
        store=store,
        backend_client=backend_client
    )

    # --- CODE COMANDI ---
    command_queue = asyncio.Queue()

    # --- STATE MACHINE ---
    state_machine_event_queue = asyncio.Queue()

    # --- BLE REALE ---
    ble_client = RealBLEClient(
        event_queue=state_machine_event_queue,
        data_pipeline=data_pipeline
    )

    # --- STATE MACHINE ---
    state_machine = BLEStateMachine(
        ble_client=ble_client,
        command_queue=command_queue,
        device_id="DEVICE_001"
    )

    ble_client.event_queue = state_machine.event_queue

    await state_machine.start()

    # cleanup (mai raggiunto finché gira)
    await backend_client.stop()
    await backend_client.close()


if __name__ == "__main__":
    asyncio.run(main())
