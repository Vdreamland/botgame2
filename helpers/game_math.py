from enum import Enum
from typing import Dict

class TerrainType(Enum):
    PLAINS = "plains"
    FOREST = "forest"
    HILLS = "hills"
    RUINS = "ruins"
    WATER = "water"

class WeatherType(Enum):
    CLEAR = "clear"
    RAIN = "rain"
    FOG = "fog"
    STORM = "storm"

VISION_MODIFIERS: Dict[TerrainType, int] = {
    TerrainType.PLAINS: 1,
    TerrainType.FOREST: -1,
    TerrainType.HILLS: 2,
    TerrainType.RUINS: 0,
    TerrainType.WATER: 0,
}

WEATHER_VISION_MODIFIERS: Dict[WeatherType, int] = {
    WeatherType.CLEAR: 0,
    WeatherType.RAIN: -1,
    WeatherType.FOG: -2,
    WeatherType.STORM: -2,
}

WEATHER_COMBAT_MODIFIERS: Dict[WeatherType, int] = {
    WeatherType.CLEAR: 0,
    WeatherType.RAIN: -5,
    WeatherType.FOG: -10,
    WeatherType.STORM: -15,
}

ARMOR_DEFENSE_BONUS: Dict[str, int] = {
    "Leather": 4,
    "Chainmail": 12,
    "Plate": 20,
}

MONSTER_FALLBACK_STATS = {
    "wolf": {"hp": 25, "ep": 0, "atk": 15, "def": 1},
    "bear": {"hp": 30, "ep": 0, "atk": 12, "def": 3},
    "bandit": {"hp": 40, "ep": 0, "atk": 25, "def": 5},
    "guardian": {"hp": 150, "ep": 10, "atk": 12, "def": 120}
}

WEAPON_STATS = {
    "fist": {"atk": 0, "ep": 1, "range": 0, "type": "melee"},
    "knife": {"atk": 16, "ep": 1, "range": 0, "type": "melee"},
    "dagger": {"atk": 16, "ep": 1, "range": 0, "type": "melee"},
    "sword": {"atk": 24, "ep": 2, "range": 0, "type": "melee"},
    "katana": {"atk": 40, "ep": 3, "range": 0, "type": "melee"},
    "bow": {"atk": 8, "ep": 1, "range": 1, "type": "ranged"},
    "pistol": {"atk": 15, "ep": 2, "range": 1, "type": "ranged"},
    "sniper_rifle": {"atk": 32, "ep": 3, "range": 2, "type": "ranged"}
}

ARMOR_STATS = {
    "leather": {"def": 4},
    "leather_armor": {"def": 4},
    "chainmail": {"def": 12},
    "chainmail_armor": {"def": 12},
    "plate": {"def": 20},
    "plate_armor": {"def": 20}
}

RECOVERY_STATS = {
    "bandage": {"hp": 10, "ep": 0},
    "emergency_food": {"hp": 20, "ep": 0},
    "energy_drink": {"hp": 0, "ep": 5},
    "medkit": {"hp": 30, "ep": 5}
}

def get_vision_mod(terrain: TerrainType, weather: WeatherType) -> int:
    return VISION_MODIFIERS.get(terrain, 0) + WEATHER_VISION_MODIFIERS.get(weather, 0)

def calculate_damage(atk: int, weapon_bonus: int, def_val: int, weather: WeatherType) -> int:
    weather_mod = WEATHER_COMBAT_MODIFIERS.get(weather, 0)
    return max(1, atk + weapon_bonus - def_val + weather_mod)

def calculate_alert_change(action: str, current_gauge: int, is_active: bool) -> int:
    new_gauge = current_gauge
    if action == "explore":
        new_gauge += 2
    elif action == "clear_ruin":
        new_gauge += 4
    
    if is_active:
        new_gauge = max(0, new_gauge - 4)
    
    return new_gauge

def is_entity_alive(entity):
    if not isinstance(entity, dict):
        return False
    is_alive_camel = entity.get('isAlive')
    if is_alive_camel is not None:
        return bool(is_alive_camel)
    is_alive_snake = entity.get('is_alive')
    if is_alive_snake is not None:
        return bool(is_alive_snake)
    hp = entity.get('hp')
    if hp is not None:
        try:
            return float(hp) > 0
        except (ValueError, TypeError):
            pass
    return True