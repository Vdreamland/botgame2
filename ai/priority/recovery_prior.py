from helpers.game_math import RECOVERY_STATS

def score_recovery_actions(hp: int, ep: int, inventory, is_safe: bool):
    best_action = None
    best_score = 0
    
    hp_items = []
    ep_items = []
    
    for item in inventory:
        if not isinstance(item, dict):
            continue
        item_type = item.get("typeId") or item.get("name") or item.get("id")
        if not item_type:
            continue
        name_clean = str(item_type).lower().replace(" ", "_")
        if name_clean in RECOVERY_STATS:
            stat = RECOVERY_STATS[name_clean]
            if stat["hp"] > 0:
                hp_items.append((stat["hp"], item))
            if stat["ep"] > 0:
                ep_items.append((stat["ep"], item))
                
    if hp < 80 and hp_items:
        score = 40 + (100 - hp)
        if hp < 40:
            score += 30
        if score > best_score:
            best_score = score
            hp_items.sort(key=lambda x: x[0], reverse=True)
            best_action = {"action": "use_item", "item": hp_items[0][1]}
            
    if ep <= 2 and ep_items:
        score = 85 + (10 - ep) * 5
        if score > best_score:
            best_score = score
            ep_items.sort(key=lambda x: x[0], reverse=True)
            best_action = {"action": "use_item", "item": ep_items[0][1]}
            
    if ep in (3, 4) and ep_items and is_safe:
        score = 60
        if score > best_score:
            best_score = score
            ep_items.sort(key=lambda x: x[0], reverse=True)
            best_action = {"action": "use_item", "item": ep_items[0][1]}
            
    if ep in (4, 5, 6, 7) and is_safe:
        score = 50
        if score > best_score:
            best_score = score
            best_action = {"action": "rest"}
            
    if ep == 0 and is_safe and not ep_items:
        score = 40
        if score > best_score:
            best_score = score
            best_action = {"action": "rest"}
            
    return {
        "score": best_score,
        "action": best_action
    }