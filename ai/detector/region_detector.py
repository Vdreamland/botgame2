from typing import Dict, Any, List

def detect_connected_regions(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    connected = view.get("connectedRegions") or view.get("connected_regions") or []
    current_region = view.get("currentRegion") or view.get("current_region") or {}
    connections = current_region.get("connections") or []
    
    detected_list = []
    seen_ids = set()
    
    # 1. Deteksi region tetangga yang terlihat dalam jangkauan visi (jika ada)
    for region in connected:
        if isinstance(region, dict):
            region_id = region.get("id") or "unknown_id"
            region_name = region.get("name") or region_id[:8]
            terrain = region.get("terrain") or "unknown"
            is_death_zone = region.get("isDeathZone") if region.get("isDeathZone") is not None else region.get("is_death_zone", False)
            seen_ids.add(region_id)
            detected_list.append({
                "id": region_id,
                "name": region_name,
                "terrain": terrain,
                "is_death_zone": is_death_zone,
                "is_visible": True
            })
        elif isinstance(region, str):
            seen_ids.add(region)
            detected_list.append({
                "id": region,
                "name": region[:8],
                "terrain": "unknown",
                "is_death_zone": False,
                "is_visible": False
            })
            
    # 2. Fallback: baca koneksi fisik jika bot buta (misal: di dalam Cave)
    for region_id in connections:
        if region_id not in seen_ids:
            detected_list.append({
                "id": region_id,
                "name": region_id[:8],
                "terrain": "unknown",
                "is_death_zone": False,
                "is_visible": False
            })
            
    return detected_list