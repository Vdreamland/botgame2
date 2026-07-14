def score_exploration(regions, alert_gauge, ep):
    if ep < 1 or not regions:
        return {
            "score": 0,
            "action": None
        }
        
    current_region = regions[0]
    ruins = current_region.get("ruins")
    
    if ruins:
        status = str(ruins.get("status", "")).lower()
        if status not in ("cleared", "completed", "finished") and alert_gauge < 10:
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