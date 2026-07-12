def get_survival_decision(view_data, agent_info, enemy_detector, deadzone_detector):
    view = view_data
    self_data = view.get("self", {}) or {}
    hp = self_data.get("hp", 0)
    my_def = self_data.get("def", 5)

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
    max_incoming_damage = 0

    for agent in local_agents:
        a_name = agent.get("name", "").lower()
        if "guardian" in a_name:
            if agent.get("alertActive", False):
                has_guardian = True
        else:
            has_active_threats = True
            atk = agent.get("atk", 25)
            damage = max(1, atk - my_def)
            if damage > max_incoming_damage:
                max_incoming_damage = damage

    for monster in local_monsters:
        m_type = monster.get("type", "").lower() or monster.get("name", "").lower()
        if "guardian" in m_type:
            if monster.get("alertActive", False):
                has_guardian = True
        else:
            has_active_threats = True
            atk = monster.get("atk", 15)
            damage = max(1, atk - my_def)
            if damage > max_incoming_damage:
                max_incoming_damage = damage

    if is_deadzone:
        return {"is_danger": True, "reason": "deadzone"}

    if has_guardian:
        return {"is_danger": True, "reason": "guardian_present"}

    if hp <= 35 and has_active_threats:
        return {"is_danger": True, "reason": "critical_hp_under_attack"}

    if has_active_threats and max_incoming_damage >= hp:
        return {"is_danger": True, "reason": "one_shot_threat_detected"}

    return {"is_danger": False}