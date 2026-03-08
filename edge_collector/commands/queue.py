import asyncio


class CommandQueue:
    """
    Coda comandi asincrona.
    """

    def __init__(self):
        self.queue = asyncio.Queue()

    async def put(self, command: str):
        await self.queue.put(command)

    async def get(self) -> str:
        return await self.queue.get()
