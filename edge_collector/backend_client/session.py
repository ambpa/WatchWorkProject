import httpx
from datetime import datetime
import asyncio


class BackendSessionClient:
    def __init__(self, base_url: str, device_id: str):
        self.base_url = base_url.rstrip("/")
        self.device_id = device_id
        self.session_id = None

        #import per buffer send_data
        self.buffer = {}
        self.buffer_lock = asyncio.Lock()
        self.flush_interval = 1  # secondi
        self.max_batch_size = 100
        self.flush_task = None

        limits = httpx.Limits(
            max_connections=5,
            max_keepalive_connections=5,
        )
        self.client = httpx.AsyncClient(timeout=5, limits=limits)

    async def start(self):
        r = await self.client.post(
            f"{self.base_url}/api/sessions/start/",
            json={"device_id": self.device_id},
        )
        r.raise_for_status()
        self.session_id = r.json()["session_id"]
        self.flush_task = asyncio.create_task(self._flush_loop())
        print(f"[BACKEND] session started {self.session_id}")

    async def heartbeat(self):
        if not self.session_id:
            return

        await self.client.post(
            f"{self.base_url}/api/sessions/heartbeat/",
            json={"session_id": self.session_id},
        )

    async def stop(self):
        if not self.session_id:
            return

        await self._flush()

        if self.flush_task:
            self.flush_task.cancel()

        await self.client.post(
            f"{self.base_url}/api/sessions/stop/",
            json={"session_id": self.session_id},
        )
        print("[BACKEND] session stopped")

    async def close(self):
        await self.client.aclose()

    async def send_data(self, data: dict):
        if not self.session_id:
            return
        if data is None:
            #print("⚠️ Data is None, skipping send")
            return

        #print(data)
        payload = {
            "session_id": self.session_id,
            "data_type": data.get("type"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": data,
        }
        await self.client.post(
            f"{self.base_url}/api/data/",
            json=payload
        )
        print(f"[BACKEND] data sent: {payload}")

    async def add_to_buffer(self, data: dict):

        if not self.session_id or data is None:
            return

        data_type = data.get("type")

        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": data,
        }

        should_flush = False

        async with self.buffer_lock:

            if data_type not in self.buffer:
                self.buffer[data_type] = []

            self.buffer[data_type].append(payload)

            if len(self.buffer[data_type]) >= self.max_batch_size:
                should_flush = True
        if should_flush:
            await self._flush_type(data_type)


    async def _flush_type(self, data_type):

        async with self.buffer_lock:

            if data_type not in self.buffer or not self.buffer[data_type]:
                return

            batch = self.buffer[data_type]
            self.buffer[data_type] = []

        try:

            payload = {
                "session_id": self.session_id,
                "data_type": data_type,
                "samples": batch
            }

            await self.client.post(
                f"{self.base_url}/api/data/",
                json=payload
            )

            print(f"[BACKEND] batch {data_type}: {len(batch)} samples")

        except Exception as e:

            print(f"[BACKEND] batch failed ({data_type}):", e)

            async with self.buffer_lock:
                self.buffer[data_type] = batch + self.buffer.get(data_type, [])

    async def _flush_loop(self):

        while True:
            await asyncio.sleep(self.flush_interval)

            async with self.buffer_lock:
                data_types = list(self.buffer.keys())

            for data_type in data_types:
                await self._flush_type(data_type)


    async def _flush(self):

        async with self.buffer_lock:
            data_types = list(self.buffer.keys())

        for data_type in data_types:
            await self._flush_type(data_type)