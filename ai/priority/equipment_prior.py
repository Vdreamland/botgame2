from helpers.game_math import WEAPON_STATS, ARMOR_STATS

def score_weapon_overall(name_clean: str) -> int:
    """Menghitung kekuatan taktis keseluruhan senjata secara terpadu."""
    if not name_clean:
        return 0
    stat = WEAPON_STATS.get(name_clean)
    if not stat:
        return 0
    score = stat.get("atk", 0)
    # Berikan bobot taktis tambahan untuk senjata Ranged berdasarkan jangkauannya
    if stat.get("type") == "ranged":
        score += stat.get("range", 0) * 5
    return score

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
    
    # Dapatkan skor taktis senjata yang sedang digunakan saat ini
    current_weapon_score = score_weapon_overall(current_weapon_clean)
    best_weapon_score = current_weapon_score
    best_weapon_item = None
    
    # Dapatkan skor armor yang sedang digunakan saat ini
    best_armor_score = score_armor(current_armor_id)
    best_armor_item = None
    
    # 1. Pindai tas untuk mencari senjata atau armor yang mutlak lebih baik dari yang sedang dipakai
    for item in inventory:
        if not isinstance(item, dict):
            continue
            
        item_type = item.get("typeId") or item.get("name") or item.get("id")
        if not item_type:
            continue
            
        name_clean = str(item_type).lower().replace(" ", "_")
        
        # Penilaian senjata terpadu (mencegah oscillation loop)
        if name_clean in WEAPON_STATS:
            score = score_weapon_overall(name_clean)
            if score > best_weapon_score:
                best_weapon_score = score
                best_weapon_item = item
                
        # Penilaian armor
        elif name_clean in ARMOR_STATS:
            score = score_armor(name_clean)
            if score > best_armor_score:
                best_armor_score = score
                best_armor_item = item
        else:
            to_drop.append(item)
            
    # Tentukan item terbaik yang akan dipasang
    if best_weapon_item:
        to_equip_weapon = best_weapon_item
        
    if best_armor_item:
        to_equip_armor = best_armor_item
        
    # 2. Pembersihan Otomatis: Buang senjata/armor yang lebih lemah dari dalam tas agar hemat slot
    keep_weapon_clean = current_weapon_clean
    if best_weapon_item:
        keep_type = best_weapon_item.get("typeId") or best_weapon_item.get("name") or best_weapon_item.get("id")
        keep_weapon_clean = str(keep_type).lower().replace(" ", "_")
        
    keep_armor_clean = current_armor_clean
    if best_armor_item:
        keep_type = best_armor_item.get("typeId") or best_armor_item.get("name") or best_armor_item.get("id")
        keep_armor_clean = str(keep_type).lower().replace(" ", "_")
        
    for item in inventory:
        if not isinstance(item, dict):
            continue
        item_type = item.get("typeId") or item.get("name") or item.get("id")
        if not item_type:
            continue
        name_clean = str(item_type).lower().replace(" ", "_")
        
        if name_clean in WEAPON_STATS:
            if best_weapon_item and item == best_weapon_item:
                continue
            if name_clean == keep_weapon_clean:
                continue
            to_drop.append(item)
            
        elif name_clean in ARMOR_STATS:
            if best_armor_item and item == best_armor_item:
                continue
            if name_clean == keep_armor_clean:
                continue
            to_drop.append(item)
            
    return {
        "to_equip_weapon": to_equip_weapon,
        "to_equip_armor": to_equip_armor,
        "to_drop": to_drop
    }