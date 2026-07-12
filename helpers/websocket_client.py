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
        print("[Socket] Successfully connected to live arena stream.")
        async for message_raw in ws:
            msg = json.loads(message_raw)
            msg_type = msg.get("type")
            
            if msg_type in ("agent_view", "turn_advanced"):
                view = msg.get("view") or msg.get("agentView") or msg.get("agent_view") or msg.get("data") or {}
                self._handle_agent_view(view)
            elif msg_type == "action_result":
                success = msg.get("success", True)
                action = msg.get("action", "unknown")
                if success:
                    print(f"[Action] Success: Executed '{action}'")
                else:
                    err_msg = msg.get("error", {}).get("message", "Unknown error")
                    print(f"[Action] Failed: Executed '{action}' - Error: {err_msg}")
            elif msg_type == "item_picked":
                agent_id = msg.get("agentId", "")[:8]
                item = msg.get("item", {})
                item_name = item.get("name", "an item")
                print(f"[Activity] Agent {agent_id} picked up: {item_name}")
            elif msg_type == "agent_equipped":
                agent_id = msg.get("agentId", "")[:8]
                item_name = msg.get("name", "an item")
                print(f"[Activity] Agent {agent_id} equipped: {item_name}")
            elif msg_type == "ruin_state_changed":
                gauge = msg.get("gauge", 0)
                max_gauge = msg.get("maxGauge", 3)
                print(f"[Ruin] Exploration gauge changed to {gauge}/{max_gauge}")
            elif msg_type == "error":
                err_msg = msg.get("error", {}).get("message", message_raw)
                print(f"[Server Error] {err_msg}")
            elif msg_type == "log":
                log_data = msg.get("log", {})
                message = log_data.get("message")
                if message:
                    print(f"[World Log] {message}")

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
            print("[Alert] Agent has died. Connection closing...")

    async def connect_and_join(self, entry_type: str = "free"):
        url = "wss://cdn.clawroyale.ai/ws/join"
        print(f"[Connection] Connecting to matchmaker: {url}")
        
        async with websockets.connect(url, additional_headers=self.headers) as ws:
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
                    if msg_type in ("agent_view", "turn_advanced"):
                        view = msg.get("view") or msg.get("agentView") or {}
                        self._handle_agent_view(view)
                    await self.run_game_loop(ws)
                    break
                elif msg_type == "not_selected":
                    print("[Matchmaking] Allocation timed out.")
                    break
                elif msg_type == "error":
                    err_msg = msg.get("error", {}).get("message", "Unknown matchmaking error")
                    print(f"[Matchmaking Error] {err_msg}")
                    break

    async def connect_direct_agent(self):
        url = "wss://cdn.clawroyale.ai/ws/agent"
        print(f"[Connection] Direct-connecting to game server: {url}")
        async with websockets.connect(url, additional_headers=self.headers) as ws:
            await self.run_game_loop(ws)