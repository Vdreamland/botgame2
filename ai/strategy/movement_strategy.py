from ai.priority.region_loot_prior import is_item_needed

def score_region_movement(region, is_death_zone_pending, hp, is_safe):
    score = 100
    
    is_dead_zone = region.get("is_death_zone") or region.get("isDeathZone") or False
    if is_dead_zone:
        score -= 2000
        
    if is_death_zone_pending:
        score -= 1000
        
    if hp < 40 and not is_safe:
        terrain = str(region.get("terrain", "")).lower()
        if terrain == "cave":
            score += 40
        else:
            score += 20
            
    return score

def get_best_movement_action(connected_regions, visible_regions, pending_deathzones, hp, ep, is_safe, inventory, current_weapon, current_armor, interacted_ids, current_region):
    if ep < 2 or not connected_regions:
        return None
        
    current_id = current_region.get("id")
    is_in_dead_zone = current_region.get("is_death_zone") or current_region.get("isDeathZone") or False
    is_in_pending = current_id in pending_deathzones if current_id else False
    is_urgent = is_in_dead_zone or is_in_pending or (hp < 40 and not is_safe)
    
    visible_regions_map = {}
    for r in visible_regions:
        if isinstance(r, dict):
            r_id = r.get("id")
            if r_id:
                visible_regions_map[r_id] = r
                
    scored_regions = []
    for r in connected_regions:
        r_id = r.get("id") if isinstance(r, dict) else r
        is_pending_dead = r_id in pending_deathzones if r_id else False
        
        score = score_region_movement(r, is_pending_dead, hp, is_safe)
        
        if ep < 3 and not is_urgent:
            score -= 1500
            
        region_detail = visible_regions_map.get(r_id) if r_id else None
        
        has_ruin = False
        r_name_lower = str(r.get("name", "")).lower()
        if "relic" in r_name_lower or "ruin" in r_name_lower or (region_detail and region_detail.get("ruins")):
            ruin_obj = r.get("ruins") or (region_detail.get("ruins") if region_detail else None)
            if not ruin_obj or str(ruin_obj.get("status", "")).lower() not in ("cleared", "completed", "finished"):
                has_ruin = True
                
        if has_ruin:
            score += 95
            
        if region_detail:
            items_in_region = region_detail.get("items", []) or region_detail.get("groundItems", []) or []
            has_needed_item = False
            for item in items_in_region:
                if isinstance(item, dict):
                    item_name = item.get("name") or item.get("type") or item.get("typeId")
                    if item_name and is_item_needed(item_name, inventory, current_weapon, current_armor):
                        has_needed_item = True
                        break
            if has_needed_item:
                score += 20
                
            interactables = region_detail.get("interactables", []) or []
            for inter in interactables:
                if isinstance(inter, dict):
                    f_type = inter.get("type") or inter.get("name") or inter.get("id")
                    if f_type:
                        name_clean = f_type.lower().replace(" ", "_")
                        t_id = inter.get("id") or inter.get("targetId") or inter.get("facilityId")
                        if t_id and t_id in interacted_ids:
                            continue
                        if name_clean == "medical_facility" and hp < 100:
                            score += 30
                        elif name_clean == "supply_cache":
                            score += 25
                            
        scored_regions.append((score, r))
        
    if not scored_regions:
        return None
        
    scored_regions.sort(key=lambda x: x[0], reverse=True)
    best_score, best_region = scored_regions[0]
    
    return {
        "score": best_score,
        "action": {"action": "move", "target": best_region}
    }