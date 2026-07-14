def score_recovery_actions(hp, ep, inventory, is_safe):
    medkits = []
    small_healers = []
    ep_items = []

    for item in inventory:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        item_type = item.get("type") or item.get("typeId") or item.get("name") or item_id
        if not item_type:
            continue
        name_clean = str(item_type).lower()

        if "medkit" in name_clean:
            medkits.append(item)
        elif "bandage" in name_clean or "food" in name_clean:
            small_healers.append(item)
        elif "drink" in name_clean or "potion" in name_clean:
            ep_items.append(item)

    hp_item = None
    if medkits or small_healers:
        if hp < 50:
            hp_item = medkits[0] if medkits else small_healers[0]
        else:
            hp_item = small_healers[0] if small_healers else medkits[0]

    ep_item = ep_items[0] if ep_items else None

    if hp_item:
        if hp < 30:
            score = 98
        elif hp < 50:
            score = 85
        else:
            score = int((100 - hp) * 0.9)
            
        return {
            "score": min(100, max(0, score)),
            "action": {"action": "use_item", "item": hp_item}
        }

    if ep <= 2 and ep_item:
        score = 90
        return {
            "score": score,
            "action": {"action": "use_item", "item": ep_item}
        }

    if is_safe:
        if ep <= 2:
            score = 80
        elif ep == 3:
            score = 60
        elif ep >= 4 and ep <= 7:
            score = int((10 - ep) * 8)
        else:
            score = 0
            
        if score > 0:
            return {
                "score": min(100, max(0, score)),
                "action": {"action": "rest"}
            }

    return {
        "score": 0,
        "action": None
    }