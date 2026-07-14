def evaluate_survival(hp, ep, is_safe, current_region, visible_enemies, pending_deathzones, connected_region_ids=None):
    danger_score = 0
    is_dead_zone = current_region.get("is_death_zone") or current_region.get("isDeathZone") or False
    curr_id = current_region.get("id")
    is_pending = curr_id in pending_deathzones if curr_id else False
    
    # 1. Bahaya Mutlak: Death Zone Aktif
    if is_dead_zone:
        danger_score = 100
    # 2. Bahaya Kritis: Pending Death Zone atau Sekarat saat sedang dikepung musuh
    elif is_pending:
        danger_score = 85
    elif hp < 30 and not is_safe:
        danger_score = 95
    # 3. Bahaya Sedang: Dikepung beberapa musuh saat HP menurun
    else:
        enemy_list = visible_enemies.get("current", []) if isinstance(visible_enemies, dict) else []
        enemy_count = len(enemy_list)
        if enemy_count > 0:
            if hp < 50:
                danger_score = 75 + enemy_count * 5
            else:
                danger_score = 40 + enemy_count * 10
        else:
            danger_score = 0
            
    danger_score = min(100, max(0, danger_score))
    should_flee = danger_score >= 80
    
    return {
        "danger_score": danger_score,
        "should_flee": should_flee
    }