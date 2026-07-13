from helpers.game_math import WEAPON_STATS, ARMOR_STATS, RECOVERY_STATS

def _is_smoltz(item_id_or_name: str) -> bool:
    clean = str(item_id_or_name).lower()
    return "smoltz" in clean or "reward1" in clean

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

def is_item_needed(item_id: str, inventory, current_weapon_id, current_armor_id) -> bool:
    if _is_smoltz(item_id):
        return True
        
    name_clean = str(item_id).lower().replace(" ", "_")
    if name_clean in WEAPON_STATS:
        stat = WEAPON_STATS[name_clean]
        w_type = stat["type"]
        atk = stat["atk"]
        
        if w_type == "melee":
            best_melee = score_weapon(current_weapon_id) if current_weapon_id and WEAPON_STATS.get(str(current_weapon_id).lower().replace(" ", "_"), {}).get("type") == "melee" else 0
            for item in inventory:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("typeId") or item.get("name") or item.get("id") or ""
                item_name = str(item_type).lower().replace(" ", "_")
                if WEAPON_STATS.get(item_name, {}).get("type") == "melee":
                    best_melee = max(best_melee, WEAPON_STATS[item_name]["atk"])
            return atk > best_melee
            
        elif w_type == "ranged":
            ranged_in_inv = {}
            if current_weapon_id and WEAPON_STATS.get(str(current_weapon_id).lower().replace(" ", "_"), {}).get("type") == "ranged":
                curr_clean = str(current_weapon_id).lower().replace(" ", "_")
                ranged_in_inv[curr_clean] = WEAPON_STATS[curr_clean]["atk"]
                
            for item in inventory:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("typeId") or item.get("name") or item.get("id") or ""
                item_name = str(item_type).lower().replace(" ", "_")
                if WEAPON_STATS.get(item_name, {}).get("type") == "ranged":
                    ranged_in_inv[item_name] = max(ranged_in_inv.get(item_name, 0), WEAPON_STATS[item_name]["atk"])
            
            if name_clean not in ranged_in_inv:
                return len(ranged_in_inv) < 2
            else:
                return atk > ranged_in_inv[name_clean]
                
    elif name_clean in ARMOR_STATS:
        score = ARMOR_STATS[name_clean]["def"]
        best_armor = score_armor(current_armor_id)
        for item in inventory:
            if not isinstance(item, dict):
                continue
            item_type = item.get("typeId") or item.get("name") or item.get("id") or ""
            item_name = str(item_type).lower().replace(" ", "_")
            if item_name in ARMOR_STATS:
                best_armor = max(best_armor, ARMOR_STATS[item_name]["def"])
        return score > best_armor
        
    elif name_clean in RECOVERY_STATS:
        hp_count = 0
        ep_count = 0
        total_items = 0
        for item in inventory:
            if not isinstance(item, dict):
                continue
            total_items += 1
            item_type = item.get("typeId") or item.get("name") or item.get("id") or ""
            item_name = str(item_type).lower().replace(" ", "_")
            if item_name in RECOVERY_STATS:
                stat = RECOVERY_STATS[item_name]
                if stat["hp"] > 0:
                    hp_count += 1
                if stat["ep"] > 0:
                    ep_count += 1
                    
        if total_items < 10:
            stat = RECOVERY_STATS[name_clean]
            if stat["hp"] > 0:
                return hp_count <= ep_count + 1
            if stat["ep"] > 0:
                return ep_count <= hp_count + 1
                
    return False

def score_ground_item(item_id: str, hp: int, ep: int) -> int:
    if _is_smoltz(item_id):
        return 200
        
    name_clean = str(item_id).lower().replace(" ", "_")
    score = 150
    if name_clean in WEAPON_STATS:
        stat = WEAPON_STATS[name_clean]
        score = 150 + stat["atk"]
    elif name_clean in ARMOR_STATS:
        stat = ARMOR_STATS[name_clean]
        score = 150 + stat["def"]
    elif name_clean in RECOVERY_STATS:
        stat = RECOVERY_STATS[name_clean]
        if stat["hp"] > 0 and hp < 40:
            score = 180
        elif stat["ep"] > 0 and ep <= 2:
            score = 180
        else:
            score = 140
            
    return score

def get_best_loot_action(ground_items, current_inventory, hp, ep, current_weapon_id, current_armor_id):
    if not ground_items:
        return None
        
    inv_count = 0
    has_smoltz_slot = False
    for item in current_inventory:
        if not isinstance(item, dict):
            continue
        item_type = item.get("typeId") or item.get("name") or item.get("id") or ""
        if _is_smoltz(item_type):
            has_smoltz_slot = True
        inv_count += 1
        
    scored_items = []
    for item in ground_items:
        if not isinstance(item, dict):
            continue
        item_name = item.get("name") or item.get("type") or item.get("typeId")
        if not item_name:
            continue
            
        if is_item_needed(item_name, current_inventory, current_weapon_id, current_armor_id):
            score = score_ground_item(item_name, hp, ep)
            scored_items.append((score, item_name, item))
            
    if not scored_items:
        return None
        
    scored_items.sort(key=lambda x: x[0], reverse=True)
    best_score, best_name, best_item = scored_items[0]
    
    if _is_smoltz(best_name) and has_smoltz_slot:
        return {"action": "pickup", "item": best_item, "score": best_score}
        
    if inv_count < 10:
        return {"action": "pickup", "item": best_item, "score": best_score}
        
    return None