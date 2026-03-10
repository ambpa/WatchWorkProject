import httpx
from datetime import datetime

class BackendSessionClient:
    def __init__(self, base_url: str, device_id: str):
        self.base_url = base_url.rstrip("/")
        self.device_id = device_id
        self.session_id = None
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