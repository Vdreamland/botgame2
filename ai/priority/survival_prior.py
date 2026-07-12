def get_survival_decision(view_data, agent_info, enemy_detector, deadzone_detector):
    view = view_data.get("view", {}) or {}
    self_data = view.get("self", {}) or {}
    hp = self_data.get("hp", 0)

    is_deadzone = deadzone_detector.is_in_dead_zone(view_data)

    current_region_id = view.get("currentRegion", {}).get("id")
    enemies = enemy_detector.detect_enemies(view_data)
    local_enemies = [e for e in enemies if e.get("zone") == current_region_id]

    has_guardian = any(e.get("type") == "guardian" for e in local_enemies)
    has_active_threats = any(e.get("type") in ("agent", "monster") for e in local_enemies)

    if is_deadzone:
        return {"is_danger": True, "reason": "deadzone"}

    if has_guardian:
        return {"is_danger": True, "reason": "guardian_present"}

    if hp <= 35 and has_active_threats:
        return {"is_danger": True, "reason": "critical_hp_under_attack"}

    return {"is_danger": False}