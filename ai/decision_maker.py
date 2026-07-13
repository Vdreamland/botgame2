from ai.priority.equipment_prior import evaluate_equipment
from ai.priority.region_loot_prior import get_best_loot_action
from ai.priority.recovery_prior import score_recovery_actions
from ai.priority.interact_prior import score_interactables
from ai.priority.target_kill_prior import score_targets
from ai.priority.survival_prior import evaluate_survival
from ai.strategy.movement_strategy import get_best_movement_action
from ai.strategy.ruin_exploration_strategy import score_exploration

_LOCAL_INTERACTED = set()
_LOCAL_LAST_TARGET = None

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
    current_weapon = self_data.get("equippedWeaponId")
    current_armor = self_data.get("equippedArmorId")
    
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
    is_safe = len(visible_agents) == 0 and len(visible_monsters) == 0 and len(visible_npcs) == 0
    
    if eval_equip["to_equip_weapon"]:
        if current_weapon is None:
            candidates.append((300, {"action": "equip", "item": eval_equip["to_equip_weapon"]}))
        elif is_safe:
            candidates.append((30, {"action": "equip", "item": eval_equip["to_equip_weapon"]}))
            
    if eval_equip["to_equip_armor"]:
        if current_armor is None:
            candidates.append((305, {"action": "equip", "item": eval_equip["to_equip_armor"]}))
        elif is_safe:
            candidates.append((35, {"action": "equip", "item": eval_equip["to_equip_armor"]}))
            
    if eval_equip["to_drop"] and len(inventory) >= 10:
        candidates.append((80, {"action": "drop", "item": eval_equip["to_drop"][0]}))
        
    surv_res = evaluate_survival(hp, ep, is_safe, current_region, {"visibleAgents": visible_agents, "visibleMonsters": visible_monsters, "visibleNPCs": visible_npcs}, pending_deathzones)
    should_flee = surv_res["should_flee"]
    
    rec_res = score_recovery_actions(hp, ep, inventory, is_safe)
    if rec_res["action"]:
        score = rec_res["score"]
        if should_flee and rec_res["action"]["action"] == "use_item":
            score += 30
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
        current_region.get("id"): [e for e in (visible_agents + visible_monsters + visible_npcs) if str(e.get("regionId") or e.get("region_id")).lower() == str(current_region.get("id")).lower()]
    }
    for r_name, r_obj in visible_regions_map.items():
        r_id = r_obj.get("id")
        if r_id and r_id != current_region.get("id"):
            visible_enemies_map[r_id] = [e for e in (visible_agents + visible_monsters + visible_npcs) if str(e.get("regionId") or e.get("region_id")).lower() == str(r_id).lower()]
            
    connected_region_ids = {r.get("id") for r in connected_regions if r.get("id")}
    combat_res = score_targets(visible_enemies_map, hp, ep, current_weapon, inventory, atk, defense, weather, last_target_id, connected_region_ids)
    if combat_res["action"]:
        candidates.append((combat_res["score"], combat_res["action"]))
        
    move_res = get_best_movement_action(connected_regions, visible_regions, pending_deathzones, hp, ep, is_safe, inventory, current_weapon, current_armor, interacted_ids, current_region, visible_agents, visible_monsters, visible_npcs)
    if move_res:
        score = move_res["score"]
        if should_flee:
            score += 150
        candidates.append((score, move_res["action"]))
        
    if not candidates:
        print("[DEBUG DECISION] candidates are empty!")
        best_action = {"action": "rest"}
    else:
        candidates.sort(key=lambda x: x[0], reverse=True)
        print(f"[DEBUG DECISION] candidates: {[(c[0], c[1].get('action') or c[1].get('type')) for c in candidates]}")
        
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