import logging
import sys
import websockets
import json

logger = logging.getLogger("botgame.game")
logger.setLevel(logging.INFO)
if not logger.handlers:
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
            logger.info(f"Connected to local web log server at {self.web_log_url}")
        except Exception as e:
            logger.warning(f"Could not connect to local web log server: {e}")

    async def close(self):
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass

    async def send_log(self, payload):
        if not self.ws:
            return
        payload["bot_name"] = self.bot_name
        try:
            await self.ws.send(json.dumps(payload))
        except Exception:
            pass

    async def send_agent_info(self, view_data, turn=None, logs_list=None):
        if not view_data:
            return

        from ai.detector.agent_info import AgentInfoDetector
        from ai.detector.enemy_info import EnemyInfoDetector
        from ai.detector.zone_detector import ZoneDetector
        from ai.detector.deadzone_detector import DeadZoneDetector
        from ai.detector.ground_item_detector import GroundItemDetector
        from ai.detector.facility_detector import FacilityDetector

        detector = AgentInfoDetector(view_data)
        equipped = detector.get_equipped()
        inventory = detector.get_inventory()
        
        hp = detector.get_hp()
        max_hp = detector.get_max_hp()
        ep = detector.get_ep()
        max_ep = detector.get_max_ep()
        kill_count = detector.get_kills()
        atk = detector.get_atk()
        defender_def = detector.get_def()

        weapon_item = equipped.get("weapon")
        if isinstance(weapon_item, dict) and weapon_item.get("name"):
            weapon_name = weapon_item.get("name")
        else:
            weapon_name = str(weapon_item) if weapon_item else "None"

        armor_item = equipped.get("armor")
        if isinstance(armor_item, dict) and armor_item.get("name"):
            armor_name = armor_item.get("name")
        else:
            armor_name = str(armor_item) if armor_item else "None"

        current_region = view_data.get("currentRegion", {}) or {}
        current_region_name = current_region.get("name", "Unknown")
        is_death = current_region.get("isDeathZone") or current_region.get("isDeadZone") or False
        zone_status = "DeadZone" if is_death else "SafeZone"

        terrain_mods = current_region.get("terrainModifiers", {}) or {}
        terrain_type = current_region.get("terrain", "Plains")
        weather = view_data.get("weather", "Clear")
        vision = detector.get_vision()
        links_count = detector.get_links_count()

        recent_logs = logs_list if logs_list is not None else (view_data.get("recentLogs") or [])

        agent_payload = {
            "hp": hp,
            "maxHp": max_hp,
            "ep": ep,
            "maxEp": max_ep,
            "killCount": kill_count,
            "atk": atk,
            "def": defender_def,
            "weapon": weapon_name,
            "armor": armor_name,
            "locationName": current_region_name,
            "zoneStatus": zone_status,
            "terrain": terrain_type,
            "weather": weather,
            "vision": vision,
            "linksCount": links_count,
            "inventory": inventory
        }
        await self.send_log({"type": "agent_info", "agent": agent_payload, "turn": turn})

        if hp <= 0:
            await self.send_log({"type": "zones_info", "zones": {}})
            await self.send_log({"type": "facilities_info", "facilities": {}})
            await self.send_log({"type": "ground_info", "ground": {}})
            await self.send_log({"type": "enemies_info", "enemies": {}})
        else:
            zone_detector = ZoneDetector(view_data)
            zones_by_layer = zone_detector.detect_zones()
            zone_payload = {}
            for layer, regions_list in zones_by_layer.items():
                zone_payload[str(layer)] = [r.get("name") for r in regions_list if r.get("name")]
            await self.send_log({"type": "zones_info", "zones": zone_payload})

            facility_detector = FacilityDetector(view_data)
            fac_payload = {}
            for fac in facility_detector.visible_facilities:
                f_region = fac.get("regionId")
                f_type = fac.get("type")
                f_status = fac.get("status")
                f_name = fac.get("name", f_type)
                
                visible_regs_raw = view_data.get("visibleRegions", []) or []
                regions_map = {}
                for r in visible_regs_raw:
                    if isinstance(r, dict):
                        regions_map[r.get("id")] = r.get("name")
                regions_map[current_region.get("id")] = current_region.get("name")
                reg_name = regions_map.get(f_region, "Unknown")
                
                status_suffix = " [Already Used]" if f_status == "Used" else ""
                fac_payload[reg_name] = f_name + status_suffix
            await self.send_log({"type": "facilities_info", "facilities": fac_payload})

            region_distances = zone_detector.get_region_distances()
            ground_detector = GroundItemDetector(view_data)
            ground_items_by_layer = ground_detector.get_formatted_items_by_layer(region_distances)
            ground_payload = {}
            for r_name, items_list in ground_items_by_layer.items():
                if items_list:
                    ground_payload[r_name] = items_list
            await self.send_log({"type": "ground_info", "ground": ground_payload})

            enemy_detector = EnemyInfoDetector(view_data)
            enemies_by_layer = enemy_detector.get_enemies_by_layer(region_distances)
            enemy_payload = {}
            for r_name, enemies_list in enemies_by_layer.items():
                if enemies_list:
                    formatted_enemies = []
                    for enemy in enemies_list:
                        e_type = enemy.get("type", "Unknown")
                        if e_type == "agent":
                            weap = enemy.get("weapon", "None")
                            arm = enemy.get("armor", "None")
                            formatted_enemies.append(f"{enemy.get('name')} [Agent] (HP {enemy.get('hp')}/{enemy.get('maxHp')} / EP {enemy.get('ep')}/10, ATK: {enemy.get('atk')}, DEF: {enemy.get('def')}, Weapon: {weap}, Armour: {arm})")
                        elif e_type == "monster":
                            formatted_enemies.append(f"{enemy.get('name')} [Monster] (HP {enemy.get('hp')}/{enemy.get('maxHp')}', ATK: {enemy.get('atk')}, DEF: {enemy.get('def')})")
                        elif e_type == "guardian":
                            formatted_enemies.append(f"{enemy.get('name')} [Guardian] (HP {enemy.get('hp')}/150, ATK: {enemy.get('atk')}, DEF: {enemy.get('def')}, Weapon: None, Armour: None)")
                    enemy_payload[r_name] = formatted_enemies
            await self.send_log({"type": "enemies_info", "enemies": enemy_payload})

        move_list = []
        battle_list = []
        action_list = []
        for log_entry in recent_logs:
            log_str = ""
            if isinstance(log_entry, dict):
                log_str = log_entry.get("message", "")
            else:
                log_str = str(log_entry)
            
            if not log_str:
                continue
            
            log_clean = log_str
            log_lower = log_str.lower()
            
            if "move" in log_lower:
                if log_clean not in move_list:
                    move_list.append(log_clean)
            elif any(k in log_lower for k in ["attack", "kill", "damage", "defeat", "slay", "slain", "lost", "hp", "deathzone", "deadzone", "shrank", "hurt"]):
                if log_clean not in battle_list:
                    battle_list.append(log_clean)
            else:
                if log_clean not in action_list:
                    action_list.append(log_clean)

        battle_str = " / ".join(battle_list) if battle_list else "None"
        action_str = " / ".join(action_list) if action_list else "None"
        move_str = " / ".join(move_list) if move_list else "None"

        await self.send_log({"type": "detail", "message": ""})
        await self.send_log({"type": "detail", "message": "All Events Log :"})
        await self.send_log({"type": "detail", "message": f"Battle : {battle_str}"})
        await self.send_log({"type": "detail", "message": f"Action: {action_str}"})
        await self.send_log({"type": "detail", "message": f"Move : {move_str}"})