from helpers.game_math import WEAPON_STATS, ARMOR_STATS, RECOVERY_STATS

def score_ground_item(item_id: str, hp: int, ep: int) -> int:
    name_clean = str(item_id).lower().replace(" ", "_")
    if name_clean == "smoltz":
        return 100
        
    score = 0
    if name_clean in WEAPON_STATS:
        stat = WEAPON_STATS[name_clean]
        score = 50 + stat["atk"]
    elif name_clean in ARMOR_STATS:
        stat = ARMOR_STATS[name_clean]
        score = 50 + stat["def"]
    elif name_clean in RECOVERY_STATS:
        stat = RECOVERY_STATS[name_clean]
        if stat["hp"] > 0 and hp < 40:
            score = 70
        elif stat["ep"] > 0 and ep <= 2:
            score = 70
        else:
            score = 40
            
    return score

def get_best_loot_action(ground_items, current_inventory, hp, ep):
    if not ground_items:
        return None
        
    inv_count = 0
    has_smoltz_slot = False
    for item in current_inventory:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id") or item.get("typeId")
        if str(item_id).lower() == "smoltz":
            has_smoltz_slot = True
        inv_count += 1
        
    scored_items = []
    for item in ground_items:
        if not isinstance(item, dict):
            continue
        item_name = item.get("name") or item.get("type") or item.get("typeId")
        if not item_name:
            continue
            
        score = score_ground_item(item_name, hp, ep)
        scored_items.append((score, item_name, item))
        
    if not scored_items:
        return None
        
    scored_items.sort(key=lambda x: x[0], reverse=True)
    best_score, best_name, best_item = scored_items[0]
    
    if best_name.lower() == "smoltz" and has_smoltz_slot:
        return {"action": "pickup", "item": best_item, "score": best_score}
        
    if inv_count < 10:
        return {"action": "pickup", "item": best_item, "score": best_score}
        
    return None