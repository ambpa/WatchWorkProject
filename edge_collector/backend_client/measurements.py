import httpx
import asyncio


class BackendMeasurementClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=5)

    async def send_measurement(self, payload: dict):
        url = f"{self.base_url}/api/measurements/"
        try:
            r = await self.client.post(url, json=payload)
            r.raise_for_status()
            print("[BACKEND] measurement sent")
            return True
        except Exception as e:
            print(f"[BACKEND] error: {e}")
            return False

    async def close(self):
        await self.client.aclose()

# async def main():
#     client = BackendMeasurementClient("http://127.0.0.1:8000")
#
#     payload = {
#         "device": 1,  # PK del device nel DB
#         "data_type": "raw_motion",
#         "timestamp": "2026-01-01T12:00:00Z",
#         "payload": {
#             "epoch": 1710000002,
#             "index": 1,
#             "accel": [0.0, 0.1, 9.8],
#             "gyro": [0.01, 0.02, 0.03],
#             "temperature": 36.5,
#         },
#     }
#
#     ok = await client.send_measurement(payload)
#     print("RESULT:", ok)
#
#     await client.close()
#
#
# if __name__ == "__main__":
#     asyncio.run(main())