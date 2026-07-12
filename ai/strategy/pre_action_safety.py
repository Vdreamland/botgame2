def is_action_safe(view_data, action, agent_info, enemy_detector):
    view = view_data
    self_data = view.get("self", {}) or {}
    hp = self_data.get("hp", 0)

    current_region = view.get("currentRegion", {}) or {}
    current_region_id = current_region.get("id")

    action_type = action.get("action")
    data = action.get("data", {}) or {}

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

    has_local_threat = False
    for agent in local_agents:
        a_name = agent.get("name", "").lower()
        if "guardian" in a_name:
            if agent.get("alertActive", False):
                has_local_threat = True
        else:
            has_local_threat = True
    for monster in local_monsters:
        m_type = monster.get("type", "").lower() or monster.get("name", "").lower()
        if "guardian" in m_type:
            if monster.get("alertActive", False):
                has_local_threat = True
        else:
            has_local_threat = True

    if action_type == "interact":
        if has_local_threat:
            return False

    elif action_type == "pickup":
        if has_local_threat:
            item_id = data.get("itemId")
            ground_items = current_region.get("items", []) or []
            item_name = ""
            for item in ground_items:
                if isinstance(item, dict) and item.get("id") == item_id:
                    item_name = item.get("name", "").lower()
                    break
            if item_name != "smoltz" and "katana" not in item_name and "sniper" not in item_name:
                return False

    elif action_type == "move":
        dest_id = data.get("regionId")
        if dest_id:
            visible_regions = view.get("visibleRegions", []) or []
            dest_reg = next((r for r in visible_regions if r.get("id") == dest_id), None)
            if dest_reg:
                is_death = dest_reg.get("isDeathZone") or dest_reg.get("isDeadZone") or False
                if is_death:
                    return False

                dest_monsters = dest_reg.get("monsters", []) or []
                dest_agents = dest_reg.get("agents", []) or []

                has_dest_guardian = False
                for m in dest_monsters:
                    m_type = m.get("type", "").lower() or m.get("name", "").lower()
                    if "guardian" in m_type:
                        if m.get("alertActive", False):
                            has_dest_guardian = True
                            break
                for a in dest_agents:
                    if "guardian" in a.get("name", "").lower():
                        if a.get("alertActive", False):
                            has_dest_guardian = True
                            break

                if has_dest_guardian:
                    return False

                equipped = agent_info.get_equipped()
                eq_weapon = equipped.get("weapon")

                if not has_local_threat:
                    if len(dest_agents) >= 2:
                        return False
                    if not eq_weapon and dest_agents:
                        return False
                    if hp <= 50 and dest_agents:
                        return False

    return True