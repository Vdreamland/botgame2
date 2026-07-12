from typing import Dict, Any

def extract_agent_status(view: Dict[str, Any]) -> Dict[str, Any]:
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
    
    turn = game_state.get("turn", 1)
    day = game_state.get("day", 1)
    
    atk = player.get("atk") or eff_stats.get("atk") or player.get("baseAtk", 0)
    defense = player.get("def") or eff_stats.get("def") or player.get("baseDef", 0)
    kills = player.get("kills") if player.get("kills") is not None else player.get("killCount", 0)
    
    # Mengekstrak nama wilayah (e.g. Bank) dan tipe daratan/fasilitas (e.g. cave)
    region_name = region_data.get("name", "Unknown") if isinstance(region_data, dict) else "Unknown"
    terrain = region_data.get("terrain", "unknown") if isinstance(region_data, dict) else "unknown"
    
    return {
        "name": name,
        "id": agent_id,
        "hp": hp,
        "ep": ep,
        "x": x,
        "y": y,
        "is_alive": is_alive,
        "turn": turn,
        "day": day,
        "atk": atk,
        "def": defense,
        "kill": kills,
        "region_name": region_name,
        "terrain": terrain
    }