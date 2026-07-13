from helpers.game_math import WEAPON_STATS, ARMOR_STATS

def score_weapon(weapon_id: str) -> int:
    if not weapon_id:
        return 0
    name_clean = str(weapon_id).lower().replace(" ", "_")
    return WEAPON_STATS.get(name_clean, {}).get("atk", 0)

def score_armor(armor_id: str) -> int:
    if not armor_id:
        return 0
    name_clean = str(armor_id).lower().replace(" ", "_")
    return ARMOR_STATS.get(name_clean, {}).get("def", 0)

def evaluate_equipment(inventory, current_weapon_id, current_armor_id):
    to_equip_weapon = None
    to_equip_armor = None
    to_drop = []
    
    current_weapon_clean = str(current_weapon_id).lower().replace(" ", "_") if current_weapon_id else ""
    current_armor_clean = str(current_armor_id).lower().replace(" ", "_") if current_armor_id else ""
    
    current_weapon_type = WEAPON_STATS.get(current_weapon_clean, {}).get("type") if current_weapon_clean in WEAPON_STATS else None
    
    best_melee_score = score_weapon(current_weapon_id) if current_weapon_type == "melee" else 0
    best_melee_item = None
    
    ranged_items_map = {}
    best_armor_score = score_armor(current_armor_id)
    best_armor_item = None
    
    for item in inventory:
        if not isinstance(item, dict):
            continue
            
        item_type = item.get("typeId") or item.get("name") or item.get("id")
        if not item_type:
            continue
        
        name_clean = str(item_type).lower().replace(" ", "_")
        
        if name_clean in WEAPON_STATS:
            stat = WEAPON_STATS[name_clean]
            if stat["type"] == "melee":
                score = stat["atk"]
                if score > best_melee_score:
                    best_melee_score = score
                    best_melee_item = item
            elif stat["type"] == "ranged":
                if name_clean not in ranged_items_map:
                    ranged_items_map[name_clean] = []
                ranged_items_map[name_clean].append((stat["atk"], item))
                
        elif name_clean in ARMOR_STATS:
            score = ARMOR_STATS[name_clean]["def"]
            if score > best_armor_score:
                best_armor_score = score
                best_armor_item = item
            else:
                to_drop.append(item)
                
    if best_melee_item:
        to_equip_weapon = best_melee_item
        
    for item in inventory:
        if not isinstance(item, dict):
            continue
        item_type = item.get("typeId") or item.get("name") or item.get("id")
        if not item_type:
            continue
        name_clean = str(item_type).lower().replace(" ", "_")
        if name_clean in WEAPON_STATS and WEAPON_STATS[name_clean]["type"] == "melee":
            if item != best_melee_item:
                to_drop.append(item)
                
    ranged_representatives = []
    for r_type, items_list in ranged_items_map.items():
        items_list.sort(key=lambda x: x[0], reverse=True)
        best_of_type_score, best_item = items_list[0]
        ranged_representatives.append((best_of_type_score, best_item))
        for score, item in items_list[1:]:
            to_drop.append(item)
            
    ranged_representatives.sort(key=lambda x: x[0], reverse=True)
    for i, (score, item) in enumerate(ranged_representatives):
        if i < 2:
            item_id = item.get("id") or item.get("typeId")
            if current_weapon_id != item_id:
                to_equip_weapon = item
        else:
            to_drop.append(item)
            
    if best_armor_item:
        to_equip_armor = best_armor_item
        
    return {
        "to_equip_weapon": to_equip_weapon,
        "to_equip_armor": to_equip_armor,
        "to_drop": to_drop
    }