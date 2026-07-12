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

def get_equipment_decision(view_data, agent_info):
    inventory = agent_info.get_inventory()
    resolved = resolve_equipped(view_data, inventory)

    eq_weapon_name = resolved.get("weapon_name")
    eq_armor_name = resolved.get("armor_name")
    eq_weapon_id = resolved.get("weapon_id")
    eq_armor_id = resolved.get("armor_id")

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