from ai.priority.equipment_prior import evaluate_equipment
from ai.priority.region_loot_prior import get_best_loot_action
from ai.priority.recovery_prior import score_recovery_actions
from ai.priority.interact_prior import score_interactables
from ai.priority.target_kill_prior import score_targets
from ai.strategy.movement_strategy import get_best_movement_action
from ai.strategy.ruin_exploration_strategy import score_exploration

INTERACTED_FACILITIES = set()

def decide_next_action(view):
    self_data = view.get("self", {}) or {}
    hp = self_data.get("hp", 100)
    ep = self_data.get("ep", 10)
    atk = self_data.get("atk", 25)
    inventory = self_data.get("inventory", []) or []
    current_weapon = self_data.get("equippedWeaponId")
    current_armor = self_data.get("equippedArmorId")
    
    current_region = view.get("currentRegion", {}) or {}
    visible_regions = view.get("visibleRegions", []) or []
    ground_items = current_region.get("items", []) or current_region.get("groundItems", []) or []
    interactables = current_region.get("interactables", []) or []
    
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
    
    if eval_equip["to_equip_weapon"]:
        item_obj = eval_equip["to_equip_weapon"]
        item_id = item_obj.get("id") or item_obj.get("typeId") if isinstance(item_obj, dict) else item_obj
        return {
            "type": "action",
            "data": {
                "type": "equip",
                "itemId": item_id
            }
        }
        
    if eval_equip["to_equip_armor"]:
        item_obj = eval_equip["to_equip_armor"]
        item_id = item_obj.get("id") or item_obj.get("typeId") if isinstance(item_obj, dict) else item_obj
        return {
            "type": "action",
            "data": {
                "type": "equip",
                "itemId": item_id
            }
        }
        
    if eval_equip["to_drop"] and len(inventory) >= 10:
        item_obj = eval_equip["to_drop"][0]
        item_id = item_obj.get("id") or item_obj.get("typeId") if isinstance(item_obj, dict) else item_obj
        return {
            "type": "action",
            "data": {
                "type": "drop",
                "itemId": item_id
            }
        }
        
    candidates = []
    is_safe = len(visible_agents) == 0 and len(visible_monsters) == 0 and len(visible_npcs) == 0
    
    rec_res = score_recovery_actions(hp, ep, inventory, is_safe)
    if rec_res["action"]:
        candidates.append((rec_res["score"], rec_res["action"]))
        
    loot_res = get_best_loot_action(ground_items, inventory, hp, ep, current_weapon, current_armor)
    if loot_res:
        candidates.append((loot_res["score"], {"action": "pickup", "item": loot_res["item"]}))
        
    inter_res = score_interactables(interactables, hp, ep, INTERACTED_FACILITIES)
    if inter_res["action"]:
        candidates.append((inter_res["score"], inter_res["action"]))
        
    explore_res = score_exploration([current_region], alert_gauge, ep)
    if explore_res["action"]:
        candidates.append((explore_res["score"], explore_res["action"]))
        
    move_res = get_best_movement_action(connected_regions, visible_regions, pending_deathzones, hp, ep, is_safe, inventory, current_weapon, current_armor, INTERACTED_FACILITIES, current_region)
    if move_res:
        candidates.append((move_res["score"], move_res["action"]))
        
    if not candidates:
        best_action = {"action": "rest"}
    else:
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_action = candidates[0][1]
        
    act_type = best_action.get("action")
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
        if t_id:
            INTERACTED_FACILITIES.add(t_id)
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
        
    return {
        "type": "action",
        "data": {
            "type": "rest"
        }
    }