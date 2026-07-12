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

def get_loot_decision(view_data, agent_info, ground_detector):
    equipped = agent_info.get_equipped(view_data)
    inventory = agent_info.get_inventory(view_data)
    ground_items = ground_detector.detect_ground_items(view_data)

    eq_weapon = equipped.get("weapon")
    eq_armor = equipped.get("armor")

    owned_melee = []
    owned_ranged = []
    owned_armors = []

    if eq_weapon and isinstance(eq_weapon, dict):
        w_name = eq_weapon.get("name")
        if w_name in MELEE_RANKS:
            owned_melee.append(eq_weapon)
        elif w_name in RANGED_RANKS:
            owned_ranged.append(eq_weapon)

    if eq_armor and isinstance(eq_armor, dict):
        owned_armors.append(eq_armor)

    for item in inventory:
        if not isinstance(item, dict):
            continue
        i_name = item.get("name")
        if i_name in MELEE_RANKS:
            owned_melee.append(item)
        elif i_name in RANGED_RANKS:
            owned_ranged.append(item)
        elif i_name in ARMOR_RANKS:
            owned_armors.append(item)

    melee_ranks = sorted([MELEE_RANKS.get(w.get("name"), 0) for w in owned_melee], reverse=True)
    ranged_ranks = sorted([RANGED_RANKS.get(w.get("name"), 0) for w in owned_ranged], reverse=True)
    armor_ranks = sorted([ARMOR_RANKS.get(a.get("name"), 0) for a in owned_armors], reverse=True)

    for item in ground_items:
        if not isinstance(item, dict):
            continue
        i_name = item.get("name")
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

    return None