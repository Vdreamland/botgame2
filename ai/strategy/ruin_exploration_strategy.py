def score_exploration(regions, alert_gauge, ep):
    if ep < 1 or not regions:
        return {
            "score": 0,
            "action": None
        }
        
    current_region = regions[0]
    r_name = str(current_region.get("name", "")).lower()
    is_ruin = "relic" in r_name or "ruin" in r_name or "pack" in r_name
    
    if is_ruin:
        is_empty = current_region.get("isEmpty", False) or current_region.get("is_empty", False)
        if not is_empty and alert_gauge < 10:
            score = min(65, max(0, 65 - alert_gauge * 2))
            return {
                "score": score,
                "action": {
                    "action": "explore",
                    "target": current_region
                }
            }
            
    return {
        "score": 0,
        "action": None
    }