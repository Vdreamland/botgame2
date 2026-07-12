def get_recovery_decision(view_data, agent_info):
    view = view_data.get("view", {}) or {}
    self_data = view.get("self", {}) or {}
    hp = self_data.get("hp", 0)
    ep = self_data.get("ep", 0)
    inventory = agent_info.get_inventory(view_data)

    medkit_item = None
    bandage_item = None
    drink_item = None
    food_item = None

    hp_items = []
    ep_items = []

    for item in inventory:
        if not isinstance(item, dict):
            continue
        name = item.get("name", "")
        item_id = item.get("id")

        if name == "medkit":
            medkit_item = item
            hp_items.append(item)
        elif name == "bandage":
            bandage_item = item
            hp_items.append(item)
        elif name == "energy_drink":
            drink_item = item
            ep_items.append(item)
        elif name == "emergency_food":
            food_item = item
            ep_items.append(item)

    if hp <= 50 and medkit_item:
        return {"action": "use", "item_id": medkit_item.get("id")}
    if hp <= 80 and bandage_item:
        return {"action": "use", "item_id": bandage_item.get("id")}
    if ep <= 6 and drink_item:
        return {"action": "use", "item_id": drink_item.get("id")}
    if ep <= 8 and food_item:
        return {"action": "use", "item_id": food_item.get("id")}

    if len(inventory) >= 10 and len(hp_items) >= 3 and len(ep_items) == 0:
        if bandage_item:
            return {"action": "drop", "item_id": bandage_item.get("id")}
        elif medkit_item:
            return {"action": "drop", "item_id": medkit_item.get("id")}

    return None