WEAPONS = {
    "fist": { "atk_bonus": 0, "range": 1, "ep_cost": 0 },
    "knife": { "atk_bonus": 5, "range": 1, "ep_cost": 2 },
    "dagger": { "atk_bonus": 10, "range": 1, "ep_cost": 2 },
    "sword": { "atk_bonus": 24, "range": 1, "ep_cost": 2 },
    "katana": { "atk_bonus": 40, "range": 1, "ep_cost": 2 },
    "bow": { "atk_bonus": 8, "range": 2, "ep_cost": 2 },
    "pistol": { "atk_bonus": 24, "range": 2, "ep_cost": 3 },
    "sniper": { "atk_bonus": 32, "range": 3, "ep_cost": 3 }
}

ARMOR = {
    "leather": { "def_bonus": 4 },
    "chainmail": { "def_bonus": 12 },
    "plate": { "def_bonus": 20 }
}

RECOVERY = {
    "bandage": { "hp_restore": 15, "ep_restore": 0 },
    "emergency_food": { "hp_restore": 10, "ep_restore": 2 },
    "energy_drink": { "hp_restore": 0, "ep_restore": 4 },
    "medkit": { "hp_restore": 50, "ep_restore": 0 }
}

UTILITY = {
    "binoculars": { "vision_bonus": 1 }
}

TERRAIN_MODS = {
    "plains": { "hp_mod": 0, "ep_mod": 0 },
    "hills": { "hp_mod": 0, "ep_mod": -1 },
    "forest": { "hp_mod": 0, "ep_mod": 0 },
    "cave": { "hp_mod": -5, "ep_mod": 0 },
    "ruins": { "hp_mod": 0, "ep_mod": 0 },
    "water": { "hp_mod": 0, "ep_mod": -2 }
}

WEATHER_MODS = {
    "clear": { "atk_mod": 0, "vision_mod": 0 },
    "rain": { "atk_mod": -5, "vision_mod": -1 },
    "fog": { "atk_mod": 0, "vision_mod": -2 },
    "storm": { "atk_mod": -10, "vision_mod": -3 }
}

FACILITIES = {
    "supply_cache": { "interact_action": "search" },
    "medical_facility": { "interact_action": "heal" },
    "watchtower": { "interact_action": "scan" },
    "broadcast_station": { "interact_action": "broadcast" }
}

MONSTERS = {
    "wolf": { "hp": 25, "atk": 15, "def": 1, "drops": ["bandage", "emergency_food"] },
    "bear": { "hp": 30, "atk": 12, "def": 3, "drops": ["energy_drink", "medkit"] },
    "bandit": { "hp": 40, "atk": 25, "def": 5, "drops": ["sMoltz", "weapon", "armor", "recovery"] }
}

GUARDIAN = {
    "hp": 150,
    "atk": 12,
    "def": 120,
    "ep": 10,
    "vision": 1,
    "range_bonus": 2
}

AGENT_BASE = {
    "hp": 100,
    "atk": 25,
    "def": 5,
    "ep": 10,
    "max_ep": 10,
    "vision": 1
}

def get_weapon_bonus(item_name):
    weapon = WEAPONS.get(item_name)
    if weapon:
        return weapon.get("atk_bonus", 0)
    return 0

def get_armor_bonus(item_name):
    armor = ARMOR.get(item_name)
    if armor:
        return armor.get("def_bonus", 0)
    return 0

def calculate_damage(attacker_atk, weapon_bonus, defender_def, weather_mod=0):
    total_atk = attacker_atk + weapon_bonus + weather_mod
    damage = total_atk - defender_def
    return max(1, damage)

def normalize_item_name(name):
    if not name:
        return ""
    if isinstance(name, dict):
        name = name.get("name", "")
    norm = str(name).lower().replace(" ", "_")
    if "sniper" in norm:
        return "sniper"
    if "plate" in norm:
        return "plate"
    if "chainmail" in norm:
        return "chainmail"
    if "leather" in norm:
        return "leather"
    return norm

def get_item_name(item):
    if not item:
        return ""
    if isinstance(item, dict):
        return item.get("name", "")
    return str(item)

def get_item_id(item):
    if isinstance(item, dict):
        return item.get("id")
    return None

def resolve_equipped(view_data, inventory):
    self_data = view_data.get("self", {}) or {}
    equipped_dict = self_data.get("equipped")

    eq_weapon_raw = None
    eq_armor_raw = None

    if isinstance(equipped_dict, dict):
        eq_weapon_raw = equipped_dict.get("weapon")
        eq_armor_raw = equipped_dict.get("armor")
    else:
        eq_weapon_raw = self_data.get("equippedWeapon")
        eq_armor_raw = self_data.get("equippedArmor")

    eq_weapon_name = ""
    eq_armor_name = ""

    if eq_weapon_raw:
        if isinstance(eq_weapon_raw, dict):
            eq_weapon_name = eq_weapon_raw.get("name", "")
        else:
            eq_weapon_name = str(eq_weapon_raw)

    if eq_armor_raw:
        if isinstance(eq_armor_raw, dict):
            eq_armor_name = eq_armor_raw.get("name", "")
        else:
            eq_armor_name = str(eq_armor_raw)

    eq_weapon_id = None
    eq_armor_id = None

    if eq_weapon_name:
        for item in inventory:
            if isinstance(item, dict) and normalize_item_name(item.get("name")) == normalize_item_name(eq_weapon_name):
                eq_weapon_id = item.get("id")
                break

    if eq_armor_name:
        for item in inventory:
            if isinstance(item, dict) and normalize_item_name(item.get("name")) == normalize_item_name(eq_armor_name):
                eq_armor_id = item.get("id")
                break

    return {
        "weapon_name": eq_weapon_name,
        "armor_name": eq_armor_name,
        "weapon_id": eq_weapon_id,
        "armor_id": eq_armor_id
    }

def get_region_distances(view_data):
    view = view_data
    current_region = view.get("currentRegion", {}) or {}
    start_id = current_region.get("id")
    if not start_id:
        return {}

    visible_regions = view.get("visibleRegions", []) or []
    regions = {start_id: current_region}
    for r in visible_regions:
        r_id = r.get("id")
        if r_id:
            regions[r_id] = r

    queue = [(start_id, 0)]
    visited = {start_id: 0}

    while queue:
        curr_id, d = queue.pop(0)
        curr_reg = regions.get(curr_id, {})
        conns = curr_reg.get("connections") or curr_reg.get("links") or []
        for neighbor_id in conns:
            if neighbor_id in regions and neighbor_id not in visited:
                visited[neighbor_id] = d + 1
                queue.append((neighbor_id, d + 1))
    return visited