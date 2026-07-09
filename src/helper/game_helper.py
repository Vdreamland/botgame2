MONSTERS = {
    "wolf": {
        "hp": 25,
        "atk": 15,
        "def": 1,
        "drops": ["bandage", "knife"]
    },
    "bear": {
        "hp": 30,
        "atk": 12,
        "def": 3,
        "drops": ["medkit", "sword"]
    },
    "bandit": {
        "hp": 40,
        "atk": 25,
        "def": 5,
        "drops": ["katana", "pistol"]
    }
}

GUARDIAN = {
    "hp": 150,
    "atk": 12,
    "def": 120,
    "ep": 10,
    "vision": 1,
    "range_bonus": 2
}

WEAPONS = {
    "fist": {
        "atk_bonus": 0,
        "range": 0,
        "ep_cost": 1
    },
    "knife": {
        "atk_bonus": 16,
        "range": 0,
        "ep_cost": 1
    },
    "dagger": {
        "atk_bonus": 16,
        "range": 0,
        "ep_cost": 1
    },
    "sword": {
        "atk_bonus": 24,
        "range": 0,
        "ep_cost": 2
    },
    "katana": {
        "atk_bonus": 40,
        "range": 0,
        "ep_cost": 3
    },
    "bow": {
        "atk_bonus": 8,
        "range": 1,
        "ep_cost": 1
    },
    "pistol": {
        "atk_bonus": 15,
        "range": 1,
        "ep_cost": 2
    },
    "sniper": {
        "atk_bonus": 32,
        "range": 2,
        "ep_cost": 3
    }
}

ARMOR = {
    "leather": {
        "def_bonus": 4
    },
    "chainmail": {
        "def_bonus": 12
    },
    "plate": {
        "def_bonus": 20
    }
}

RECOVERY = {
    "bandage": {
        "hp_restore": 10,
        "ep_restore": 0
    },
    "emergency_food": {
        "hp_restore": 20,
        "ep_restore": 5
    },
    "energy_drink": {
        "hp_restore": 0,
        "ep_restore": 5
    },
    "medkit": {
        "hp_restore": 30,
        "ep_restore": 0
    }
}

TERRAIN_MODS = {
    "plains": {
        "vision": 1,
        "move_cost": 1
    },
    "hills": {
        "vision": 2,
        "move_cost": 1
    },
    "forest": {
        "vision": -1,
        "move_cost": 1
    },
    "cave": {
        "vision": -2,
        "move_cost": 1
    },
    "ruins": {
        "vision": 0,
        "move_cost": 1
    },
    "water": {
        "vision": 0,
        "move_cost": 1
    }
}

WEATHER_MODS = {
    "clear": {
        "vision": 0,
        "atk_modifier": 0
    },
    "rain": {
        "vision": -1,
        "atk_modifier": -3
    },
    "fog": {
        "vision": -2,
        "atk_modifier": 0
    },
    "storm": {
        "vision": -2,
        "atk_modifier": -5
    }
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
    if not item_name:
        return 0
    name_lower = item_name.lower()
    for w_key, w_data in WEAPONS.items():
        if w_key in name_lower:
            return w_data.get("atk_bonus", 0)
    return 0

def get_armor_bonus(item_name):
    if not item_name:
        return 0
    name_lower = item_name.lower()
    for a_key, a_data in ARMOR.items():
        if a_key in name_lower:
            return a_data.get("def_bonus", 0)
    return 0

def calculate_damage(attacker_atk, weapon_bonus, defender_def, weather_mod=0):
    return max(1, attacker_atk + weapon_bonus - defender_def + weather_mod)