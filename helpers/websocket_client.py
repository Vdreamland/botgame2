import asyncio
import json
import websockets
from typing import Dict, Any

class ClawRoyaleWebSocketClient:
    def __init__(self, api_key: str, version: str, auth_type: str = "mr-auth"):
        self.api_key = api_key
        self.version = version
        self.auth_type = auth_type
        self.headers = self._build_headers()

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
        print("Connected to game socket. Awaiting server state updates...")
        async for message_raw in ws:
            msg = json.loads(message_raw)
            msg_type = msg.get("type")
            
            if msg_type in ("agent_view", "turn_advanced"):
                view = msg.get("view") or msg.get("agentView") or msg.get("agent_view") or msg.get("data") or {}
                self._handle_agent_view(view)
            elif msg_type == "action_result":
                print(f"[Action Result] {json.dumps(msg)}")
            elif msg_type == "error":
                print(f"[Server Error] {json.dumps(msg)}")
            else:
                print(f"[Server Push] Type: {msg_type} - content: {message_raw[:200]}")

    def _handle_agent_view(self, view: Dict[str, Any]):
        player = view.get("self") or view.get("player") or {}
        game_state = view.get("game") or view.get("gameState") or {}
        
        name = player.get("name", "Unknown")
        hp = player.get("hp", 0)
        ep = player.get("ep", 0)
        x = player.get("x", 0)
        y = player.get("y", 0)
        is_alive = player.get("isAlive") if player.get("isAlive") is not None else player.get("is_alive", True)
        
        day = game_state.get("day", 1)
        turn = game_state.get("turn", 1)
        weather = game_state.get("weather", "clear")
        
        region_data = view.get("currentRegion") or view.get("current_region") or {}
        terrain = region_data.get("terrain", "unknown") if isinstance(region_data, dict) else "unknown"
        
        print(f"\n--- [STATE] Day {day} Turn {turn} | Weather: {weather} ---")
        print(f"Agent: {name} | HP: {hp} | EP: {ep} | Location: ({x}, {y}) | Terrain: {terrain} | Alive: {is_alive}")
        
        inventory = player.get("inventory", [])
        if inventory:
            items_list = [item.get("name") for item in inventory if item]
            print(f"Inventory: {items_list}")
        
        if not is_alive:
            print("Agent is dead. Game session terminated.")

    async def connect_and_join(self, entry_type: str = "free"):
        url = "wss://cdn.clawroyale.ai/ws/join"
        print(f"Connecting to unified matchmaker: {url}")
        
        async with websockets.connect(url, additional_headers=self.headers) as ws:
            welcome_raw = await ws.recv()
            welcome = json.loads(welcome_raw)
            print(f"Welcome Frame: {json.dumps(welcome)}")
            
            decision = welcome.get("decision")
            if decision == "BLOCKED":
                print("Matchmaking blocked by server readiness constraints.")
                return
            elif decision == "ALREADY_IN_GAME":
                print("Active session found. Redirecting to direct agent socket...")
                await self.connect_direct_agent()
                return
                
            hello_msg = {"type": "hello", "entryType": entry_type}
            print(f"Sending hello handshaking: {json.dumps(hello_msg)}")
            await ws.send(json.dumps(hello_msg))
            
            async for message_raw in ws:
                msg = json.loads(message_raw)
                msg_type = msg.get("type")
                
                if msg_type == "queued":
                    print(f"Matchmaking Status: {json.dumps(msg)}")
                elif msg_type == "assigned":
                    print(f"Match Assigned! Game ID: {msg.get('gameId')}. Promoting socket...")
                    await self.run_game_loop(ws)
                    break
                elif msg_type == "not_selected":
                    print("Matchmaker allocation timed out.")
                    break
                elif msg_type == "error":
                    print(f"Handshake failed: {json.dumps(msg)}")
                    break

    async def connect_direct_agent(self):
        url = "wss://cdn.clawroyale.ai/ws/agent"
        print(f"Connecting directly to active agent session: {url}")
        async with websockets.connect(url, additional_headers=self.headers) as ws:
            await self.run_game_loop(ws)