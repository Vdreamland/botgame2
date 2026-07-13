def evaluate_survival(hp, ep, is_safe, current_region, visible_enemies, pending_deathzones):
    danger_score = 0
    should_flee = False
    
    current_id = current_region.get("id")
    is_in_dead_zone = current_region.get("is_death_zone") or current_region.get("isDeathZone") or False
    is_in_pending = current_id in pending_deathzones if current_id else False
    
    if hp < 40:
        danger_score += 60
        if not is_safe:
            danger_score += 40
            should_flee = True
            
    if is_in_dead_zone:
        danger_score += 150
        should_flee = True
    elif is_in_pending:
        danger_score += 100
        should_flee = True
        
    enemy_count = 0
    for r_name, enemies in visible_enemies.items():
        enemy_count += len(enemies)
        
    if enemy_count > 1 and hp < 60:
        danger_score += 30
        should_flee = True
        
    return {
        "score": danger_score,
        "should_flee": should_flee
    }