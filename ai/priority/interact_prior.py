def score_interactables(interactables, hp, ep):
    best_action = None
    best_score = 0
    
    for inter in interactables:
        if not isinstance(inter, dict):
            continue
        f_type = inter.get("type") or inter.get("id")
        if not f_type:
            continue
            
        name_clean = str(f_type).lower()
        if "ruins" in name_clean or "candi" in name_clean:
            score = 30
            if score > best_score:
                best_score = score
                best_action = {"action": "interact", "target": inter}
                
    return {
        "score": best_score,
        "action": best_action
    }