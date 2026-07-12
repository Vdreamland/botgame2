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

def get_equipment_decision(view_data, agent_info):
    equipped = agent_info.get_equipped()
    inventory = agent_info.get_inventory()

    eq_weapon = equipped.get("weapon")
    eq_armor = equipped.get("armor")

    owned_melee = []
    owned_ranged = []
    owned_armors = []

    if eq_weapon and isinstance(eq_weapon, dict):
        w_name = normalize_item_name(eq_weapon.get("name"))
        if w_name in MELEE_RANKS:
            owned_melee.append(eq_weapon)
        elif w_name in RANGED_RANKS:
            owned_ranged.append(eq_weapon)

    if eq_armor and isinstance(eq_armor, dict):
        owned_armors.append(eq_armor)

    for item in inventory:
        if not isinstance(item, dict):
            continue
        i_name = normalize_item_name(item.get("name"))
        if i_name in MELEE_RANKS:
            owned_melee.append(item)
        elif i_name in RANGED_RANKS:
            owned_ranged.append(item)
        elif i_name in ARMOR_RANKS:
            owned_armors.append(item)

    owned_melee.sort(key=lambda w: MELEE_RANKS.get(normalize_item_name(w.get("name")), 0), reverse=True)
    owned_ranged.sort(key=lambda w: RANGED_RANKS.get(normalize_item_name(w.get("name")), 0), reverse=True)
    owned_armors.sort(key=lambda a: ARMOR_RANKS.get(normalize_item_name(a.get("name")), 0), reverse=True)

    keep_melee_ids = {w.get("id") for w in owned_melee[:2]}
    keep_ranged_ids = {w.get("id") for w in owned_ranged[:2]}
    keep_armor_id = owned_armors[0].get("id") if owned_armors else None

    best_melee = owned_melee[0] if owned_melee else None
    best_ranged = owned_ranged[0] if owned_ranged else None
    best_armor = owned_armors[0] if owned_armors else None

    if best_armor and eq_armor and isinstance(eq_armor, dict):
        if best_armor.get("id") != eq_armor.get("id"):
            return {"action": "equip", "item_id": best_armor.get("id")}
    elif best_armor and not eq_armor:
        return {"action": "equip", "item_id": best_armor.get("id")}

    if eq_weapon and isinstance(eq_weapon, dict):
        eq_name = normalize_item_name(eq_weapon.get("name"))
        if eq_name in MELEE_RANKS:
            if best_melee and best_melee.get("id") != eq_weapon.get("id"):
                return {"action": "equip", "item_id": best_melee.get("id")}
        elif eq_name in RANGED_RANKS:
            if best_ranged and best_ranged.get("id") != eq_weapon.get("id"):
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
        i_name = normalize_item_name(item.get("name"))
        i_id = item.get("id")
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