WEAPON_RANGES = {
    "fist": 1,
    "knife": 1,
    "dagger": 1,
    "sword": 1,
    "katana": 1,
    "bow": 2,
    "pistol": 2,
    "sniper": 3
}

def normalize_item_name(name):
    if not name:
        return ""
    norm = name.lower().replace(" ", "_")
    if "sniper" in norm:
        return "sniper"
    return norm

def get_region_distances(view_data):
    view = view_data
    current_region = view.get("currentRegion", {}) or {}
    start_id = current_region.get("id")
    if not start_id:
        return {}

    visible_regions = view.get("visibleRegions", []) or []
    regions = {start_id: current_region}
    for r in visible_regions:
        r_id = r.get("id")
        if r_id:
            regions[r_id] = r

    queue = [(start_id, 0)]
    visited = {start_id: 0}

    while queue:
        curr_id, d = queue.pop(0)
        curr_reg = regions.get(curr_id, {})
        conns = curr_reg.get("connections") or curr_reg.get("links") or []
        for neighbor_id in conns:
            if neighbor_id in regions and neighbor_id not in visited:
                visited[neighbor_id] = d + 1
                queue.append((neighbor_id, d + 1))
    return visited

def get_target_decision(view_data, agent_info, enemy_detector):
    view = view_data
    current_region_id = view.get("currentRegion", {}).get("id")
    equipped = agent_info.get_equipped()
    eq_weapon = equipped.get("weapon")

    eq_weapon_name = eq_weapon.get("name") if isinstance(eq_weapon, dict) else eq_weapon
    eq_weapon_norm = normalize_item_name(eq_weapon_name)
    weapon_range = WEAPON_RANGES.get(eq_weapon_norm, 1)

    region_distances = get_region_distances(view_data)

    combat_targets = []

    for agent in enemy_detector.get_alive_agents():
        if "guardian" not in agent.get("name", "").lower():
            t_zone = agent.get("zone") or agent.get("regionId") or agent.get("region")
            dist = region_distances.get(t_zone, 999)
            if dist <= weapon_range:
                combat_targets.append({
                    "id": agent.get("id"),
                    "name": agent.get("name"),
                    "hp": agent.get("hp", 0),
                    "type": "agent",
                    "dist": dist
                })

    for monster in enemy_detector.get_alive_monsters():
        m_type = monster.get("type", "").lower() or monster.get("name", "").lower()
        if "guardian" not in m_type:
            t_zone = monster.get("zone") or monster.get("regionId") or monster.get("region")
            dist = region_distances.get(t_zone, 999)
            if dist <= weapon_range:
                combat_targets.append({
                    "id": monster.get("id"),
                    "name": monster.get("name"),
                    "hp": monster.get("hp", 0),
                    "type": "monster",
                    "dist": dist
                })

    best_target = None
    best_score = -99999

    for target in combat_targets:
        t_id = target.get("id")
        t_type = target.get("type")
        t_hp = target.get("hp", 0)
        t_dist = target.get("dist", 1)

        score = 1000

        if t_type == "monster":
            score += 500
            score += (40 - t_hp)
            if t_dist > 1:
                score -= 100
        elif t_type == "agent":
            if t_hp < 30:
                score += 300
            if not eq_weapon:
                score -= 800
            score -= t_hp
            if t_dist > 1:
                score += 50

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