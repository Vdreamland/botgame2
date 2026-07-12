from typing import Dict, Any

# Pemetaan resmi nilai Vision Modifier berdasarkan tipe terrain/fasilitas
TERRAIN_VISION_MODS = {
    "plains": 1,
    "forest": -1,
    "hills": 2,
    "ruins": 0,
    "water": 0,
    "cave": -2
}

def extract_agent_status(msg: Dict[str, Any]) -> Dict[str, Any]:
    if "view" in msg:
        view = msg.get("view") or {}
        global_turn = msg.get("turn") or 1
    else:
        view = msg
        global_turn = view.get("turn") or 1
        
    player = view.get("self") or view.get("player") or {}
    game_state = view.get("game") or view.get("gameState") or {}
    region_data = view.get("currentRegion") or view.get("current_region") or {}
    
    eff_stats = player.get("effectiveStats") or {}
    
    name = player.get("name", "Unknown")
    agent_id = player.get("id")
    hp = player.get("hp", 0)
    ep = player.get("ep", 0)
    x = player.get("x", 0)
    y = player.get("y", 0)
    is_alive = player.get("isAlive") if player.get("isAlive") is not None else player.get("is_alive", True)
    
    day = (global_turn - 1) // 4 + 1
    day_turn = (global_turn - 1) % 4 + 1
    
    atk = player.get("atk") or eff_stats.get("atk") or player.get("baseAtk", 0)
    defense = player.get("def") or eff_stats.get("def") or player.get("baseDef", 0)
    kills = player.get("kills") if player.get("kills") is not None else player.get("killCount", 0)
    
    region_name = region_data.get("name", "Unknown") if isinstance(region_data, dict) else "Unknown"
    terrain = region_data.get("terrain", "unknown") if isinstance(region_data, dict) else "unknown"
    
    is_death_zone = False
    if isinstance(region_data, dict):
        is_death_zone = region_data.get("isDeathZone") if region_data.get("isDeathZone") is not None else region_data.get("is_death_zone", False)
    
    weather = game_state.get("weather", "clear")
    num_links = len(region_data.get("connections") or [])
    
    # Ambil nilai Vision murni dari terrain petak saat ini
    terrain_lower = terrain.lower()
    facility_lower = (region_data.get("facility") or "").lower()
    if facility_lower == "cave" or terrain_lower == "cave":
        vision = -2
    else:
        vision = TERRAIN_VISION_MODS.get(terrain_lower, 0)
        
    # Deteksi status candi/ruin secara aman
    ruin_raw = region_data.get("ruin")
    ruin = None
    if isinstance(ruin_raw, dict):
        ruin = {
            "status": ruin_raw.get("status") or "Available",
            "gauge": ruin_raw.get("gauge", 0),
            "max_gauge": ruin_raw.get("maxGauge") or ruin_raw.get("max_gauge") or 3,
            "explorer": ruin_raw.get("explorerName") or ruin_raw.get("explorer") or "—"
        }
    
    return {
        "name": name,
        "id": agent_id,
        "hp": hp,
        "ep": ep,
        "x": x,
        "y": y,
        "is_alive": is_alive,
        "global_turn": global_turn,
        "turn": day_turn,
        "day": day,
        "atk": atk,
        "def": defense,
        "kill": kills,
        "region_name": region_name,
        "terrain": terrain,
        "is_death_zone": is_death_zone,
        "weather": weather,
        "vision": vision,
        "num_links": num_links,
        "ruin": ruin
    }