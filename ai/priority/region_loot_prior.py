from helpers.game_math import WEAPON_STATS, ARMOR_STATS, RECOVERY_STATS

def _is_smoltz(item_id_or_name):
    if not item_id_or_name:
        return False
    name_clean = str(item_id_or_name).lower()
    return "smoltz" in name_clean or "moltz" in name_clean

def score_weapon(weapon_id):
    if not weapon_id:
        return 0
    name_clean = str(weapon_id).lower().replace(" ", "_")
    stat = WEAPON_STATS.get(name_clean)
    if stat:
        return stat.get("atk", 0)
    return 0

def score_armor(armor_id):
    if not armor_id:
        return 0
    name_clean = str(armor_id).lower().replace(" ", "_")
    stat = ARMOR_STATS.get(name_clean)
    if stat:
        return stat.get("def", 0)
    return 0

def is_item_needed(item_name, inventory, current_weapon_id, current_armor_id):
    if not item_name:
        return False
    
    if _is_smoltz(item_name):
        return True

    name_clean = str(item_name).lower().replace(" ", "_")
    
    # 1. Deteksi Kebutuhan Teropong (Binoculars)
    if "binocular" in name_clean:
        has_binoc = False
        for inv_item in inventory:
            if not isinstance(inv_item, dict):
                continue
            inv_type = inv_item.get("type") or inv_item.get("typeId") or inv_item.get("name") or inv_item.get("id")
            if inv_type and "binocular" in str(inv_type).lower():
                has_binoc = True
                break
        return not has_binoc

    # 2. Penilaian Senjata (Sistem Backup Melee + Ranged)
    if name_clean in WEAPON_STATS:
        target_stat = WEAPON_STATS[name_clean]
        target_type = target_stat.get("type")
        target_atk = target_stat.get("atk", 0)
        
        curr_atk = score_weapon(current_weapon_id)
        curr_clean = str(current_weapon_id).lower().replace(" ", "_") if current_weapon_id else ""
        curr_stat = WEAPON_STATS.get(curr_clean, {})
        curr_type = curr_stat.get("type")
        
        # Jika tipe senjata sama (sama-sama Melee atau Ranged), bandingkan ATK
        if target_type == curr_type:
            if target_atk > curr_atk:
                return True
                
        # Jika tipe berbeda (misal kita pegang Ranged, tapi di tanah ada Melee), 
        # izinkan ambil jika di tas belum ada senjata kategori tersebut sebagai backup.
        has_type_in_inv = False
        if curr_type == target_type:
            has_type_in_inv = True
        else:
            for inv_item in inventory:
                if not isinstance(inv_item, dict):
                    continue
                inv_type = inv_item.get("type") or inv_item.get("typeId") or inv_item.get("name") or inv_item.get("id")
                if inv_type:
                    inv_clean = str(inv_type).lower().replace(" ", "_")
                    if inv_clean in WEAPON_STATS:
                        if WEAPON_STATS[inv_clean].get("type") == target_type:
                            has_type_in_inv = True
                            break
                            
        if not has_type_in_inv:
            return True
            
        return False

    # 3. Armor
    if name_clean in ARMOR_STATS:
        target_def = ARMOR_STATS[name_clean].get("def", 0)
        curr_def = score_armor(current_armor_id)
        if target_def > curr_def:
            return True
        # Periksa armor di inventaris
        for inv_item in inventory:
            if not isinstance(inv_item, dict):
                continue
            inv_type = inv_item.get("type") or inv_item.get("typeId") or inv_item.get("name") or inv_item.get("id")
            if inv_type:
                inv_clean = str(inv_type).lower().replace(" ", "_")
                if inv_clean in ARMOR_STATS:
                    inv_def = ARMOR_STATS[inv_clean].get("def", 0)
                    if inv_def >= target_def:
                        return False
        return True

    # 4. Recovery items
    if name_clean in RECOVERY_STATS:
        if len(inventory) >= 10:
            return False
            
        hp_count = 0
        ep_count = 0
        for inv_item in inventory:
            if not isinstance(inv_item, dict):
                continue
            inv_type = inv_item.get("type") or inv_item.get("typeId") or inv_item.get("name") or inv_item.get("id")
            if not inv_type:
                continue
            inv_clean = str(inv_type).lower()
            if "medkit" in inv_clean or "bandage" in inv_clean or "food" in inv_clean:
                hp_count += 1
            elif "drink" in inv_clean or "potion" in inv_clean:
                ep_count += 1

        is_hp_item = "medkit" in name_clean or "bandage" in name_clean or "food" in name_clean
        is_ep_item = "drink" in name_clean or "potion" in name_clean

        if is_hp_item and hp_count < 3:
            return True
        if is_ep_item and ep_count < 2:
            return True

    return False

def score_ground_item(item_name, hp, ep, current_inventory, current_weapon_id, current_armor_id):
    if not item_name:
        return 0

    if _is_smoltz(item_name):
        return 200

    name_clean = str(item_name).lower().replace(" ", "_")
    
    # Deteksi status tangan kosong (unarmed)
    is_unarmed = not current_weapon_id or str(current_weapon_id).lower() == "none" or current_weapon_id == ""

    # 1. Teropong (Binoculars)
    if "binocular" in name_clean:
        return 130

    # 2. Weapon
    if name_clean in WEAPON_STATS:
        atk_val = WEAPON_STATS[name_clean].get("atk", 0)
        score = 150 + atk_val
        if is_unarmed:
            score += 150
        return score

    # 3. Armor
    if name_clean in ARMOR_STATS:
        def_val = ARMOR_STATS[name_clean].get("def", 0)
        return 150 + def_val

    # 4. Recovery Items
    if name_clean in RECOVERY_STATS:
        return 120

    return 50

def get_best_loot_action(ground_items, current_inventory, hp, ep, current_weapon_id, current_armor_id):
    if len(current_inventory) >= 10 or not ground_items:
        return None

    scored_items = []
    for item in ground_items:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        item_name = item.get("name") or item.get("type") or item.get("typeId") or item_id

        if item_name and is_item_needed(item_name, current_inventory, current_weapon_id, current_armor_id):
            score = score_ground_item(item_name, hp, ep, current_inventory, current_weapon_id, current_armor_id)
            scored_items.append((score, item))

    if not scored_items:
        return None

    scored_items.sort(key=lambda x: x[0], reverse=True)
    best_score, best_item = scored_items[0]

    return {
        "score": best_score,
        "item": best_item
    }