_LOCAL_INTERACTED = set()

def build_action_payload(best_action, context=None):
    global _LOCAL_INTERACTED
    
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
    elif act_type == "move_to_enemy":
        target_region_id = best_action.get("region_id")
        return {
            "type": "action",
            "data": {
                "type": "move",
                "regionId": target_region_id
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