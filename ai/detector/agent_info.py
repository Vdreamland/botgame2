import json
from typing import Dict, Any
from helpers.game_math import get_vision_mod

def extract_agent_status(msg: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(msg, dict):
        try:
            data = json.loads(msg)
        except Exception:
            return {}
    else:
        data = msg

    view = data.get("view") or data.get("agentView") or data.get("agent_view") or data.get("data") or {}
    self_data = view.get("self", {}) or {}
    current_region = view.get("currentRegion", {}) or {}
    
    agent_id = self_data.get("id") or self_data.get("agentId") or self_data.get("agent_id") or "unknown"
    name = self_data.get("name") or "unknown"
    hp = self_data.get("hp", 100)
    ep = self_data.get("ep", 10)
    x = self_data.get("x", 0)
    y = self_data.get("y", 0)
    is_alive = self_data.get("isAlive", True) if self_data.get("isAlive") is not None else self_data.get("is_alive", True)
    
    global_turn = data.get("globalTurn") or data.get("global_turn") or data.get("turn") or 1
    day = (global_turn - 1) // 4 + 1
    turn_in_day = (global_turn - 1) % 4 + 1
    
    atk = self_data.get("atk", 25)
    defense = self_data.get("def", 5)
    kills = self_data.get("kills", 0) if self_data.get("kills") is not None else self_data.get("kill", 0)
    
    region_name = current_region.get("name") or current_region.get("id") or "unknown"
    is_death_zone = current_region.get("isDeathZone", False) or current_region.get("is_death_zone", False)
    terrain = current_region.get("terrain", "unknown")
    weather = current_region.get("weather", "clear")
    
    vision_mod = get_vision_mod(terrain, weather)
    
    num_links = len(current_region.get("connections", []))
    ruin = current_region.get("ruins")
    
    equipped_weapon = self_data.get("equippedWeapon")
    if isinstance(equipped_weapon, dict):
        weapon_name = equipped_weapon.get("name") or equipped_weapon.get("id") or "None"
    else:
        weapon_name = self_data.get("equippedWeaponId") or "None"
        
    equipped_armor = self_data.get("equippedArmor")
    if isinstance(equipped_armor, dict):
        armor_name = equipped_armor.get("name") or equipped_armor.get("id") or "None"
    else:
        armor_name = self_data.get("equippedArmorId") or "None"
        
    inv_items = self_data.get("inventory", []) or []
    inv_strings = []
    for item in inv_items:
        if isinstance(item, dict):
            item_name = item.get("name") or item.get("id") or "Item"
            qty = item.get("qty") or item.get("quantity") or 1
            qty_str = f" x{qty}" if qty > 1 else ""
            inv_strings.append(f"{item_name}{qty_str}")
    inv_display = ", ".join(inv_strings) if inv_strings else "none"
    
    return {
        "id": agent_id,
        "name": name,
        "hp": hp,
        "ep": ep,
        "x": x,
        "y": y,
        "is_alive": is_alive,
        "global_turn": global_turn,
        "turn": turn_in_day,
        "day": day,
        "atk": atk,
        "def": defense,
        "kill": kills,
        "region_name": region_name,
        "is_death_zone": is_death_zone,
        "terrain": terrain,
        "weather": weather,
        "vision": vision_mod,
        "vision_mod": vision_mod,
        "num_links": num_links,
        "links_count": num_links,
        "ruin": ruin,
        "weapon": weapon_name,
        "armor": armor_name,
        "inventory": inv_display
    }