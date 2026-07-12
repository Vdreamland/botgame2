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

def resolve_equipped(view_data, inventory):
    self_data = view_data.get("self", {}) or {}
    equipped_dict = self_data.get("equipped")

    eq_weapon_raw = None
    eq_armor_raw = None

    if isinstance(equipped_dict, dict):
        eq_weapon_raw = equipped_dict.get("weapon")
        eq_armor_raw = equipped_dict.get("armor")
    else:
        eq_weapon_raw = self_data.get("equippedWeapon")
        eq_armor_raw = self_data.get("equippedArmor")

    eq_weapon_name = ""
    eq_armor_name = ""

    if eq_weapon_raw:
        if isinstance(eq_weapon_raw, dict):
            eq_weapon_name = eq_weapon_raw.get("name", "")
        else:
            eq_weapon_name = str(eq_weapon_raw)

    if eq_armor_raw:
        if isinstance(eq_armor_raw, dict):
            eq_armor_name = eq_armor_raw.get("name", "")
        else:
            eq_armor_name = str(eq_armor_raw)

    eq_weapon_id = None
    eq_armor_id = None

    if eq_weapon_name:
        for item in inventory:
            if isinstance(item, dict) and normalize_item_name(item.get("name")) == normalize_item_name(eq_weapon_name):
                eq_weapon_id = item.get("id")
                break

    if eq_armor_name:
        for item in inventory:
            if isinstance(item, dict) and normalize_item_name(item.get("name")) == normalize_item_name(eq_armor_name):
                eq_armor_id = item.get("id")
                break

    return {
        "weapon_name": eq_weapon_name,
        "armor_name": eq_armor_name,
        "weapon_id": eq_weapon_id,
        "armor_id": eq_armor_id
    }

def get_loot_decision(view_data, agent_info, ground_detector):
    view = view_data
    inventory = agent_info.get_inventory()
    resolved = resolve_equipped(view_data, inventory)

    eq_weapon_name = resolved.get("weapon_name")
    eq_armor_name = resolved.get("armor_name")
    eq_weapon_id = resolved.get("weapon_id")
    eq_armor_id = resolved.get("armor_id")

    ground_items = ground_detector.visible_items

    current_region = view.get("currentRegion", {}) or {}
    current_region_id = current_region.get("id")

    owned_melee = []
    owned_ranged = []
    owned_armors = []
    has_binoculars = False
    hp_item_count = 0
    ep_item_count = 0

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

        if i_name in MELEE_RANKS or i_name in RANGED_RANKS or i_name in ARMOR_RANKS:
            already_owned = False
            for w in owned_melee + owned_ranged + owned_armors:
                if isinstance(w, dict) and normalize_item_name(w.get("name")) == i_name:
                    already_owned = True
                    break
            if already_owned:
                continue

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
        elif i_name in MELEE_RANKS or i_name in RANGED_RANKS or i_name in ARMOR_RANKS:
            already_owned = False
            for w in owned_melee + owned_ranged + owned_armors:
                if isinstance(w, dict) and normalize_item_name(w.get("name")) == i_name:
                    already_owned = True
                    break
            if already_owned:
                continue

        if i_name in MELEE_RANKS:
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