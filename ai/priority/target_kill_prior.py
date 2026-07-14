import math
from helpers.game_math import WEAPON_STATS, WeatherType, calculate_damage

def score_targets(visible_enemies, hp, ep, current_weapon_id, inventory, self_atk, self_def, weather, last_target_id, connected_region_ids=None, region_layers=None, should_flee=False, current_region_id=None):
    best_action = None
    best_score = 0
    best_target_id = None

    if ep < 1 or not visible_enemies:
        return {
            "score": 0,
            "action": None,
            "target_id": None
        }

    current_weapon_clean = str(current_weapon_id).lower().replace(" ", "_") if current_weapon_id else "fist"
    current_wpn_stat = WEAPON_STATS.get(current_weapon_clean, WEAPON_STATS["fist"])
    current_range = current_wpn_stat["range"]
    current_wpn_atk = current_wpn_stat["atk"]

    best_weapon_in_inv = None
    best_weapon_atk = current_wpn_atk
    best_weapon_range = current_range

    for item in inventory:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type") or item.get("typeId") or item.get("name") or item.get("id")
        if not item_type:
            continue
        name_clean = str(item_type).lower().replace(" ", "_")
        if name_clean in WEAPON_STATS:
            stat = WEAPON_STATS[name_clean]
            if stat["atk"] > best_weapon_atk:
                best_weapon_atk = stat["atk"]
                best_weapon_in_inv = item
                best_weapon_range = stat["range"]

    try:
        weather_enum = WeatherType(str(weather).lower())
    except ValueError:
        weather_enum = WeatherType.CLEAR

    for r_id_key, enemies_list in visible_enemies.items():
        # Memperbaiki deteksi regional agar sinkron dengan ID asli dari decision_maker
        is_current_region = False
        if str(r_id_key).lower() == "current" or r_id_key == "":
            is_current_region = True
        elif current_region_id and str(r_id_key).lower() == str(current_region_id).lower():
            is_current_region = True
        
        # Penentuan Layer Jarak
        layer = 1
        if not is_current_region:
            if region_layers and r_id_key in region_layers:
                layer = region_layers[r_id_key]
            else:
                if connected_region_ids is not None and r_id_key not in connected_region_ids:
                    continue

        for enemy in enemies_list:
            if not isinstance(enemy, dict):
                continue

            enemy_id = enemy.get("id") or enemy.get("agentId") or enemy.get("monsterId") or enemy.get("npcId")
            if not enemy_id:
                continue

            is_guardian = enemy.get("isGuardian", False)
            is_player = not is_guardian and (enemy.get("isAI") is not None or "player" in str(enemy_id).lower())

            enemy_hp = enemy.get("hp", 100)
            enemy_atk = enemy.get("atk", 15)
            enemy_def = enemy.get("def", 5)

            name_clean = str(enemy.get("name") or "").lower()
            if "wolf" in name_clean:
                enemy_atk = 15
                enemy_def = 1
            elif "bear" in name_clean:
                enemy_atk = 12
                enemy_def = 3
            elif "bandit" in name_clean:
                enemy_atk = 25
                enemy_def = 5
            elif is_guardian:
                enemy_atk = 12
                enemy_def = 120

            my_dmg = calculate_damage(self_atk, current_wpn_atk, enemy_def, weather_enum)
            target_dmg = calculate_damage(enemy_atk, 0, self_def, weather_enum)

            total_target_dmg = target_dmg
            if is_current_region:
                other_enemies = [e for e in enemies_list if (e.get("id") or e.get("agentId") or e.get("monsterId") or e.get("npcId")) != enemy_id]
                for other in other_enemies:
                    o_atk = other.get("atk", 15)
                    o_name = str(other.get("name") or "").lower()
                    if "wolf" in o_name:
                        o_atk = 15
                    elif "bear" in o_name:
                        o_atk = 12
                    elif "bandit" in o_name:
                        o_atk = 25
                    total_target_dmg += calculate_damage(o_atk, 0, self_def, weather_enum)

            turns_to_kill = math.ceil(enemy_hp / my_dmg) if my_dmg > 0 else 999
            turns_to_die = math.ceil(hp / total_target_dmg) if total_target_dmg > 0 else 999

            is_suicide = turns_to_kill >= turns_to_die or (hp < 30 and total_target_dmg >= hp)

            score = 0
            if is_player:
                score = 210
            elif is_guardian:
                score = 160
            else:
                score = 190

            if enemy_hp < self_atk + current_wpn_atk:
                score += 40
            elif enemy_hp < 50:
                score += 20

            if turns_to_kill == 1 and not is_suicide:
                score += 100

            if enemy_id == last_target_id:
                score += 30

            if is_suicide:
                score -= 1000

            # Menerapkan Penalti Jarak Layer Musuh
            if layer > 1:
                score -= (layer - 1) * 35

            # Penyelamat Taktis: Tekan skor tempur jika bot dalam kondisi wajib kabur
            if should_flee and turns_to_kill > 1:
                score -= 500

            if score > best_score and score > 0:
                best_score = score
                best_target_id = enemy_id

                if is_current_region:
                    if best_weapon_in_inv and best_weapon_atk > current_wpn_atk:
                        best_action = {"action": "equip", "item": best_weapon_in_inv}
                    else:
                        best_action = {"action": "attack", "target": enemy}
                else:
                    # Memperbaiki verifikasi jangkauan tembak terhadap jarak layer musuh (Anti-Stuck Loop)
                    if current_range >= layer:
                        best_action = {"action": "attack", "target": enemy}
                    else:
                        best_action = {"action": "move_to_enemy", "target": enemy, "region_id": r_id_key}

    return {
        "score": best_score,
        "action": best_action,
        "target_id": best_target_id
    }