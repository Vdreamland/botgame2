def get_target_decision(view_data, agent_info, enemy_detector):
    view = view_data
    current_region_id = view.get("currentRegion", {}).get("id")
    equipped = agent_info.get_equipped()
    eq_weapon = equipped.get("weapon")

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

    combat_targets = []

    for agent in local_agents:
        if "guardian" not in agent.get("name", "").lower():
            combat_targets.append({
                "id": agent.get("id"),
                "name": agent.get("name"),
                "hp": agent.get("hp", 0),
                "type": "agent"
            })

    for monster in local_monsters:
        m_type = monster.get("type", "").lower() or monster.get("name", "").lower()
        if "guardian" not in m_type:
            combat_targets.append({
                "id": monster.get("id"),
                "name": monster.get("name"),
                "hp": monster.get("hp", 0),
                "type": "monster"
            })

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