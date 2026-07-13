def score_region_movement(region, is_death_zone_pending, hp, is_safe):
    score = 100
    
    is_dead_zone = region.get("is_death_zone") or region.get("isDeathZone") or False
    if is_dead_zone:
        score -= 90
        
    if is_death_zone_pending:
        score -= 50
        
    if hp < 40 and not is_safe:
        terrain = str(region.get("terrain", "")).lower()
        if terrain == "cave":
            score += 40
        else:
            score += 20
            
    return score

def get_best_movement_action(connected_regions, pending_deathzones, hp, ep, is_safe):
    if ep < 2 or not connected_regions:
        return None
        
    scored_regions = []
    for r in connected_regions:
        r_id = r.get("id")
        is_pending_dead = r_id in pending_deathzones if r_id else False
        
        score = score_region_movement(r, is_pending_dead, hp, is_safe)
        scored_regions.append((score, r))
        
    if not scored_regions:
        return None
        
    scored_regions.sort(key=lambda x: x[0], reverse=True)
    best_score, best_region = scored_regions[0]
    
    return {
        "score": best_score,
        "action": {"action": "move", "target": best_region}
    }