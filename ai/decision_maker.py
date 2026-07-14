from ai.priority.equipment_prior import evaluate_equipment
from ai.priority.region_loot_prior import get_best_loot_action
from ai.priority.recovery_prior import score_recovery_actions
from ai.priority.interact_prior import score_interactables
from ai.priority.target_kill_prior import score_targets
from ai.priority.survival_prior import evaluate_survival
from ai.strategy.movement_strategy import get_best_movement_action
from ai.strategy.ruin_exploration_strategy import score_exploration
from ai.detector import detect_connected_regions

_LOCAL_INTERACTED = set()
_LOCAL_LAST_TARGET = None

def is_entity_alive(entity):
    if not isinstance(entity, dict):
        return False
    is_alive_camel = entity.get('isAlive')
    if is_alive_camel is not None:
        return bool(is_alive_camel)
    is_alive_snake = entity.get('is_alive')
    if is_alive_snake is not None:
        return bool(is_alive_snake)
    hp = entity.get('hp')
    if hp is not None:
        try:
            return float(hp) > 0
        except (ValueError, TypeError):
            pass
    return True

def decide_next_action(view, context=None):
    global _LOCAL_LAST_TARGET
    
    if context is not None:
        if not hasattr(context, "interacted_facilities") or context.interacted_facilities is None:
            context.interacted_facilities = set()
        if not hasattr(context, "last_target_id"):
            context.last_target_id = None
            
        interacted_ids = context.interacted_facilities
        last_target_id = context.last_target_id
    else:
        interacted_ids = _LOCAL_INTERACTED
        last_target_id = _LOCAL_LAST_TARGET

    self_data = view.get("self", {}) or {}
    hp = self_data.get("hp", 100)
    ep = self_data.get("ep", 10)
    atk = self_data.get("atk", 25)
    defense = self_data.get("def", 5)
    inventory = self_data.get("inventory", []) or []
    
    equipped_weapon = self_data.get("equippedWeapon")
    if isinstance(equipped_weapon, dict):
        current_weapon = equipped_weapon.get("name") or equipped_weapon.get("typeId") or equipped_weapon.get("id")
    else:
        current_weapon = self_data.get("equippedWeaponId") or equipped_weapon

    if current_weapon is None or str(current_weapon).lower() == "none" or current_weapon == "":
        current_weapon = None

    equipped_armor = self_data.get("equippedArmor")
    if isinstance(equipped_armor, dict):
        current_armor = equipped_armor.get("name") or equipped_armor.get("typeId") or equipped_armor.get("id")
    else:
        current_armor = self_data.get("equippedArmorId") or equipped_armor

    if current_armor is None or str(current_armor).lower() == "none" or current_armor == "":
        current_armor = None

    current_region = view.get("currentRegion", {}) or {}
    visible_regions = view.get("visibleRegions", []) or []
    ground_items = current_region.get("items", []) or current_region.get("groundItems", []) or []
    interactables = current_region.get("interactables", []) or []
    weather = current_region.get("weather", "clear")
    
    pending_deathzones = view.get("pendingDeathzones", []) or []
    alert_gauge = view.get("alertGauge", 0) or 0
    
    visible_agents = view.get("visibleAgents", []) or []
    visible_monsters = view.get("visibleMonsters", []) or []
    visible_npcs = view.get("visibleNPCs", []) or []
    
    living_agents = [e for e in visible_agents if is_entity_alive(e)]
    living_monsters = [e for e in visible_monsters if is_entity_alive(e)]
    living_npcs = [e for e in visible_npcs if is_entity_alive(e)]
    
    current_id = current_region.get("id")
    is_safe = True
    alert_active = alert_gauge >= 10
    for enemy in (living_agents + living_monsters + living_npcs):
        if isinstance(enemy, dict):
            is_enemy_guardian = enemy.get("isGuardian", False) or "guardian" in str(enemy.get("id") or "").lower() or "guardian" in str(enemy.get("name") or "").lower()
            if is_enemy_guardian and not alert_active:
                continue
            r_id = enemy.get("regionId") or enemy.get("region_id") or enemy.get("location")
            if r_id == current_id:
                is_safe = False
                break

    regions_list = detect_connected_regions(view)
    region_layers = {r.get("id"): r.get("layer", 1) for r in regions_list if r.get("id")}

    visible_regions_map = {r.get("id"): r for r in visible_regions if isinstance(r, dict) and r.get("id")}
    connected_regions = []
    connections = current_region.get("connections", []) or []
    for conn_id in connections:
        if not conn_id:
            continue
        if conn_id in visible_regions_map:
            connected_regions.append(visible_regions_map[conn_id])
        else:
            connected_regions.append({"id": conn_id, "name": conn_id})

    eval_equip = evaluate_equipment(inventory, current_weapon, current_armor)
    candidates = []

    if eval_equip["to_equip_weapon"]:
        if current_weapon is None:
            candidates.append((88, {"action": "equip", "item": eval_equip["to_equip_weapon"]}))
        elif is_safe:
            candidates.append((30, {"action": "equip", "item": eval_equip["to_equip_weapon"]}))

    if eval_equip["to_equip_armor"]:
        if current_armor is None:
            candidates.append((82, {"action": "equip", "item": eval_equip["to_equip_armor"]}))
        elif is_safe:
            candidates.append((35, {"action": "equip", "item": eval_equip["to_equip_armor"]}))

    if eval_equip["to_drop"] and len(inventory) >= 10:
        candidates.append((25, {"action": "drop", "item": eval_equip["to_drop"][0]}))

    connected_region_ids = {r.get("id") for r in connected_regions if r.get("id")}

    surv_res = evaluate_survival(hp, ep, is_safe, current_region, {"current": [e for e in (living_agents + living_monsters + living_npcs) if (e.get("regionId") or e.get("region_id")) == current_id]}, pending_deathzones, connected_region_ids)
    should_flee = surv_res["should_flee"]

    rec_res = score_recovery_actions(hp, ep, inventory, is_safe)
    if rec_res["action"]:
        score = rec_res["score"]
        if should_flee and rec_res["action"]["action"] == "use_item":
            score = min(98, score + 10)
        candidates.append((score, rec_res["action"]))

    loot_res = get_best_loot_action(ground_items, inventory, hp, ep, current_weapon, current_armor)
    if loot_res and not should_flee:
        candidates.append((loot_res["score"], {"action": "pickup", "item": loot_res["item"]}))

    inter_res = score_interactables(interactables, hp, ep, interacted_ids)
    if inter_res["action"] and not should_flee:
        candidates.append((inter_res["score"], inter_res["action"]))

    explore_res = score_exploration([current_region], alert_gauge, ep)
    if explore_res["action"] and not should_flee:
        candidates.append((explore_res["score"], explore_res["action"]))

    visible_enemies_map = {
        current_region.get("id"): [e for e in (living_agents + living_monsters + living_npcs) if str(e.get("regionId") or e.get("region_id")).lower() == str(current_region.get("id")).lower()]
    }
    for r_name, r_obj in visible_regions_map.items():
        r_id = r_obj.get("id")
        if r_id and r_id != current_region.get("id"):
            visible_enemies_map[r_id] = [e for e in (living_agents + living_monsters + living_npcs) if str(e.get("regionId") or e.get("region_id")).lower() == str(r_id).lower()]

    combat_res = score_targets(visible_enemies_map, hp, ep, current_weapon, inventory, atk, defense, weather, last_target_id, connected_region_ids, region_layers, should_flee, current_region.get("id"), alert_active)
    if combat_res["action"]:
        candidates.append((combat_res["score"], combat_res["action"]))

    move_res = get_best_movement_action(connected_regions, visible_regions, pending_deathzones, hp, ep, is_safe, inventory, current_weapon, current_armor, interacted_ids, current_region, visible_agents, visible_monsters, visible_npcs, regions_list, alert_active)
    if move_res:
        score = move_res["score"]
        if should_flee:
            score = 98
        candidates.append((score, move_res["action"]))

    if not candidates:
        best_action = {"action": "rest"}
    else:
        has_flee = False
        has_critical_heal = False
        has_finishing_kill = False
        has_rare_pickup = False

        if hp < 30:
            for score, cand in candidates:
                act = cand.get("action")
                if act == "use_item":
                    has_critical_heal = True
                    break
                elif act == "interact":
                    target = cand.get("target", {})
                    f_type = target.get("type") or target.get("name") or target.get("id") or ""
                    if "medical" in f_type.lower():
                        has_critical_heal = True
                        break

        for score, cand in candidates:
            if cand.get("action") == "attack" and score >= 95:
                has_finishing_kill = True
                break

        for score, cand in candidates:
            if cand.get("action") == "pickup" and score >= 80:
                has_rare_pickup = True
                break

        is_in_death_zone = current_region.get("is_death_zone") or current_region.get("isDeathZone") or False
        if has_critical_heal and not is_in_death_zone:
            filtered_candidates = []
            for score, cand in candidates:
                act = cand.get("action")
                if act == "use_item":
                    filtered_candidates.append((score + 50, cand))
                elif act == "interact":
                    target = cand.get("target", {})
                    f_type = target.get("type") or target.get("name") or target.get("id") or ""
                    if "medical" in f_type.lower():
                        filtered_candidates.append((score + 50, cand))
            if filtered_candidates:
                candidates = filtered_candidates

        elif has_finishing_kill and hp >= 30:
            filtered_candidates = []
            for score, cand in candidates:
                if cand.get("action") == "attack" and score >= 95:
                    filtered_candidates.append((score + 50, cand))
            if filtered_candidates:
                candidates = filtered_candidates

        elif has_rare_pickup and is_safe:
            filtered_candidates = []
            for score, cand in candidates:
                if cand.get("action") == "pickup" and score >= 80:
                    filtered_candidates.append((score + 50, cand))
            if filtered_candidates:
                candidates = filtered_candidates

        candidates.sort(key=lambda x: x[0], reverse=True)
        
        print("\n================== DECISION CANDIDATES ==================")
        for i, (score, cand) in enumerate(candidates[:5]):
            act_type = cand.get("action") or cand.get("type")
            target_str = ""
            if act_type == "move":
                target_str = f"to region {cand.get('target', {}).get('name') or cand.get('target')}"
            elif act_type == "move_to_enemy":
                target_str = f"to enemy region {cand.get('region_id')}"
            elif act_type in ("pickup", "equip", "use_item", "drop"):
                target_str = f"item {cand.get('item', {}).get('name') or cand.get('item', {}).get('id') or cand.get('item')}"
            elif act_type == "interact":
                target_str = f"facility {cand.get('target', {}).get('name') or cand.get('target', {}).get('type') or cand.get('target', {}).get('id')}"
            elif act_type == "attack":
                target_str = f"target {cand.get('target', {}).get('name') or cand.get('target', {}).get('id')}"
            
            winner_mark = "★ [WINNER]" if i == 0 else "  [Candidate]"
            print(f" {winner_mark} Score: {score:.1f} | Action: {act_type} {target_str}")
        print("=========================================================\n")
        
        best_action = None
        for score, cand in candidates:
            act_type = cand.get("action")
            
            if act_type == "move":
                target = cand.get("target", {})
                r_id = target.get("id") if isinstance(target, dict) else target
                if r_id:
                    best_action = cand
                    break
            elif act_type == "move_to_enemy":
                target_region_id = cand.get("region_id")
                r_id = None
                for r in connected_regions:
                    if r.get("id") == target_region_id:
                        r_id = r.get("id")
                        break
                if not r_id:
                    for r in regions_list:
                        if r.get("id") == target_region_id:
                            r_id = r.get("first_step")
                            break
                if r_id:
                    best_action = cand
                    break
            elif act_type in ("pickup", "equip", "use_item", "drop", "rest", "interact", "explore", "attack"):
                best_action = cand
                break

    if not best_action:
        best_action = {"action": "rest"}

    act_type = best_action.get("action")
    new_target_id = None
    if act_type in ("attack", "move_to_enemy"):
        target_obj = best_action.get("target", {})
        new_target_id = target_obj.get("id") or target_obj.get("agentId") or target_obj.get("monsterId") or target_obj.get("npcId")

    if context is not None:
        context.last_target_id = new_target_id
    else:
        _LOCAL_LAST_TARGET = new_target_id

    if act_type == "move":
        target = best_action.get("target", {})
        r_id = target.get("id") if isinstance(target, dict) else target
        return {
            "type": "action",
            "data": {
                "type": "move",
                "regionId": r_id
            }
        }
    elif act_type == "move_to_enemy":
        target_region_id = best_action.get("region_id")
        r_id = None
        for r in regions_list:
            if r.get("id") == target_region_id:
                r_id = r.get("first_step")
                break
        if not r_id:
            for r in connected_regions:
                if r.get("id") == target_region_id:
                    r_id = r.get("id")
                    break
        if r_id:
            return {
                "type": "action",
                "data": {
                    "type": "move",
                    "regionId": r_id
                }
            }
    elif act_type == "pickup":
        item_obj = best_action.get("item", {})
        item_id = item_obj.get("id") or item_obj.get("typeId") if isinstance(item_obj, dict) else item_obj
        return {
            "type": "action",
            "data": {
                "type": "pickup",
                "itemId": item_id
            }
        }
    elif act_type == "equip":
        item_obj = best_action.get("item", {})
        item_id = item_obj.get("id") or item_obj.get("typeId") if isinstance(item_obj, dict) else item_obj
        return {
            "type": "action",
            "data": {
                "type": "equip",
                "itemId": item_id
            }
        }
    elif act_type == "use_item":
        item_obj = best_action.get("item", {})
        item_id = item_obj.get("id") or item_obj.get("typeId") if isinstance(item_obj, dict) else item_obj
        return {
            "type": "action",
            "data": {
                "type": "use_item",
                "itemId": item_id
            }
        }
    elif act_type == "drop":
        item_obj = best_action.get("item", {})
        item_id = item_obj.get("id") or item_obj.get("typeId") if isinstance(item_obj, dict) else item_obj
        return {
            "type": "action",
            "data": {
                "type": "drop",
                "itemId": item_id
            }
        }
    elif act_type == "rest":
        return {
            "type": "action",
            "data": {
                "type": "rest"
            }
        }
    elif act_type == "interact":
        target = best_action.get("target", {})
        t_id = target.get("id") or target.get("targetId") or target.get("facilityId")
        
        if t_id and context is not None:
            context.interacted_facilities.add(t_id)
        elif t_id:
            _LOCAL_INTERACTED.add(t_id)
                
        return {
            "type": "action",
            "data": {
                "type": "interact",
                "targetId": t_id
            }
        }
    elif act_type == "explore":
        target = best_action.get("target", {})
        ruin_id = target.get("id") or target.get("ruinId")
        return {
            "type": "action",
            "data": {
                "type": "explore",
                "ruinId": ruin_id
            }
        }
    elif act_type == "attack":
        target = best_action.get("target", {})
        t_id = target.get("id") or target.get("agentId") or target.get("monsterId") or target.get("npcId")
        return {
            "type": "action",
            "data": {
                "type": "attack",
                "targetId": t_id
            }
        }
        
    return {
        "type": "action",
        "data": {
            "type": "rest"
        }
    }