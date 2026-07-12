from typing import Dict, Any, List

def detect_connected_regions(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    current_region = view.get("currentRegion") or view.get("current_region") or {}
    connections = current_region.get("connections") or []
    
    # Ambil seluruh petak peta yang terlihat di luar kabut dari server
    visible_regions_source = view.get("regions") or view.get("visibleRegions") or view.get("visible_regions") or {}
    
    visible_regions_map = {}
    if isinstance(visible_regions_source, list):
        for r in visible_regions_source:
            if isinstance(r, dict) and r.get("id"):
                visible_regions_map[r["id"]] = r
    elif isinstance(visible_regions_source, dict):
        visible_regions_map = visible_regions_source

    connected_source = view.get("connectedRegions") or view.get("connected_regions") or []
    for r in connected_source:
        if isinstance(r, dict) and r.get("id"):
            visible_regions_map[r["id"]] = r

    detected_list = []
    seen_ids = set()

    # 1. Proses jalur terdekat (Adjacent Connections) terlebih dahulu
    for region_id in connections:
        seen_ids.add(region_id)
        r_detail = visible_regions_map.get(region_id)
        if isinstance(r_detail, dict):
            region_name = r_detail.get("name") or region_id[:8]
            terrain = r_detail.get("terrain") or "unknown"
            is_death_zone = r_detail.get("isDeathZone") if r_detail.get("isDeathZone") is not None else r_detail.get("is_death_zone", False)
            detected_list.append({
                "id": region_id,
                "name": region_name,
                "terrain": terrain,
                "is_death_zone": is_death_zone,
                "is_visible": True
            })
        else:
            detected_list.append({
                "id": region_id,
                "name": region_id[:8],
                "terrain": "unknown",
                "is_death_zone": False,
                "is_visible": False
            })

    # 2. Proses petak terang lainnya yang ada di dalam jangkauan pandangan bot Anda (Ruins, Court, Theater, dll.)
    for r_id, r_detail in visible_regions_map.items():
        if r_id not in seen_ids and isinstance(r_detail, dict):
            region_name = r_detail.get("name") or r_id[:8]
            terrain = r_detail.get("terrain") or "unknown"
            is_death_zone = r_detail.get("isDeathZone") if r_detail.get("isDeathZone") is not None else r_detail.get("is_death_zone", False)
            detected_list.append({
                "id": r_id,
                "name": region_name,
                "terrain": terrain,
                "is_death_zone": is_death_zone,
                "is_visible": True
            })

    return detected_list