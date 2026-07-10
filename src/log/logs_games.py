import json
import websockets
import logging
import sys
import asyncio
import re
from ai.detector import AgentInfoDetector

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
            logger.info(f"[{self.bot_name}] Connected to local web log server at {self.web_log_url}")
        except Exception:
            self.ws = None
            logger.info(f"[{self.bot_name}] Web log server offline. Falling back to PowerShell.")

    async def close(self):
        if self.ws:
            await self.ws.close()

    async def send_log(self, payload):
        ws_success = False
        if self.ws:
            try:
                payload["bot_name"] = self.bot_name
                await asyncio.wait_for(self.ws.send(json.dumps(payload)), timeout=2.0)
                ws_success = True
            except Exception:
                self.ws = None
        
        msg_type = payload.get("type")
        
        if ws_success and msg_type in ("detail", "status_update", "turn", "waiting"):
            return
        
        if msg_type == "turn":
            logger.info(f"[{self.bot_name}] [Turn {payload.get('turn')}] Status: {payload.get('status')}")
        elif msg_type == "detail":
            logger.info(f"[{self.bot_name}] -> Game Log: {payload.get('message')}")
        elif msg_type == "waiting":
            logger.info(f"[{self.bot_name}] [Turn {payload.get('turn')}] Game status: waiting. Waiting for other agents...")
        elif msg_type == "ended":
            logger.info(f"[{self.bot_name}] Game has ended.")
        elif msg_type == "finished":
            logger.info(f"[{self.bot_name}] Game finished or Agent is no longer alive. Status: {payload.get('status')}")
        elif msg_type == "reenter":
            logger.info(f"[{self.bot_name}] Gameplay frames detected. Re-entering active loop.")

    async def send_agent_info(self, view_data, turn=None, logs_list=None):
        detector = AgentInfoDetector(view_data)
        
        hp_line = f"Hp {detector.get_hp()}/{detector.get_max_hp()} / Ep {detector.get_ep()}/{detector.get_max_ep()} / Kill {detector.get_kills()}"
        atk_def_line = f"ATK: {detector.get_atk()} / DEF: {detector.get_def()}"
        
        equipped = detector.get_equipped()
        weapon_name = "None"
        armor_name = "None"
        weapon_item = equipped.get("weapon")
        if isinstance(weapon_item, dict) and weapon_item.get("name"):
            weapon_name = weapon_item.get("name")
        armor_item = equipped.get("armor") or equipped.get("armour")
        if isinstance(armor_item, dict) and armor_item.get("name"):
            armor_name = armor_item.get("name")
        eq_line = f"Equipped : Weapon : {weapon_name} / Armour : {armor_name}"
        
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
        
        loc_line = f"Location : {detector.get_location()} [{detector.get_current_zone_status()}] / Terrain : {detector.get_terrain().capitalize()} / Weather : {detector.get_weather().capitalize()} / Vision {detector.get_vision()} / Links {detector.get_links_count()}"
        
        await self.send_log({"type": "detail", "message": hp_line})
        await self.send_log({"type": "detail", "message": atk_def_line})
        await self.send_log({"type": "detail", "message": eq_line})
        await self.send_log({"type": "detail", "message": inv_line})
        await self.send_log({"type": "detail", "message": loc_line})

        zones = detector.get_zones()
        if zones:
            await self.send_log({"type": "detail", "message": ""})
            await self.send_log({"type": "detail", "message": "Zone Detector :"})
            for dist in sorted(zones.keys()):
                regions_str = ", ".join(zones[dist])
                await self.send_log({"type": "detail", "message": f"Layer {dist}: {regions_str}"})
        
        fac_logs = detector.get_facility_logs()
        if fac_logs:
            await self.send_log({"type": "detail", "message": ""})
            for line in fac_logs:
                await self.send_log({"type": "detail", "message": line})
        
        ground_logs = detector.get_ground_item_logs()
        if ground_logs:
            await self.send_log({"type": "detail", "message": ""})
            for line in ground_logs:
                await self.send_log({"type": "detail", "message": line})
        
        enemy_logs = detector.get_enemy_logs()
        if enemy_logs:
            await self.send_log({"type": "detail", "message": ""})
            for line in enemy_logs:
                await self.send_log({"type": "detail", "message": line})

        recent_logs = logs_list if logs_list is not None else (view_data.get("recentLogs") or [])

        attack_list = []
        item_list = []
        all_events_list = []

        for log_entry in recent_logs:
            log_str = ""
            if isinstance(log_entry, dict):
                log_str = log_entry.get("message", "")
            else:
                log_str = str(log_entry)

            if not log_str:
                continue

            if self.bot_name.lower() not in log_str.lower() and "you" not in log_str.lower():
                continue

            if log_str.endswith("."):
                log_clean = log_str[:-1]
            else:
                log_clean = log_str

            if log_clean not in all_events_list:
                all_events_list.append(log_clean)

            is_attack = any(k in log_str.lower() for k in ["attack", "kill", "damage", "defeat", "slay", "slain", "lost", "hp", "deathzone", "deadzone", "shrank", "hurt"])
            is_item = any(k in log_str.lower() for k in ["pick", "drop", "equip", "found", "use", "inventory", "took", "obtain", "grab"])

            if is_attack:
                cleaned = re.sub(rf"\b{re.escape(self.bot_name)}\b", "you", log_str, flags=re.IGNORECASE)
                cleaned = re.sub(r"\battacked\b", "attack", cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r"\bfor\b", "", cleaned, flags=re.IGNORECASE)
                cleaned = " ".join(cleaned.split())
                if cleaned.endswith("."):
                    cleaned = cleaned[:-1]
                if cleaned not in attack_list:
                    attack_list.append(cleaned)
            elif is_item:
                cleaned = re.sub(rf"\b{re.escape(self.bot_name)}\b", "you", log_str, flags=re.IGNORECASE)
                if cleaned.endswith("."):
                    cleaned = cleaned[:-1]
                if cleaned not in item_list:
                    item_list.append(cleaned)

        attack_str = " / ".join(attack_list) if attack_list else "None"
        item_str = " / ".join(item_list) if item_list else "None"
        all_events_str = " / ".join(all_events_list) if all_events_list else "None"

        await self.send_log({"type": "detail", "message": ""})
        await self.send_log({"type": "detail", "message": "Log :"})
        await self.send_log({"type": "detail", "message": f"attack : {attack_str}"})
        await self.send_log({"type": "detail", "message": f"item : {item_str}"})
        await self.send_log({"type": "detail", "message": ""})
        await self.send_log({"type": "detail", "message": "All Events Log :"})
        await self.send_log({"type": "detail", "message": f"{all_events_str}"})