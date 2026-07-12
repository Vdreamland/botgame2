from typing import Dict, Any, List

def detect_connected_regions(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    connected = view.get("connectedRegions") or view.get("connected_regions") or []
    detected_list = []
    
    for region in connected:
        if isinstance(region, dict):
            region_name = region.get("name") or "Unknown Region"
            region_id = region.get("id") or "unknown_id"
            terrain = region.get("terrain") or "unknown"
            is_death_zone = region.get("isDeathZone") if region.get("isDeathZone") is not None else region.get("is_death_zone", False)
            detected_list.append({
                "id": region_id,
                "name": region_name,
                "terrain": terrain,
                "is_death_zone": is_death_zone,
                "is_visible": True
            })
        elif isinstance(region, str):
            detected_list.append({
                "id": region,
                "name": f"Hidden Region ({region[:8]})",
                "terrain": "unknown",
                "is_death_zone": False,
                "is_visible": False
            })
            
    return detected_list