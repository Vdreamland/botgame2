def get_interact_decision(view_data, agent_info):
    view = view_data.get("view", {}) or {}
    current_region = view.get("currentRegion", {}) or {}
    region_name = current_region.get("name", "")
    is_empty = current_region.get("isEmpty", False)

    if region_name in ("S:Relic", "S:Pack") and not is_empty:
        my_id = view.get("self", {}).get("id")
        occupant = current_region.get("ruinOccupant")
        if not occupant or occupant == my_id:
            return {"action": "explore"}

    interactables = current_region.get("interactables", []) or []
    self_data = view.get("self", {}) or {}
    hp = self_data.get("hp", 0)
    inventory = self_data.get("inventory", []) or []

    for fac in interactables:
        if not isinstance(fac, dict):
            continue
        fac_id = fac.get("id")
        fac_type = fac.get("type")
        is_used = fac.get("isUsed", False)

        if is_used:
            continue

        if fac_type == "medical_facility":
            if hp <= 80:
                return {"action": "interact", "interactable_id": fac_id}

        elif fac_type == "supply_cache":
            if len(inventory) < 10:
                return {"action": "interact", "interactable_id": fac_id}

    return None