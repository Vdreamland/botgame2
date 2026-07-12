from src.helper.game_helper import WEAPONS, ARMOR, normalize_item_name, get_item_name, get_item_id, resolve_equipped

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

def get_equipment_decision(view_data, agent_info, enemy_detector=None):
    inventory = agent_info.get_inventory()
    resolved = resolve_equipped(view_data, inventory)

    eq_weapon_name = resolved.get("weapon_name")
    eq_armor_name = resolved.get("armor_name")
    eq_weapon_id = resolved.get("weapon_id")
    eq_armor_id = resolved.get("armor_id")

    has_local_enemy = False
    has_ranged_enemy = False

    if enemy_detector:
        current_region_id = view_data.get("currentRegion", {}).get("id")
        enemies = enemy_detector.get_alive_agents() + enemy_detector.get_alive_monsters()
        for e in enemies:
            e_zone = e.get("zone") or e.get("regionId") or e.get("region")
            if e_zone == current_region_id:
                e_name = e.get("name", "").lower()
                e_type = e.get("type", "").lower()
                if "guardian" not in e_name and "guardian" not in e_type:
                    has_local_enemy = True
                    break
        if not has_local_enemy:
            for e in enemies:
                e_name = e.get("name", "").lower()
                e_type = e.get("type", "").lower()
                if "guardian" not in e_name and "guardian" not in e_type:
                    has_ranged_enemy = True
                    break

    owned_melee = []
    owned_ranged = []
    owned_armors = []

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

    keep_melee_ids = set()
    seen_melee_names = set()
    for w in owned_melee:
        w_name = normalize_item_name(w.get("name"))
        if w_name not in seen_melee_names:
            if len(keep_melee_ids) < 2:
                keep_melee_ids.add(w.get("id"))
                seen_melee_names.add(w_name)

    keep_ranged_ids = set()
    seen_ranged_names = set()
    for w in owned_ranged:
        w_name = normalize_item_name(w.get("name"))
        if w_name not in seen_ranged_names:
            if len(keep_ranged_ids) < 2:
                keep_ranged_ids.add(w.get("id"))
                seen_ranged_names.add(w_name)

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

    if has_local_enemy:
        m_rank = MELEE_RANKS.get(normalize_item_name(best_melee.get("name")), 0) if best_melee else 0
        r_rank = RANGED_RANKS.get(normalize_item_name(best_ranged.get("name")), 0) if best_ranged else 0
        if m_rank > r_rank and best_melee:
            best_melee_norm = normalize_item_name(best_melee.get("name"))
            if eq_weapon_norm != best_melee_norm:
                return {"action": "equip", "item_id": best_melee.get("id")}
        elif best_ranged:
            best_ranged_norm = normalize_item_name(best_ranged.get("name"))
            if eq_weapon_norm != best_ranged_norm:
                return {"action": "equip", "item_id": best_ranged.get("id")}
        elif best_melee:
            best_melee_norm = normalize_item_name(best_melee.get("name"))
            if eq_weapon_norm != best_melee_norm:
                return {"action": "equip", "item_id": best_melee.get("id")}

    elif has_ranged_enemy:
        if best_ranged:
            best_ranged_norm = normalize_item_name(best_ranged.get("name"))
            if eq_weapon_norm != best_ranged_norm:
                return {"action": "equip", "item_id": best_ranged.get("id")}
        elif best_melee:
            best_melee_norm = normalize_item_name(best_melee.get("name"))
            if eq_weapon_norm != best_melee_norm:
                return {"action": "equip", "item_id": best_melee.get("id")}

    else:
        if best_melee and best_ranged:
            m_rank = MELEE_RANKS.get(normalize_item_name(best_melee.get("name")), 0)
            r_rank = RANGED_RANKS.get(normalize_item_name(best_ranged.get("name")), 0)
            if m_rank >= r_rank:
                best_weapon = best_melee
            else:
                best_weapon = best_ranged
        else:
            best_weapon = best_melee or best_ranged

        if best_weapon:
            best_weapon_norm = normalize_item_name(best_weapon.get("name"))
            if eq_weapon_norm != best_weapon_norm:
                return {"action": "equip", "item_id": best_weapon.get("id")}

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