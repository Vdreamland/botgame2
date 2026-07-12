def get_survival_decision(view_data, agent_info, enemy_detector, deadzone_detector):
    view = view_data.get("view", {}) or {}
    self_data = view.get("self", {}) or {}
    hp = self_data.get("hp", 0)

    current_region = view.get("currentRegion", {}) or {}
    dead_status = deadzone_detector.get_region_status(current_region)
    is_deadzone = (dead_status == "DeadZone")

    current_region_id = current_region.get("id")
    local_agents = []
    for agent in enemy_detector.get_alive_agents():
        r_id = agent.get("regionId") or agent.get("region")
        if r_id == current_region_id:
            local_agents.append(agent)

    local_monsters = []
    for monster in enemy_detector.get_alive_monsters():
        r_id = monster.get("regionId") or monster.get("region")
        if r_id == current_region_id:
            local_monsters.append(monster)

    has_guardian = False
    has_active_threats = False

    for agent in local_agents:
        if "guardian" in agent.get("name", "").lower():
            has_guardian = True
        else:
            has_active_threats = True

    for monster in local_monsters:
        m_type = monster.get("type", "").lower() or monster.get("name", "").lower()
        if "guardian" in m_type:
            has_guardian = True
        else:
            has_active_threats = True

    if is_deadzone:
        return {"is_danger": True, "reason": "deadzone"}

    if has_guardian:
        return {"is_danger": True, "reason": "guardian_present"}

    if hp <= 35 and has_active_threats:
        return {"is_danger": True, "reason": "critical_hp_under_attack"}

    return {"is_danger": False}