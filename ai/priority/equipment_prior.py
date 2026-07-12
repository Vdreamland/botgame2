from src.helper.game_helper import WEAPONS, ARMOR

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
    if isinstance(name, dict):
        name = name.get("name", "")
    norm = str(name).lower().replace(" ", "_")
    if "sniper" in norm:
        return "sniper"
    if "plate" in norm:
        return "plate"
    if "chainmail" in norm:
        return "chainmail"
    if "leather" in norm:
        return "leather"
    return norm

def get_item_name(item):
    if not item:
        return ""
    if isinstance(item, dict):
        return item.get("name", "")
    return str(item)

def get_item_id(item):
    if isinstance(item, dict):
        return item.get("id")
    return None

def get_equipment_decision(view_data, agent_info):
    self_data = view_data.get("self", {}) or {}
    equipped_dict = self_data.get("equipped", {}) or {}
    
    eq_weapon_item = equipped_dict.get("weapon") if isinstance(equipped_dict, dict) else None
    eq_armor_item = equipped_dict.get("armor") if isinstance(equipped_dict, dict) else None

    eq_weapon_name = get_item_name(eq_weapon_item)
    eq_armor_name = get_item_name(eq_armor_item)
    eq_weapon_id = get_item_id(eq_weapon_item)
    eq_armor_id = get_item_id(eq_armor_item)

    inventory = agent_info.get_inventory()

    owned_melee = []
    owned_ranged = []
    owned_armors = []
    seen_ids = set()

    if eq_weapon_id:
        w_name = normalize_item_name(eq_weapon_name)
        if w_name in MELEE_RANKS:
            owned_melee.append(eq_weapon_item)
            seen_ids.add(eq_weapon_id)
        elif w_name in RANGED_RANKS:
            owned_ranged.append(eq_weapon_item)
            seen_ids.add(eq_weapon_id)

    if eq_armor_id:
        owned_armors.append(eq_armor_item)
        seen_ids.add(eq_armor_id)

    for item in inventory:
        if not isinstance(item, dict):
            continue
        i_id = item.get("id")
        if i_id in seen_ids:
            continue
        i_name = normalize_item_name(item.get("name"))
        if i_name in MELEE_RANKS:
            owned_melee.append(item)
            seen_ids.add(i_id)
        elif i_name in RANGED_RANKS:
            owned_ranged.append(item)
            seen_ids.add(i_id)
        elif i_name in ARMOR_RANKS:
            owned_armors.append(item)
            seen_ids.add(i_id)

    owned_melee.sort(key=lambda w: MELEE_RANKS.get(normalize_item_name(w.get("name")), 0), reverse=True)
    owned_ranged.sort(key=lambda w: RANGED_RANKS.get(normalize_item_name(w.get("name")), 0), reverse=True)
    owned_armors.sort(key=lambda a: ARMOR_RANKS.get(normalize_item_name(a.get("name")), 0), reverse=True)

    keep_melee_ids = {w.get("id") for w in owned_melee[:2]}
    keep_ranged_ids = {w.get("id") for w in owned_ranged[:2]}
    keep_armor_id = owned_armors[0].get("id") if owned_armors else None

    if eq_weapon_id:
        w_name = normalize_item_name(eq_weapon_name)
        if w_name in MELEE_RANKS:
            keep_melee_ids.add(eq_weapon_id)
        elif w_name in RANGED_RANKS:
            keep_ranged_ids.add(eq_weapon_id)

    if eq_armor_id:
        keep_armor_id = eq_armor_id

    best_melee = owned_melee[0] if owned_melee else None
    best_ranged = owned_ranged[0] if owned_ranged else None
    best_armor = owned_armors[0] if owned_armors else None

    if best_armor:
        best_armor_norm = normalize_item_name(best_armor.get("name"))
        eq_armor_norm = normalize_item_name(eq_armor_name)
        if eq_armor_norm != best_armor_norm:
            return {"action": "equip", "item_id": best_armor.get("id")}

    eq_weapon_norm = normalize_item_name(eq_weapon_name)
    if eq_weapon_norm in MELEE_RANKS:
        if best_melee:
            best_melee_norm = normalize_item_name(best_melee.get("name"))
            if eq_weapon_norm != best_melee_norm:
                return {"action": "equip", "item_id": best_melee.get("id")}
    elif eq_weapon_norm in RANGED_RANKS:
        if best_ranged:
            best_ranged_norm = normalize_item_name(best_ranged.get("name"))
            if eq_weapon_norm != best_ranged_norm:
                return {"action": "equip", "item_id": best_ranged.get("id")}
    else:
        if best_melee and best_ranged:
            m_rank = MELEE_RANKS.get(normalize_item_name(best_melee.get("name")), 0)
            r_rank = RANGED_RANKS.get(normalize_item_name(best_ranged.get("name")), 0)
            if m_rank >= r_rank:
                return {"action": "equip", "item_id": best_melee.get("id")}
            else:
                return {"action": "equip", "item_id": best_ranged.get("id")}
        elif best_melee:
            return {"action": "equip", "item_id": best_melee.get("id")}
        elif best_ranged:
            return {"action": "equip", "item_id": best_ranged.get("id")}

    for item in inventory:
        if not isinstance(item, dict):
            continue
        i_id = item.get("id")
        if i_id == eq_weapon_id or i_id == eq_armor_id:
            continue
        i_name = normalize_item_name(item.get("name"))
        if i_name in MELEE_RANKS:
            if i_id not in keep_melee_ids:
                return {"action": "drop", "item_id": i_id}
        elif i_name in RANGED_RANKS:
            if i_id not in keep_ranged_ids:
                return {"action": "drop", "item_id": i_id}
        elif i_name in ARMOR_RANKS:
            if i_id != keep_armor_id:
                return {"action": "drop", "item_id": i_id}

    return None