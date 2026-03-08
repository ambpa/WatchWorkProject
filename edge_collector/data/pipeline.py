# data/pipeline.py
from ble.payloads.registry import PAYLOAD_DECODERS


class DataPipeline:
    def __init__(self, store, backend_client=None):
        self.store = store
        self.backend_client = backend_client

    async def handle_payload(self, payload: bytes):
        print(f"[DATA] raw payload received: {payload}")
        if not isinstance(payload, (bytes, bytearray)):
            return
        # STEP A: hardcoded decoder
        #decoder = PAYLOAD_DECODERS["processed_motion"]
        for decoder in PAYLOAD_DECODERS.values():
            decoded = decoder.decode(payload)
            if decoded:
                break
        else:
            print("Unknown payload format")
            return

        try:
            decoded = decoder.decode(payload)
        except Exception as e:
            print(f"[DATA] decode error: {e}")
            return

        print(f"[DATA] decoded payload: {decoded}")

        # Persistenza locale (offline-first)
        self.store.save(decoded)

        # Invio backend (se online)
        if self.backend_client:
            await self.backend_client.send_data(decoded)

    async def flush(self):
        for payload in self.store.load_all():
            decoded = PAYLOAD_DECODERS["processed_motion"].decode(payload)
            if self.backend_client:
                await self.backend_client.send_data(decoded)
