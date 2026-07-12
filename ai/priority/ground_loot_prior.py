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

def get_loot_decision(view_data, agent_info, ground_detector):
    view = view_data
    inventory = agent_info.get_inventory()
    equipped = agent_info.get_equipped()

    eq_weapon_item = equipped.get("weapon")
    eq_armor_item = equipped.get("armor")

    eq_weapon_name = get_item_name(eq_weapon_item)
    eq_armor_name = get_item_name(eq_armor_item)
    eq_weapon_id = get_item_id(eq_weapon_item)
    eq_armor_id = get_item_id(eq_armor_item)

    ground_items = ground_detector.visible_items

    current_region = view.get("currentRegion", {}) or {}
    current_region_id = current_region.get("id")

    owned_melee = []
    owned_ranged = []
    owned_armors = []
    seen_ids = set()
    has_binoculars = False
    hp_item_count = 0
    ep_item_count = 0

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
        elif i_name == "binoculars":
            has_binoculars = True
        elif i_name in ("bandage", "medkit"):
            hp_item_count += 1
        elif i_name in ("emergency_food", "energy_drink"):
            ep_item_count += 1

    melee_ranks = sorted([MELEE_RANKS.get(normalize_item_name(w.get("name")), 0) for w in owned_melee if isinstance(w, dict)], reverse=True)
    ranged_ranks = sorted([RANGED_RANKS.get(normalize_item_name(w.get("name")), 0) for w in owned_ranged if isinstance(w, dict)], reverse=True)
    armor_ranks = sorted([ARMOR_RANKS.get(normalize_item_name(a.get("name")), 0) for a in owned_armors if isinstance(a, dict)], reverse=True)

    for item in ground_items:
        if not isinstance(item, dict):
            continue
        if item.get("regionId") != current_region_id:
            continue
        if normalize_item_name(item.get("name")) == "smoltz":
            return {"action": "pickup", "item_id": item.get("id")}

    for item in ground_items:
        if not isinstance(item, dict):
            continue
        if item.get("regionId") != current_region_id:
            continue
        i_name = normalize_item_name(item.get("name"))
        i_id = item.get("id")

        if i_name in MELEE_RANKS:
            g_rank = MELEE_RANKS.get(i_name, 0)
            if len(melee_ranks) < 2:
                return {"action": "pickup", "item_id": i_id}
            else:
                worse_rank = melee_ranks[1]
                if g_rank > worse_rank:
                    return {"action": "pickup", "item_id": i_id}

        elif i_name in RANGED_RANKS:
            g_rank = RANGED_RANKS.get(i_name, 0)
            if len(ranged_ranks) < 2:
                return {"action": "pickup", "item_id": i_id}
            else:
                worse_rank = ranged_ranks[1]
                if g_rank > worse_rank:
                    return {"action": "pickup", "item_id": i_id}

        elif i_name in ARMOR_RANKS:
            g_rank = ARMOR_RANKS.get(i_name, 0)
            if len(armor_ranks) < 1:
                return {"action": "pickup", "item_id": i_id}
            else:
                current_rank = armor_ranks[0]
                if g_rank > current_rank:
                    return {"action": "pickup", "item_id": i_id}

    if len(inventory) < 10:
        for item in ground_items:
            if not isinstance(item, dict):
                continue
            if item.get("regionId") != current_region_id:
                continue
            i_name = normalize_item_name(item.get("name"))
            i_id = item.get("id")

            if i_name == "binoculars":
                if not has_binoculars:
                    return {"action": "pickup", "item_id": i_id}

            elif i_name in ("emergency_food", "energy_drink"):
                return {"action": "pickup", "item_id": i_id}

            elif i_name in ("bandage", "medkit"):
                if hp_item_count < 3 or ep_item_count > 0:
                    return {"action": "pickup", "item_id": i_id}

    connections = current_region.get("connections") or current_region.get("links") or []
    best_adjacent_region = None
    best_loot_name = ""

    for item in ground_items:
        if not isinstance(item, dict):
            continue
        r_id = item.get("regionId")
        if r_id not in connections:
            continue

        i_name = normalize_item_name(item.get("name"))
        is_high_value = False

        if i_name == "smoltz":
            is_high_value = True
        elif i_name in MELEE_RANKS:
            g_rank = MELEE_RANKS.get(i_name, 0)
            if len(melee_ranks) < 2:
                is_high_value = True
            else:
                if g_rank > melee_ranks[1]:
                    is_high_value = True
        elif i_name in RANGED_RANKS:
            g_rank = RANGED_RANKS.get(i_name, 0)
            if len(ranged_ranks) < 2:
                is_high_value = True
            else:
                if g_rank > ranged_ranks[1]:
                    is_high_value = True
        elif i_name in ARMOR_RANKS:
            g_rank = ARMOR_RANKS.get(i_name, 0)
            if len(armor_ranks) < 1:
                is_high_value = True
            else:
                if g_rank > armor_ranks[0]:
                    is_high_value = True

        if is_high_value:
            best_adjacent_region = r_id
            best_loot_name = item.get("name")
            break

    if best_adjacent_region:
        return {
            "action": "move_to_loot",
            "region_id": best_adjacent_region,
            "item_name": best_loot_name
        }

    return None