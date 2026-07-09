def make_action(action_type, data_payload, thought=None):
    payload = {
        "type": "action",
        "data": {
            "type": action_type,
            **data_payload
        }
    }
    if thought is not None:
        payload["thought"] = str(thought)[:700]
    return payload

def move_to(region_id, thought=None):
    return make_action("move", {"regionId": region_id}, thought)

def explore_ruin(thought=None):
    return make_action("explore", {}, thought)

def attack_target(target_id, target_type="agent", thought=None):
    return make_action("attack", {"targetId": target_id, "targetType": target_type}, thought)

def use_item(item_id, thought=None):
    return make_action("use_item", {"itemId": item_id}, thought)

def interact_facility(interactable_id, thought=None):
    return make_action("interact", {"interactableId": interactable_id}, thought)

def rest(thought=None):
    return make_action("rest", {}, thought)

def pickup_item(item_id, thought=None):
    return make_action("pickup", {"itemId": item_id}, thought)

def drop_item(item_id, thought=None):
    return make_action("drop", {"itemId": item_id}, thought)

def equip_item(item_id, thought=None):
    return make_action("equip", {"itemId": item_id}, thought)