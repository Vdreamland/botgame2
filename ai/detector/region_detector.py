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

    # 1. Daftarkan petak tempat berdiri bot saat ini di urutan paling depan
    current_id = current_region.get("id")
    if current_id:
        region_name = current_region.get("name") or current_id[:8]
        terrain = current_region.get("terrain") or "unknown"
        is_death_zone = current_region.get("isDeathZone") if current_region.get("isDeathZone") is not None else current_region.get("is_death_zone", False)
        seen_ids.add(current_id)
        detected_list.append({
            "id": current_id,
            "name": region_name,
            "terrain": terrain,
            "is_death_zone": is_death_zone,
            "is_visible": True
        })

    # 2. Proses jalur terdekat (Adjacent Connections)
    for region_id in connections:
        if region_id not in seen_ids:
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

    # 3. Proses petak terang lainnya yang ada di dalam jangkauan pandangan bot Anda (Ruins, Court, dll)
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


def detect_region_items(view: Dict[str, Any]) -> Dict[str, List[str]]:
    current_region = view.get("currentRegion") or view.get("current_region") or {}
    visible_regions_source = view.get("regions") or view.get("visibleRegions") or view.get("visible_regions") or {}
    connected_source = view.get("connectedRegions") or view.get("connected_regions") or []
    
    regions_map = {}
    
    if isinstance(current_region, dict) and current_region.get("id"):
        regions_map[current_region["id"]] = current_region
        
    if isinstance(visible_regions_source, list):
        for r in visible_regions_source:
            if isinstance(r, dict) and r.get("id"):
                regions_map[r["id"]] = r
    elif isinstance(visible_regions_source, dict):
        for r_id, r in visible_regions_source.items():
            if isinstance(r, dict):
                regions_map[r_id] = r
                
    for r in connected_source:
        if isinstance(r, dict) and r.get("id"):
            regions_map[r["id"]] = r
            
    region_contents = {}
    
    for r_id, r in regions_map.items():
        region_name = r.get("name") or f"Region ({r_id[:8]})"
        item_counts = {}
        
        # Jenis 2: Deteksi Fasilitas Petak (Dibuat toleran terhadap tipe data string maupun dict)
        facility_data = r.get("facility")
        facility = None
        if isinstance(facility_data, str):
            facility = facility_data
        elif isinstance(facility_data, dict):
            facility = facility_data.get("name") or facility_data.get("type") or facility_data.get("typeId")
            
        if facility:
            facility_clean = facility.replace("_", " ")
            item_counts[facility_clean] = item_counts.get(facility_clean, 0) + 1
            
        # Jenis 1: Deteksi Item Fisik (Weapon, Armor, Recovery, Binoculars/Utility)
        items_list = r.get("items") or []
        for item in items_list:
            if isinstance(item, dict):
                item_name = item.get("name") or item.get("typeId") or "item"
                item_name = item_name.strip()
                item_counts[item_name] = item_counts.get(item_name, 0) + 1
                
        # Konversi hasil hitungan ke format penamaan terkelompok, misal: Bandage [3]
        detected_items = []
        for name, count in item_counts.items():
            if count > 1:
                detected_items.append(f"{name} [{count}]")
            else:
                detected_items.append(name)
                
        if detected_items:
            region_contents[region_name] = detected_items
            
    return region_contents