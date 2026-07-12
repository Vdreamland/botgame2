import asyncio
from src.helper import actions_helper
import ai.priority as priority
import ai.strategy as strategy

def get_decision(view_data, agent_info, enemy_detector, deadzone_detector, ground_detector, memory):
    view = view_data.get("view", {}) or {}
    self_data = view.get("self", {}) or {}
    ep = self_data.get("ep", 0)

    visible_regions = view.get("visibleRegions", []) or []
    current_region = view.get("currentRegion", {}) or {}
    current_region_id = current_region.get("id")

    region_names = {r.get("id"): r.get("name") for r in visible_regions if r.get("id")}
    if current_region_id:
        region_names[current_region_id] = current_region.get("name")

    survival = priority.get_survival_decision(view_data, agent_info, enemy_detector, deadzone_detector)
    if survival and survival.get("is_danger"):
        rec_dec = priority.get_recovery_decision(view_data, agent_info)
        if rec_dec and rec_dec.get("action") == "use":
            inventory = agent_info.get_inventory(view_data)
            item_name = "consumable"
            for it in inventory:
                if isinstance(it, dict) and it.get("id") == rec_dec.get("item_id"):
                    item_name = it.get("name")
                    break
            thought = f"HP critical under danger! Using recovery: {item_name}"
            return actions_helper.use_item(rec_dec.get("item_id"), thought)

        connections = current_region.get("connections") or current_region.get("links") or []
        safe_escape_region = None
        for r_id in connections:
            r_data = next((r for r in visible_regions if r.get("id") == r_id), None)
            if r_data:
                is_death = r_data.get("isDeathZone") or r_data.get("isDeadZone") or False
                if not is_death:
                    safe_escape_region = r_id
                    break

        if safe_escape_region:
            dest_name = region_names.get(safe_escape_region, "Unknown")
            thought = f"Danger detected! Escaping immediately to {dest_name}"
            return actions_helper.move_to(safe_escape_region, thought)

    equip_dec = priority.get_equipment_decision(view_data, agent_info)
    if equip_dec:
        act = equip_dec.get("action")
        item_id = equip_dec.get("item_id")
        inventory = agent_info.get_inventory(view_data)
        item_name = "item"
        for it in inventory:
            if isinstance(it, dict) and it.get("id") == item_id:
                item_name = it.get("name")
                break
        if act == "equip":
            thought = f"Equipping better weapon/armor: {item_name}"
            return actions_helper.equip_item(item_id, thought)
        elif act == "drop":
            thought = f"Dropping redundant equipment: {item_name}"
            return actions_helper.drop_item(item_id, thought)

    loot_dec = priority.get_loot_decision(view_data, agent_info, ground_detector)
    if loot_dec:
        item_id = loot_dec.get("item_id")
        ground_items = ground_detector.detect_ground_items(view_data)
        item_name = "item"
        for it in ground_items:
            if isinstance(it, dict) and it.get("id") == item_id:
                item_name = it.get("name")
                break
        thought = f"Looting {item_name} from ground"
        return actions_helper.pickup_item(item_id, thought)

    rec_dec = priority.get_recovery_decision(view_data, agent_info)
    if rec_dec:
        act = rec_dec.get("action")
        item_id = rec_dec.get("item_id")
        inventory = agent_info.get_inventory(view_data)
        item_name = "consumable"
        for it in inventory:
            if isinstance(it, dict) and it.get("id") == item_id:
                item_name = it.get("name")
                break
        if act == "use":
            thought = f"Activating recovery: {item_name}"
            return actions_helper.use_item(item_id, thought)
        elif act == "drop":
            thought = f"Dropping excess consumable: {item_name}"
            return actions_helper.drop_item(item_id, thought)

    target_dec = priority.get_target_decision(view_data, agent_info, enemy_detector)
    if target_dec:
        target_id = target_dec.get("target_id")
        target_type = target_dec.get("target_type")
        enemies = enemy_detector.get_alive_agents() + enemy_detector.get_alive_monsters()
        target_name = "Enemy"
        for e in enemies:
            if isinstance(e, dict) and e.get("id") == target_id:
                target_name = e.get("name")
                break
        thought = f"Attacking {target_name} ({target_type})"
        memory.set_target(target_id)
        return actions_helper.attack_target(target_id, target_type, thought)

    committed_id = memory.get_target()
    if committed_id:
        enemies = enemy_detector.get_alive_agents() + enemy_detector.get_alive_monsters()
        target_info = next((e for e in enemies if e.get("id") == committed_id), None)
        if not target_info or target_info.get("hp", 0) <= 0:
            memory.clear_target()
        else:
            target_zone = target_info.get("zone") or target_info.get("regionId") or target_info.get("region")
            if target_zone != current_region_id:
                if ep >= 3:
                    target_reg = next((r for r in visible_regions if r.get("id") == target_zone), None)
                    if target_reg:
                        is_death = target_reg.get("isDeathZone") or target_reg.get("isDeadZone") or False
                        if not is_death:
                            step = strategy.get_next_step(view_data, target_zone)
                            if step:
                                dest_name = region_names.get(step, "Unknown")
                                thought = f"Chasing target! Moving to {dest_name}"
                                return actions_helper.move_to(step, thought)

    interact_dec = priority.get_interact_decision(view_data, agent_info)
    if interact_dec:
        act_type = interact_dec.get("action")
        if act_type == "explore":
            thought = f"Exploring ruin at {region_names.get(current_region_id, 'current region')}"
            return actions_helper.explore_ruin(thought)
        elif act_type == "interact":
            fac_id = interact_dec.get("interactable_id")
            interactables = current_region.get("interactables", []) or []
            fac_type = "facility"
            for fac in interactables:
                if isinstance(fac, dict) and fac.get("id") == fac_id:
                    fac_type = fac.get("type")
                    break
            thought = f"Interacting with {fac_type}"
            return actions_helper.interact_facility(fac_id, thought)

    best_ruin_id = strategy.get_best_ruin_target(view_data)
    if best_ruin_id:
        step = strategy.get_next_step(view_data, best_ruin_id)
        if step:
            dest_name = region_names.get(step, "Unknown")
            target_name = region_names.get(best_ruin_id, "Unknown")
            thought = f"Navigating to ruin: {target_name}. Moving to {dest_name}"
            return actions_helper.move_to(step, thought)

    connections = current_region.get("connections") or current_region.get("links") or []
    best_roam_id = None
    for r_id in connections:
        r_data = next((r for r in visible_regions if r.get("id") == r_id), None)
        if r_data:
            is_death = r_data.get("isDeathZone") or r_data.get("isDeadZone") or False
            if not is_death:
                if not memory.is_region_visited(r_id):
                    best_roam_id = r_id
                    break
                if best_roam_id is None:
                    best_roam_id = r_id

    if best_roam_id:
        dest_name = region_names.get(best_roam_id, "Unknown")
        thought = f"Exploring new region: {dest_name}"
        memory.add_visited_region(best_roam_id)
        return actions_helper.move_to(best_roam_id, thought)

    thought = "No urgent tactical actions. Resting to recover EP"
    return actions_helper.rest(thought)