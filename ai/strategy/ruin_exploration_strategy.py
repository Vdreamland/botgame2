def score_exploration(regions, alert_gauge, ep):
    best_ruin = None
    best_score = 0
    
    if ep < 1:
        return {
            "score": 0,
            "action": None
        }
        
    for r in regions:
        if not isinstance(r, dict):
            continue
        ruins = r.get("ruins")
        if not ruins and ("relic" in str(r.get("name", "")).lower() or "ruin" in str(r.get("name", "")).lower()):
            ruins = {"id": r.get("id"), "status": "unknown"}
            
        if ruins:
            status = str(ruins.get("status", "")).lower()
            if status not in ("cleared", "completed", "finished"):
                if alert_gauge < 10:
                    score = 175 - alert_gauge
                    if score > best_score:
                        best_score = score
                        best_ruin = ruins
                        
    return {
        "score": best_score,
        "action": {"action": "explore", "target": best_ruin} if best_ruin else None
    }