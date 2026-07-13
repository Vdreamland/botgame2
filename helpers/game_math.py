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