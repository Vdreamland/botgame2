import asyncio
import json
import websockets
from typing import Dict, Any, Optional, Callable
from ai.detector import extract_agent_status, detect_connected_regions, detect_region_items, detect_region_enemies
from ai.decision_maker import decide_next_action
from .action_builder import build_action_payload
from games_log import print_game_state, print_action_intention

async def _handle_agent_death(msg: Dict[str, Any], view: Dict[str, Any], context: Any, source: str):
    print(f"[Alert] Agent has died (Detected via {source}). Connection closing...")
    game_id = msg.get("gameId") or view.get("gameId") or view.get("game", {}).get("gameId")
    if game_id and hasattr(context, "dead_games") and context.dead_games is not None:
        context.dead_games.add(game_id)
    if context.ws:
        await context.ws.close()

def _find_entity_name_local(view: Dict[str, Any], target_id: str) -> str:
    if not target_id:
        return ""
    curr_reg = view.get("currentRegion", {}) or {}
    for inter in (curr_reg.get("interactables", []) or []):
        if isinstance(inter, dict) and inter.get("id") == target_id:
            f_type = inter.get("type") or inter.get("name") or "facility"
            return f_type.replace('_', ' ').title() + f" at {curr_reg.get('name', 'Current Region')}"
    for item in (curr_reg.get("items", []) or curr_reg.get("groundItems", []) or []):
        if isinstance(item, dict) and item.get("id") == target_id:
            return item.get("name") or item.get("type") or item.get("typeId") or ""
    for r in (view.get("visibleRegions", []) or []):
        if isinstance(r, dict):
            for inter in (r.get("interactables", []) or []):
                if isinstance(inter, dict) and inter.get("id") == target_id:
                    f_type = inter.get("type") or inter.get("name") or "facility"
                    return f_type.replace('_', ' ').title() + f" at {r.get('name', 'Visible Region')}"
            for item in (r.get("items", []) or r.get("groundItems", []) or []):
                if isinstance(item, dict) and item.get("id") == target_id:
                    return item.get("name") or item.get("type") or item.get("typeId") or ""
    self_data = view.get("self", {}) or {}
    for item in (self_data.get("inventory", []) or []):
        if isinstance(item, dict) and item.get("id") == target_id:
            return item.get("name") or item.get("type") or item.get("typeId") or ""
    for item in (self_data.get("equipment", {}) or {}).values():
        if isinstance(item, dict) and item.get("id") == target_id:
            return item.get("name") or item.get("type") or item.get("typeId") or ""
    for category in ("visibleAgents", "visibleMonsters", "visibleNPCs"):
        for entity in (view.get(category, []) or []):
            if isinstance(entity, dict):
                ent_id = entity.get("id") or entity.get("agentId") or entity.get("monsterId") or entity.get("npcId")
                if ent_id == target_id:
                    return entity.get("name") or entity.get("username") or entity.get("agentName") or entity.get("type") or ""
    return ""

async def _execute_best_action_local(view: Dict[str, Any], regions: Any, context: Any):
    try:
        next_action = decide_next_action(view, context)
        if next_action and next_action.get("type") == "action":
            print_action_intention(next_action, regions, _find_entity_name_local, view)
            if context.ws:
                await context.ws.send(json.dumps(next_action))
    except Exception as e:
        print(f"[DEBUG ERROR] Gagal mengeksekusi decide_next_action: {e}")

async def handle_game_message(msg_type: str, msg: Dict[str, Any], context: Any):
    if msg_type in ("agent_view", "turn_advanced"):
        view = msg.get("view") or msg.get("agentView") or msg.get("agent_view") or msg.get("data") or {}
        context.last_view = view
        
        status = extract_agent_status(msg)
        regions = detect_connected_regions(view)
        context.last_regions = regions
        region_items = detect_region_items(view)
        region_enemies = detect_region_enemies(view)
        
        name = status["name"]
        context.agent_name = name
        context.agent_id = status["id"]
        
        hp = status["hp"]
        ep = status["ep"]
        is_alive = status["is_alive"]
        is_death_zone = status["is_death_zone"]
        ruin = status["ruin"]
        
        current_state = (status["global_turn"], hp, ep, status["x"], status["y"], status["kill"], status["region_name"], status["terrain"], is_death_zone, status["weather"], status["vision"], status["num_links"], str(ruin), str(region_enemies))
        last_printed = getattr(context, "last_state", None)
        
        if last_printed != current_state:
            print_game_state(status, regions, region_items, region_enemies, ruin, is_death_zone)
            cooldown = view.get("self", {}).get("cooldownRemainingMs", 0)
            can_act_msg = (cooldown == 0) or msg.get("canAct") or view.get("self", {}).get("canAct", False) or view.get("self", {}).get("can_act", False)
            if hp > 0 and can_act_msg:
                await _execute_best_action_local(view, regions, context)
            context.last_state = current_state
        
        last_hp = getattr(context, "last_hp", None)
        if last_hp is not None and last_hp != hp:
            diff = last_hp - hp
            if diff > 0:
                print(f"[Status Update] You took {diff} damage! HP is now {hp}/{view.get('self', {}).get('maxHp', 100)}")
            elif diff < 0:
                print(f"[Status Update] You healed {abs(diff)} HP! HP is now {hp}/{view.get('self', {}).get('maxHp', 100)}")
        context.last_hp = hp
        
        if not is_alive:
            await _handle_agent_death(msg, view, context, "state view")
            
    elif msg_type == "can_act_changed":
        can_act = msg.get("canAct", False) or msg.get("can_act", False)
        if can_act:
            print("[Action Ready] Cooldown over. You can act now!")
            last_view = getattr(context, "last_view", None)
            last_regions = getattr(context, "last_regions", [])
            if last_view and last_regions:
                await _execute_best_action_local(last_view, last_regions, context)
            
    elif msg_type == "error":
        err_msg = msg.get("error", {}).get("message", json.dumps(msg))
        print(f"[Server Error] {err_msg}")
        
    elif msg_type == "log":
        log_data = msg.get("log", {})
        message = log_data.get("message", "")
        agent_id = msg.get("agentId") or log_data.get("agentId")
        
        if (agent_id == context.agent_id) or (context.agent_name and context.agent_name in message):
            if message:
                print(f"[World Log] {message}")
                
        if context.agent_name:
            lower_msg = message.lower()
            name_lower = context.agent_name.lower()
            
            is_my_death = False
            if f"{name_lower} died" in lower_msg:
                is_my_death = True
            elif f"{name_lower} perished" in lower_msg:
                is_my_death = True
            elif f"{name_lower} was killed" in lower_msg:
                is_my_death = True
            elif f"{name_lower} was eliminated" in lower_msg:
                is_my_death = True
            elif f"{name_lower} has been eliminated" in lower_msg:
                is_my_death = True
            elif f"killed {name_lower}" in lower_msg or f"eliminated {name_lower}" in lower_msg:
                is_my_death = True
                
            if is_my_death:
                await _handle_agent_death(msg, {}, context, "world log")

class ClawRoyaleWebSocketClient:
    JOIN_URL = "wss://cdn.clawroyale.ai/ws/join"
    AGENT_URL = "wss://cdn.clawroyale.ai/ws/agent"

    def __init__(self, api_key: str, version: str, auth_type: str = "mr-auth", message_handler: Optional[Callable] = None, dead_games: Optional[set] = None):
        self.api_key = api_key
        self.version = version
        self.auth_type = auth_type
        self.message_handler = message_handler or handle_game_message
        self.dead_games = dead_games
        self.ws = None
        self.agent_name = None
        self.agent_id = None

    def _build_headers(self) -> Dict[str, str]:
        headers = {"X-Version": self.version}
        if self.auth_type == "mr-auth":
            headers["Authorization"] = f"mr-auth {self.api_key}"
        elif self.auth_type == "Bearer":
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            headers["X-API-Key"] = self.api_key
        return headers

    async def connect_and_join(self, entry_type: str = "free") -> str:
        headers = self._build_headers()
        async with websockets.connect(self.JOIN_URL, additional_headers=headers) as ws:
            self.ws = ws
            welcome_msg = await ws.recv()
            
            join_payload = {"type": "hello", "data": {"entry_type": entry_type}}
            await ws.send(json.dumps(join_payload))
            
            async for raw_msg in ws:
                msg = json.loads(raw_msg)
                msg_type = msg.get("type")
                msg_data = msg.get("data", {})
                
                if msg_type == "queued":
                    print("[Matchmaking] Waiting in matchmaking lobby...")
                elif msg_type == "assigned":
                    game_id = msg_data.get("gameId") or msg_data.get("game_id")
                    print(f"[Matchmaking] Arena match found! Game ID: {game_id}")
                    await self._listen_loop()
                    return "FINISHED"
                elif msg_type == "error":
                    err_code = msg_data.get("error", {}).get("code")
                    if err_code == "READINESS_BLOCKED":
                        return "BLOCKED"
                    print(f"[Matchmaking Error] {msg_data}")
                    return "ERROR"

    async def connect_direct_agent(self):
        headers = self._build_headers()
        async with websockets.connect(self.AGENT_URL, additional_headers=headers) as ws:
            self.ws = ws
            print("[Socket] Successfully connected to live arena stream.")
            await self._listen_loop()

    async def _listen_loop(self):
        async for raw_msg in self.ws:
            msg = json.loads(raw_msg)
            msg_type = msg.get("type")
            await self.message_handler(msg_type, msg, self)