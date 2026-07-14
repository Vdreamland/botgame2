from ai.priority.region_loot_prior import is_item_needed

def score_region_movement(region, is_death_zone_pending, hp, is_safe, enemy_count):
    score = 100
    is_dead_zone = region.get("is_death_zone") or region.get("isDeathZone") or False
    if is_dead_zone:
        score -= 2000
    if is_death_zone_pending:
        score -= 1000
    if hp < 40 and not is_safe:
        terrain = str(region.get("terrain", "")).lower()
        if terrain == "cave":
            score += 40
        else:
            score += 20
    if enemy_count > 0:
        if hp < 50:
            score -= 150 * enemy_count
        else:
            score -= 50 * enemy_count
    return score

def get_best_movement_action(connected_regions, visible_regions, pending_deathzones, hp, ep, is_safe, inventory, current_weapon, current_armor, interacted_ids, current_region, visible_agents, visible_monsters, visible_npcs, regions_list=None):
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
        r_id = enemy.get("regionId") or enemy.get("region_id") or enemy.get("location")
        if r_id:
            enemies_by_region[r_id] = enemies_by_region.get(r_id, 0) + 1

    visible_regions_map = {}
    for r in visible_regions:
        if isinstance(r, dict):
            r_id = r.get("id")
            if r_id:
                visible_regions_map[r_id] = r

    # --- Kalkulasi Nilai Proporsional Berbasis Jarak Layer ---
    layer_bonuses = {}
    if regions_list:
        for r_item in regions_list:
            r_id = r_item.get("id")
            layer = r_item.get("layer", 1)
            first_step = r_item.get("first_step")
            
            if not r_id or r_id == current_id or layer <= 0 or not first_step:
                continue
                
            region_detail = visible_regions_map.get(r_id)
            val = 0
            
            # 1. Ruins
            has_ruin = False
            r_name_lower = str(r_item.get("name", "")).lower()
            if "relic" in r_name_lower or "ruin" in r_name_lower or (region_detail and region_detail.get("ruins")):
                ruin_obj = r_item.get("ruins") or (region_detail.get("ruins") if region_detail else None)
                if not ruin_obj or str(ruin_obj.get("status", "")).lower() not in ("cleared", "completed", "finished"):
                    has_ruin = True
            if has_ruin:
                val += 50
                
            # 2. Ground Items & sMoltz
            if region_detail:
                items_in_region = region_detail.get("items", []) or region_detail.get("groundItems", []) or []
                for item in items_in_region:
                    if isinstance(item, dict):
                        item_name = item.get("name") or item.get("type") or item.get("typeId")
                        if item_name:
                            if "smoltz" in item_name.lower():
                                val += 200
                            elif is_item_needed(item_name, inventory, current_weapon, current_armor):
                                val += 20

            # 3. Facilities (Ditambahkan proteksi anti ping-pong loop fasilitas lokal)
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
                                
                            # Cek apakah wilayah kita saat ini sudah memiliki jenis fasilitas yang sama
                            has_local_facility = False
                            curr_interactables = current_region.get("interactables", []) or []
                            for curr_inter in curr_interactables:
                                if isinstance(curr_inter, dict):
                                    curr_type = curr_inter.get("type") or curr_inter.get("name") or curr_inter.get("id")
                                    if curr_type and curr_type.lower().replace(" ", "_") == name_clean:
                                        has_local_facility = True
                                        break
                                        
                            if has_local_facility:
                                # Lewati penambahan bonus jika kita bisa menggunakan fasilitas lokal yang ada di depan mata
                                continue

                            if name_clean == "medical_facility" and hp < 100:
                                val += (30 + (100 - hp) * 2)
                            elif name_clean == "supply_cache":
                                val += 25

            # Akumulasi nilai terbagi jarak layer ke arah region langkah pertama
            layer_bonuses[first_step] = layer_bonuses.get(first_step, 0) + (val / layer)

    scored_regions = []
    for r in connected_regions:
        r_id = r.get("id") if isinstance(r, dict) else r
        is_pending_dead = r_id in pending_deathzones if r_id else False
        enemy_count = enemies_by_region.get(r_id, 0) if r_id else 0
        
        score = score_region_movement(r, is_pending_dead, hp, is_safe, enemy_count)

        if ep < 3 and not is_urgent:
            score -= 1500

        if r_id and r_id in layer_bonuses:
            score += layer_bonuses[r_id]
        else:
            region_detail = visible_regions_map.get(r_id) if r_id else None
            has_ruid = False
            r_name_lower = str(r.get("name", "")).lower()
            if "relic" in r_name_lower or "ruin" in r_name_lower or (region_detail and region_detail.get("ruins")):
                ruin_obj = r.get("ruins") or (region_detail.get("ruins") if region_detail else None)
                if not ruin_obj or str(ruin_obj.get("status", "")).lower() not in ("cleared", "completed", "finished"):
                    has_ruid = True
            if has_ruid:
                score += 50
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
                    score += 20
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
                                score += 30
                            elif name_clean == "supply_cache":
                                score += 25

        scored_regions.append((score, r))

    if not scored_regions:
        return None

    scored_regions.sort(key=lambda x: x[0], reverse=True)
    best_score, best_region = scored_regions[0]

    return {
        "score": best_score,
        "action": {"action": "move", "target": best_region}
    }