def score_interactables(interactables, hp, ep, interacted_ids):
    best_action = None
    best_score = 0
    
    if ep < 1:
        return {
            "score": 0,
            "action": None
        }
        
    for inter in interactables:
        if not isinstance(inter, dict):
            continue
        f_type = inter.get("type") or inter.get("name") or inter.get("id")
        if not f_type:
            continue
            
        name_clean = str(f_type).lower().replace(" ", "_")
        t_id = inter.get("id") or inter.get("targetId") or inter.get("facilityId")
        
        if t_id and t_id in interacted_ids:
            continue
            
        if name_clean == "medical_facility":
            if hp < 100:
                score = 80 + (100 - hp)
                if score > best_score:
                    best_score = score
                    best_action = {"action": "interact", "target": inter}
        elif name_clean == "supply_cache":
            score = 75
            if score > best_score:
                best_score = score
                best_action = {"action": "interact", "target": inter}
                
    return {
        "score": best_score,
        "action": best_action
    }