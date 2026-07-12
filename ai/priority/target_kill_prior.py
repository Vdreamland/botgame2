def get_target_decision(view_data, agent_info, enemy_detector):
    view = view_data.get("view", {}) or {}
    current_region_id = view.get("currentRegion", {}).get("id")
    equipped = agent_info.get_equipped(view_data)
    eq_weapon = equipped.get("weapon")

    enemies = enemy_detector.detect_enemies(view_data)
    local_enemies = [e for e in enemies if e.get("zone") == current_region_id]
    combat_targets = [e for e in local_enemies if e.get("type") != "guardian"]

    best_target = None
    best_score = -99999

    for target in combat_targets:
        t_id = target.get("id")
        t_type = target.get("type")
        t_hp = target.get("hp", 0)

        score = 1000

        if t_type == "monster":
            score += 500
            score += (40 - t_hp)
        elif t_type == "agent":
            if t_hp < 30:
                score += 300
            if not eq_weapon:
                score -= 800
            score -= t_hp

        if score > best_score:
            best_score = score
            best_target = target

    if best_target and best_score > 0:
        return {
            "action": "attack",
            "target_id": best_target.get("id"),
            "target_type": best_target.get("type")
        }

    return None