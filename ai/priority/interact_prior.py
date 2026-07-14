def score_interactables(interactables, hp, ep, interacted_ids):
    if ep < 1 or not interactables:
        return {
            "score": 0,
            "action": None
        }

    scored_actions = []
    for inter in interactables:
        if not isinstance(inter, dict):
            continue

        t_id = inter.get("id") or inter.get("targetId") or inter.get("facilityId")
        f_type = inter.get("type") or inter.get("name") or inter.get("id") or ""
        name_clean = f_type.lower().replace(" ", "_")

        # Batasi semua fasilitas (termasuk Medical Facility) hanya boleh diinteraksi SEKALI saja
        if t_id and t_id in interacted_ids:
            continue

        score = 0
        if name_clean == "medical_facility":
            if hp < 100:
                score = 180 + (100 - hp)
                if hp < 40:
                    score += 150
                elif hp < 60:
                    score += 50
        elif name_clean == "supply_cache":
            score = 170

        if score > 0:
            scored_actions.append((score, {
                "action": "interact",
                "target": inter
            }))

    if not scored_actions:
        return {
            "score": 0,
            "action": None
        }

    scored_actions.sort(key=lambda x: x[0], reverse=True)
    best_score, best_action = scored_actions[0]

    return {
        "score": best_score,
        "action": best_action
    }