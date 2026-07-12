import asyncio
import json
import websockets
from typing import Dict, Any, Optional, AsyncGenerator

class ClawRoyaleJoiner:
    WS_URL = "wss://cdn.clawroyale.ai/ws/join"

    def __init__(self, api_key: str, version: str, auth_type: str = "mr-auth"):
        self.api_key = api_key
        self.version = version
        self.auth_type = auth_type

    def _get_headers(self) -> Dict[str, str]:
        headers = {"X-Version": self.version}
        if self.auth_type == "mr-auth":
            headers["Authorization"] = f"mr-auth {self.api_key}"
        elif self.auth_type == "Bearer":
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            headers["X-API-Key"] = self.api_key
        return headers

    async def join_queue(self, entry_type: str = "free") -> AsyncGenerator[Dict[str, Any], Any]:
        headers = self._get_headers()
        async with websockets.connect(self.WS_URL, extra_headers=headers) as ws:
            welcome_raw = await ws.recv()
            welcome = json.loads(welcome_raw)
            yield {"step": "welcome", "data": welcome}

            decision = welcome.get("decision")
            if decision == "BLOCKED":
                print("Join blocked by readiness check.")
                await ws.close(code=4001)
                return
            elif decision == "ALREADY_IN_GAME":
                print("Agent already in-game, promoting socket directly.")
                yield {"step": "promoted", "socket": ws}
                return

            hello_msg = {"type": "hello", "entryType": entry_type}
            await ws.send(json.dumps(hello_msg))

            async for message_raw in ws:
                msg = json.loads(message_raw)
                msg_type = msg.get("type")

                if msg_type == "queued":
                    yield {"step": "queued", "data": msg}
                elif msg_type == "assigned":
                    yield {"step": "assigned", "data": msg, "socket": ws}
                    return
                elif msg_type == "not_selected":
                    yield {"step": "not_selected"}
                    return
                elif msg_type == "error":
                    yield {"step": "error", "data": msg}
                    return