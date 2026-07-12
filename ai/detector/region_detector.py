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
        
        # Mencegah duplikasi nama candi (S:Relic / S:Pack) agar tidak saling menimpa
        if region_name in ("S:Relic", "S:Pack") or region_name.startswith("S:"):
            region_name = f"{region_name} ({r_id[:8]})"
            
        item_counts = {}
        
        # Jenis 2: Deteksi Fasilitas Petak
        facility_raw = r.get("facility") or r.get("facilities") or r.get("facilityType") or r.get("facility_type")
        facility_list = []
        if isinstance(facility_raw, list):
            facility_list = facility_raw
        elif facility_raw:
            facility_list = [facility_raw]
            
        for f_data in facility_list:
            f_name = None
            if isinstance(f_data, str):
                f_name = f_data
            elif isinstance(f_data, dict):
                f_name = f_data.get("name") or f_data.get("type") or f_data.get("typeId") or f_data.get("facilityType")
                
            if f_name:
                facility_clean = f_name.replace("_", " ").strip()
                item_counts[facility_clean] = item_counts.get(facility_clean, 0) + 1
                
        # Deteksi fasilitas dari array "interactables"
        interactables = r.get("interactables") or []
        if isinstance(interactables, list):
            for interactable in interactables:
                if isinstance(interactable, dict):
                    f_name = (interactable.get("facility") or 
                              interactable.get("type") or 
                              interactable.get("typeId") or 
                              interactable.get("name"))
                    is_used = (interactable.get("isUsed") 
                               if interactable.get("isUsed") is not None 
                               else interactable.get("is_used", False))
                    
                    if f_name:
                        facility_clean = f_name.replace("_", " ").strip()
                        if is_used:
                            facility_clean = f"{facility_clean} (used)"
                        # Hindari duplikasi jika sudah terdaftar
                        if facility_clean not in item_counts:
                            item_counts[facility_clean] = item_counts.get(facility_clean, 0) + 1
            
        # Jenis 1: Deteksi Item Fisik
        items_list = r.get("items") or []
        for item in items_list:
            if isinstance(item, dict):
                item_name = item.get("name") or item.get("typeId") or "item"
                item_name = item_name.strip()
                item_counts[item_name] = item_counts.get(item_name, 0) + 1
                
        # Konversi hasil hitungan ke format penamaan terkelompok
        detected_items = []
        for name, count in item_counts.items():
            if count > 1:
                detected_items.append(f"{name} [{count}]")
            else:
                detected_items.append(name)
                
        if detected_items:
            region_contents[region_name] = detected_items
            
    return region_contents


def detect_region_enemies(view: Dict[str, Any]) -> Dict[str, List[str]]:
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
            
    region_enemies = {}
    my_id = view.get("self", {}).get("id") or view.get("player", {}).get("id")
    
    for r_id, r in regions_map.items():
        region_name = r.get("name") or f"Region ({r_id[:8]})"
        
        # Mencegah duplikasi penamaan candi
        if region_name in ("S:Relic", "S:Pack") or region_name.startswith("S:"):
            region_name = f"{region_name} ({r_id[:8]})"
            
        enemies = []
        
        # 1. Deteksi Player/Agent Lain (Hanya yang masih hidup)
        agents_list = r.get("agents") or r.get("players") or []
        for agent in agents_list:
            if isinstance(agent, dict):
                agent_id = agent.get("id")
                # Abaikan bot kita sendiri agar tidak masuk dalam daftar musuh
                if agent_id == my_id:
                    continue
                    
                agent_name = agent.get("name") or "Player"
                agent_hp = agent.get("hp")
                is_alive = agent.get("isAlive") if agent.get("isAlive") is not None else agent.get("is_alive", True)
                
                if is_alive:
                    if agent_hp is not None:
                        enemies.append(f"{agent_name} [HP {agent_hp}]")
                    else:
                        enemies.append(agent_name)
        
        # 2. Deteksi Monster & Guardians (Hanya yang masih hidup)
        monsters_list = r.get("monsters") or []
        guardians_list = r.get("guardians") or []
        combined_monsters = list(monsters_list)
        for g in guardians_list:
            if g not in combined_monsters:
                combined_monsters.append(g)
                
        for monster in combined_monsters:
            if isinstance(monster, dict):
                m_name = monster.get("name") or monster.get("typeId") or "Monster"
                # Rapikan visualisasi nama monster (e.g. azure_tiger -> Azure Tiger)
                m_name = m_name.replace("_", " ").title()
                m_hp = monster.get("hp")
                is_alive = monster.get("isAlive") if monster.get("isAlive") is not None else monster.get("is_alive", True)
                
                if is_alive:
                    if m_hp is not None:
                        enemies.append(f"{m_name} [HP {m_hp}]")
                    else:
                        enemies.append(m_name)
                        
        if enemies:
            region_enemies[region_name] = enemies
            
    return region_enemies