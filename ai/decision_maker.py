from src.helper import actions_helper
import ai.priority as priority
import ai.strategy as strategy
from ai.strategy.pre_action_safety import is_action_safe
from ai.tactics_handler import chase_committed_target, hunt_vulnerable_target, roam_and_rest
from src.helper.game_helper import resolve_equipped

MELEE_RANKS = {
    "knife": 1,
    "dagger": 2,
    "sword": 3,
    "katana": 4
}

RANGED_RANKS = {
    "bow": 1,
    "pistol": 2,
    "sniper": 3
}

ARMOR_RANKS = {
    "leather": 1,
    "chainmail": 2,
    "plate": 3
}

def normalize_item_name(name):
    if not name:
        return ""
    norm = name.lower().replace(" ", "_")
    if "sniper" in norm:
        return "sniper"
    if "plate" in norm:
        return "plate"
    if "chainmail" in norm:
        return "chainmail"
    if "leather" in norm:
        return "leather"
    return norm

def get_decision(view_data, agent_info, enemy_detector, deadzone_detector, ground_detector, memory):
    view = view_data
    self_data = view.get("self", {}) or {}
    ep = self_data.get("ep", 0)
    hp = self_data.get("hp", 0)

    visible_regions = view.get("visibleRegions", []) or []
    current_region = view.get("currentRegion", {}) or {}
    current_region_id = current_region.get("id")

    region_names = {r.get("id"): r.get("name") for r in visible_regions if r.get("id")}
    if current_region_id:
        region_names[current_region_id] = current_region.get("name")

    inventory = agent_info.get_inventory()
    resolved = resolve_equipped(view_data, inventory)
    eq_weapon_name = resolved.get("weapon_name")

    survival = priority.get_survival_decision(view_data, agent_info, enemy_detector, deadzone_detector)
    if survival and survival.get("is_danger"):
        reason = survival.get("reason")
        connections = current_region.get("connections") or current_region.get("links") or []
        safe_escape_regions = []
        for r_id in connections:
            r_data = next((r for r in visible_regions if r.get("id") == r_id), None)
            if r_data:
                is_death = r_data.get("isDeathZone") or r_data.get("isDeadZone") or False
                if not is_death:
                    safe_escape_regions.append(r_id)

        if reason == "deadzone":
            if safe_escape_regions:
                dest_id = safe_escape_regions[0]
                dest_name = region_names.get(dest_id, "Unknown")
                thought = f"Deadzone escape to {dest_name}"
                action = actions_helper.move_to(dest_id, thought)
                if is_action_safe(view, action, agent_info, enemy_detector):
                    return action

            rec_dec = priority.get_recovery_decision(view_data, agent_info)
            if rec_dec and rec_dec.get("action") == "use":
                item_name = "consumable"
                for it in inventory:
                    if isinstance(it, dict) and it.get("id") == rec_dec.get("item_id"):
                        item_name = it.get("name")
                        break
                thought = f"Deadzone trapped recovery: {item_name}"
                action = actions_helper.use_item(rec_dec.get("item_id"), thought)
                if is_action_safe(view, action, agent_info, enemy_detector):
                    return action
        else:
            rec_dec = priority.get_recovery_decision(view_data, agent_info)
            if rec_dec and rec_dec.get("action") == "use":
                item_name = "consumable"
                for it in inventory:
                    if isinstance(it, dict) and it.get("id") == rec_dec.get("item_id"):
                        item_name = it.get("name")
                        break
                thought = f"Threat recovery: {item_name}"
                action = actions_helper.use_item(rec_dec.get("item_id"), thought)
                if is_action_safe(view, action, agent_info, enemy_detector):
                    return action

            if safe_escape_regions:
                dest_id = safe_escape_regions[0]
                dest_name = region_names.get(dest_id, "Unknown")
                thought = f"Threat escape to {dest_name}"
                action = actions_helper.move_to(dest_id, thought)
                if is_action_safe(view, action, agent_info, enemy_detector):
                    return action

    equip_dec = priority.get_equipment_decision(view_data, agent_info, enemy_detector)
    if equip_dec:
        act = equip_dec.get("action")
        item_id = equip_dec.get("item_id")
        item_name = "item"
        for it in inventory:
            if isinstance(it, dict) and it.get("id") == item_id:
                item_name = it.get("name")
                break
        action = None
        if act == "equip":
            thought = f"Equip: {item_name}"
            action = actions_helper.equip_item(item_id, thought)
        elif act == "drop":
            thought = f"Drop redundant: {item_name}"
            action = actions_helper.drop_item(item_id, thought)
        if action and is_action_safe(view, action, agent_info, enemy_detector):
            return action

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
        thought = f"Attack {target_name} ({target_type})"
        action = actions_helper.attack_target(target_id, target_type, thought)
        if is_action_safe(view, action, agent_info, enemy_detector):
            memory.set_target(target_id)
            return action

    loot_dec = priority.get_loot_decision(view_data, agent_info, ground_detector)
    if loot_dec:
        act = loot_dec.get("action")
        item_id = loot_dec.get("item_id")
        ground_items = ground_detector.visible_items
        action = None
        if act == "pickup":
            item_name = "item"
            for it in ground_items:
                if isinstance(it, dict) and it.get("id") == item_id:
                    item_name = it.get("name")
                    break
            thought = f"Loot {item_name}"
            action = actions_helper.pickup_item(item_id, thought)
        elif act == "move_to_loot":
            r_id = loot_dec.get("region_id")
            item_name = loot_dec.get("item_name")
            dest_name = region_names.get(r_id, "Unknown")
            thought = f"Move to {dest_name} for {item_name}"
            action = actions_helper.move_to(r_id, thought)
        if action and is_action_safe(view, action, agent_info, enemy_detector):
            return action

    rec_dec = priority.get_recovery_decision(view_data, agent_info)
    if rec_dec:
        act = rec_dec.get("action")
        item_id = rec_dec.get("item_id")
        item_name = "consumable"
        for it in inventory:
            if isinstance(it, dict) and it.get("id") == item_id:
                item_name = it.get("name")
                break
        action = None
        if act == "use":
            thought = f"Recovery use: {item_name}"
            action = actions_helper.use_item(item_id, thought)
        elif act == "drop":
            thought = f"Recovery drop excess: {item_name}"
            action = actions_helper.drop_item(item_id, thought)
        if action and is_action_safe(view, action, agent_info, enemy_detector):
            return action

    hunt_action = hunt_vulnerable_target(
        view_data, agent_info, enemy_detector, ep, current_region_id, visible_regions, region_names
    )
    if hunt_action:
        return hunt_action

    chase_action = chase_committed_target(
        view_data, agent_info, enemy_detector, memory, ep, current_region_id, visible_regions, region_names
    )
    if chase_action:
        return chase_action

    interact_dec = priority.get_interact_decision(view_data, agent_info)
    if interact_dec:
        act_type = interact_dec.get("action")
        action = None
        if act_type == "explore":
            thought = f"Explore ruin"
            action = actions_helper.explore_ruin(thought)
        elif act_type == "interact":
            fac_id = interact_dec.get("interactable_id")
            interactables = current_region.get("interactables", []) or []
            fac_type = "facility"
            for fac in interactables:
                if isinstance(fac, dict) and fac.get("id") == fac_id:
                    fac_type = fac.get("type")
                    break
            thought = f"Interact {fac_type}"
            action = actions_helper.interact_facility(fac_id, thought)
        if action and is_action_safe(view, action, agent_info, enemy_detector):
            return action

    best_ruin_id = strategy.get_best_ruin_target(view_data)
    if best_ruin_id:
        step = strategy.get_next_step(view_data, best_ruin_id)
        if step:
            dest_name = region_names.get(step, "Unknown")
            target_name = region_names.get(best_ruin_id, "Unknown")
            thought = f"Navigate ruin {target_name} via {dest_name}"
            action = actions_helper.move_to(step, thought)
            if is_action_safe(view, action, agent_info, enemy_detector):
                return action

    return roam_and_rest(view_data, agent_info, enemy_detector, memory, current_region_id, region_names)