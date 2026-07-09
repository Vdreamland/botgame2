import json
import websockets
import logging
import sys
from ai.detector.agent_info import AgentInfoDetector

logger = logging.getLogger("botgame.game")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

class GameLogSender:
    def __init__(self, bot_name, web_log_url):
        self.bot_name = bot_name
        self.web_log_url = web_log_url
        self.ws = None

    async def connect(self):
        try:
            self.ws = await websockets.connect(self.web_log_url)
        except Exception:
            self.ws = None
            logger.info(f"[{self.bot_name}] Web log server offline. Falling back to PowerShell.")

    async def close(self):
        if self.ws:
            await self.ws.close()

    async def send_log(self, payload):
        if self.ws:
            try:
                payload["bot_name"] = self.bot_name
                await self.ws.send(json.dumps(payload))
                return
            except Exception:
                self.ws = None
        
        if payload.get("type") == "turn":
            logger.info(f"[{self.bot_name}] [Turn {payload.get('turn')}] Status: {payload.get('status')}")
        elif payload.get("type") == "detail":
            logger.info(f"[{self.bot_name}]  -> Game Log: {payload.get('message')}")
        elif payload.get("type") == "waiting":
            logger.info(f"[{self.bot_name}] [Turn {payload.get('turn')}] Game status: waiting. Waiting for other agents...")
        elif payload.get("type") == "ended":
            logger.info(f"[{self.bot_name}] Game has ended.")
        elif payload.get("type") == "finished":
            logger.info(f"[{self.bot_name}] Game finished or Agent is no longer alive. Status: {payload.get('status')}")
        elif payload.get("type") == "reenter":
            logger.info(f"[{self.bot_name}] Gameplay frames detected. Re-entering active loop.")

    async def send_agent_info(self, view_data):
        detector = AgentInfoDetector(view_data)
        
        hp_line = f"Hp {detector.get_hp()}/{detector.get_max_hp()} / Ep {detector.get_ep()}/{detector.get_max_ep()} / Kill {detector.get_kills()}"
        atk_def_line = f"ATK: {detector.get_atk()} / DEF: {detector.get_def()}"
        
        equipped = detector.get_equipped()
        eq_names = []
        for eq_type, eq_item in equipped.items():
            if isinstance(eq_item, dict) and eq_item.get("name"):
                eq_names.append(eq_item.get("name"))
        eq_str = ", ".join(eq_names) if eq_names else "None"
        eq_line = f"Equipped : {eq_str}"
        
        inventory = detector.get_inventory()
        grouped_inv = {}
        for item in inventory:
            name = item.get("name", "Unknown")
            qty = item.get("quantity", 1)
            grouped_inv[name] = grouped_inv.get(name, 0) + qty
            
        inv_items = ", ".join([f"{name} [{qty}]" for name, qty in grouped_inv.items()])
        if not inv_items:
            inv_items = "Empty"
        inv_line = f"Inventory ({len(inventory)}/{detector.get_max_inventory()} Slots) : {inv_items}"
        
        loc_line = f"Location : {detector.get_location()} / Terrain : {detector.get_terrain()} / Weather : {detector.get_weather()} / Vision {detector.get_vision()} / Links {detector.get_links_count()}"
        
        await self.send_log({"type": "detail", "message": hp_line})
        await self.send_log({"type": "detail", "message": atk_def_line})
        await self.send_log({"type": "detail", "message": eq_line})
        await self.send_log({"type": "detail", "message": inv_line})
        await self.send_log({"type": "detail", "message": loc_line})