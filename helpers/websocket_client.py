import asyncio
import json
import websockets
from typing import Dict, Any, Callable, Optional, Awaitable

class ClawRoyaleWebSocketClient:
    def __init__(self, api_key: str, version: str, auth_type: str = "mr-auth", message_handler: Optional[Callable[[str, Dict[str, Any], Any], Awaitable[None]]] = None):
        self.api_key = api_key
        self.version = version
        self.auth_type = auth_type
        self.headers = self._build_headers()
        self.agent_id = None
        self.agent_name = None
        self.message_handler = message_handler
        self.ws = None

    def _build_headers(self) -> Dict[str, str]:
        headers = {"X-Version": self.version}
        if self.auth_type == "mr-auth":
            headers["Authorization"] = f"mr-auth {self.api_key}"
        elif self.auth_type == "Bearer":
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            headers["X-API-Key"] = self.api_key
        return headers

    async def run_game_loop(self, ws):
        self.ws = ws
        print("[Socket] Successfully connected to live arena stream.")
        try:
            async for message_raw in ws:
                msg = json.loads(message_raw)
                msg_type = msg.get("type")
                
                if self.message_handler:
                    await self.message_handler(msg_type, msg, self)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.ws = None
            print("[Socket] Arena connection closed.")

    async def connect_and_join(self, entry_type: str = "free"):
        url = "wss://cdn.clawroyale.ai/ws/join"
        print(f"[Connection] Connecting to matchmaker: {url}")
        
        try:
            async with websockets.connect(url, additional_headers=self.headers) as ws:
                self.ws = ws
                welcome_raw = await ws.recv()
                welcome = json.loads(welcome_raw)
                
                print(f"[Matchmaking] Handshake completed successfully. Server Time: {welcome.get('serverTime')}")
                
                decision = welcome.get("decision")
                if decision == "BLOCKED":
                    print("[Matchmaking] Matchmaking blocked by server requirements.")
                    return
                elif decision == "ALREADY_IN_GAME":
                    print("[Matchmaking] Existing game session detected. Re-routing...")
                    await self.connect_direct_agent()
                    return
                    
                print(f"[Matchmaking] Entering matchmaking queue (Room: {entry_type.upper()})...")
                hello_msg = {"type": "hello", "entryType": entry_type}
                await ws.send(json.dumps(hello_msg))
                
                async for message_raw in ws:
                    msg = json.loads(message_raw)
                    msg_type = msg.get("type")
                    
                    if msg_type == "queued":
                        print("[Matchmaking] Waiting in matchmaking lobby...")
                    elif msg_type == "assigned":
                        print(f"[Matchmaking] Arena match found! Game ID: {msg.get('gameId')}")
                        await self.run_game_loop(ws)
                        break
                    elif msg_type in ("agent_view", "turn_advanced", "can_act_changed"):
                        print("[Matchmaking] Resumed active session successfully.")
                        if self.message_handler:
                            await self.message_handler(msg_type, msg, self)
                        await self.run_game_loop(ws)
                        break
                    elif msg_type == "not_selected":
                        print("[Matchmaking] Allocation timed out.")
                        break
                    elif msg_type == "error":
                        err_msg = msg.get("error", {}).get("message", "Unknown matchmaking error")
                        print(f"[Matchmaking Error] {err_msg}")
                        break
        except Exception as e:
            print(f"[Connection Error] {e}")
        finally:
            self.ws = None

    async def connect_direct_agent(self):
        url = "wss://cdn.clawroyale.ai/ws/agent"
        print(f"[Connection] Direct-connecting to game server: {url}")
        try:
            async with websockets.connect(url, additional_headers=self.headers) as ws:
                await self.run_game_loop(ws)
        except Exception as e:
            print(f"[Connection Error] {e}")