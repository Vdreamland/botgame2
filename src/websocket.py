import websockets
import json

class GameWebSocket:
    def __init__(self, url, headers):
        self.url = url
        self.headers = headers
        self._ws = None

    async def __aenter__(self):
        self._ws = await websockets.connect(self.url, additional_headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._ws:
            await self._ws.close()

    async def send(self, data):
        await self._ws.send(json.dumps(data))

    async def recv(self):
        raw = await self._ws.recv()
        return json.loads(raw)