from ai.priority.region_loot_prior import is_item_needed
from helpers.game_math import WEAPON_STATS

def score_region_movement(region, is_death_zone_pending, hp, is_safe, enemy_count):
    score = 50
    is_dead_zone = region.get("is_death_zone") or region.get("isDeathZone") or False
    if is_dead_zone:
        score -= 100
    if is_death_zone_pending:
        score -= 50
    if hp < 40 and not is_safe:
        terrain = str(region.get("terrain", "")).lower()
        if terrain == "cave":
            score += 15
        else:
            score += 5
    if enemy_count > 0:
        if hp < 50:
            score -= 30 * enemy_count
        else:
            score -= 10 * enemy_count
    return max(0, min(100, score))

def get_best_movement_action(connected_regions, visible_regions, pending_deathzones, hp, ep, is_safe, inventory, current_weapon, current_armor, interacted_ids, current_region, visible_agents, visible_monsters, visible_npcs, regions_list=None, alert_active=False):
    if ep < 2 or not connected_regions:
        return None

    current_id = current_region.get("id")
    is_in_dead_zone = current_region.get("is_death_zone") or current_region.get("isDeathZone") or False
    is_in_pending = current_id in pending_deathzones if current_id else False
    is_urgent = is_in_dead_zone or is_in_pending or (hp < 40 and not is_safe)

    enemies_by_region = {}
    for enemy in (visible_agents or []) + (visible_monsters or []) + (visible_npcs or []):
        if not isinstance(enemy, dict):
            continue
        is_enemy_guardian = enemy.get("isGuardian", False) or "guardian" in str(enemy.get("id") or "").lower() or "guardian" in str(enemy.get("name") or "").lower()
        if is_enemy_guardian and not alert_active:
            continue
        r_id = enemy.get("regionId") or enemy.get("region_id") or enemy.get("location")
        if r_id:
            enemies_by_region[r_id] = enemies_by_region.get(r_id, 0) + 1

    visible_regions_map = {}
    for r in visible_regions:
        if isinstance(r, dict):
            r_id = r.get("id")
            if r_id:
                visible_regions_map[r_id] = r

    layer_bonuses = {}
    is_unarmed = not current_weapon or str(current_weapon).lower() == "none" or current_weapon == ""
    
    has_local_weapon = False
    if is_unarmed:
        local_items = current_region.get("items", []) or current_region.get("groundItems", []) or []
        for loc_item in local_items:
            if isinstance(loc_item, dict):
                loc_name = loc_item.get("name") or loc_item.get("type") or loc_item.get("typeId")
                if loc_name and str(loc_name).lower().replace(" ", "_") in WEAPON_STATS:
                    has_local_weapon = True
                    break

    if regions_list:
        for r_item in regions_list:
            r_id = r_item.get("id")
            layer = r_item.get("layer", 1)
            first_step = r_item.get("first_step")
            
            if not r_id or r_id == current_id or layer <= 0 or not first_step:
                continue
                
            region_detail = visible_regions_map.get(r_id)
            val = 0
            
            has_ruin = False
            r_name_lower = str(r_item.get("name", "")).lower()
            if "relic" in r_name_lower or "ruin" in r_name_lower or (region_detail and region_detail.get("ruins")):
                ruin_obj = r_item.get("ruins") or (region_detail.get("ruins") if region_detail else None)
                if not ruin_obj or str(ruin_obj.get("status", "")).lower() not in ("cleared", "completed", "finished", "depleted"):
                    has_ruin = True
            if has_ruin:
                val += 15
                
            if region_detail:
                items_in_region = region_detail.get("items", []) or region_detail.get("groundItems", []) or []
                for item in items_in_region:
                    if isinstance(item, dict):
                        item_name = item.get("name") or item.get("type") or item.get("typeId")
                        if item_name:
                            name_item_clean = str(item_name).lower().replace(" ", "_")
                            if "smoltz" in name_item_clean:
                                val += 40
                            elif name_item_clean in WEAPON_STATS:
                                if is_unarmed:
                                    if not has_local_weapon:
                                        val += 50
                                elif is_item_needed(item_name, inventory, current_weapon, current_armor):
                                    val += 10
                            elif is_item_needed(item_name, inventory, current_weapon, current_armor):
                                val += 10

            if region_detail:
                interactables = region_detail.get("interactables", []) or []
                for inter in interactables:
                    if isinstance(inter, dict):
                        f_type = inter.get("type") or inter.get("name") or inter.get("id")
                        if f_type:
                            name_clean = f_type.lower().replace(" ", "_")
                            t_id = inter.get("id") or inter.get("targetId") or inter.get("facilityId")
                            if t_id and t_id in interacted_ids:
                                continue
                                
                            has_local_facility = False
                            curr_interactables = current_region.get("interactables", []) or []
                            for curr_inter in curr_interactables:
                                if isinstance(curr_inter, dict):
                                    curr_type = curr_inter.get("type") or curr_inter.get("name") or curr_inter.get("id")
                                    if curr_type and curr_type.lower().replace(" ", "_") == name_clean:
                                        has_local_facility = True
                                        break
                                        
                            if has_local_facility:
                                continue

                            if name_clean == "medical_facility" and hp < 100:
                                val += int(20 + (100 - hp) * 0.4)
                            elif name_clean == "supply_cache":
                                val += 15

            layer_bonuses[first_step] = layer_bonuses.get(first_step, 0) + (val / layer)

    scored_regions = []
    for r in connected_regions:
        r_id = r.get("id") if isinstance(r, dict) else r
        is_pending_dead = r_id in pending_deathzones if r_id else False
        enemy_count = enemies_by_region.get(r_id, 0) if r_id else 0
        
        score = score_region_movement(r, is_pending_dead, hp, is_safe, enemy_count)

        if ep < 3 and not is_urgent:
            score -= 50

        if r_id and r_id in layer_bonuses:
            score += layer_bonuses[r_id]
        else:
            region_detail = visible_regions_map.get(r_id) if r_id else None
            has_ruin = False
            r_name_lower = str(r.get("name", "")).lower()
            if "relic" in r_name_lower or "ruin" in r_name_lower or (region_detail and region_detail.get("ruins")):
                ruin_obj = r.get("ruins") or (region_detail.get("ruins") if region_detail else None)
                if not ruin_obj or str(ruin_obj.get("status", "")).lower() not in ("cleared", "completed", "finished", "depleted"):
                    has_ruin = True
            if has_ruin:
                score += 15
            if region_detail:
                items_in_region = region_detail.get("items", []) or region_detail.get("groundItems", []) or []
                has_needed_item = False
                for item in items_in_region:
                    if isinstance(item, dict):
                        item_name = item.get("name") or item.get("type") or item.get("typeId")
                        if item_name and is_item_needed(item_name, inventory, current_weapon, current_armor):
                            has_needed_item = True
                            break
                if has_needed_item:
                    score += 10
                interactables = region_detail.get("interactables", []) or []
                for inter in interactables:
                    if isinstance(inter, dict):
                        f_type = inter.get("type") or inter.get("name") or inter.get("id")
                        if f_type:
                            name_clean = f_type.lower().replace(" ", "_")
                            t_id = inter.get("id") or inter.get("targetId") or inter.get("facilityId")
                            if t_id and t_id in interacted_ids:
                                continue
                            if name_clean == "medical_facility" and hp < 100:
                                score += 20
                            elif name_clean == "supply_cache":
                                score += 15

        score = min(85, max(0, score))
        scored_regions.append((score, r))

    if not scored_regions:
        return None

    scored_regions.sort(key=lambda x: x[0], reverse=True)
    best_score, best_region = scored_regions[0]

    return {
        "score": best_score,
        "action": {"action": "move", "target": best_region}
    }