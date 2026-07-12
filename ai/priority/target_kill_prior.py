from src.helper.game_helper import normalize_item_name, get_region_distances, resolve_equipped

WEAPON_RANGES = {
    "fist": 0,
    "knife": 0,
    "dagger": 0,
    "sword": 0,
    "katana": 0,
    "bow": 1,
    "pistol": 1,
    "sniper": 2
}

def get_target_decision(view_data, agent_info, enemy_detector):
    view = view_data
    current_region_id = view.get("currentRegion", {}).get("id")
    
    inventory = agent_info.get_inventory()
    resolved = resolve_equipped(view_data, inventory)
    eq_weapon_name = resolved.get("weapon_name")
    eq_weapon_norm = normalize_item_name(eq_weapon_name)
    weapon_range = WEAPON_RANGES.get(eq_weapon_norm, 1)

    region_distances = get_region_distances(view_data)

    self_data = view.get("self", {}) or {}
    agent_ep = self_data.get("ep", 0)

    available_actions = view.get("availableActions", {}) or {}
    attack_action = available_actions.get("attack", {}) or {}
    attack_cost = attack_action.get("cost")
    if attack_cost is None:
        from src.helper.game_helper import WEAPONS
        weapon_data = WEAPONS.get(eq_weapon_norm, {})
        attack_cost = weapon_data.get("ep", 2)

    if agent_ep < attack_cost:
        return None

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
            if not eq_weapon_name:
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