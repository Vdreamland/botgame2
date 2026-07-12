from src.helper import actions_helper
import ai.strategy as strategy
from ai.strategy.pre_action_safety import is_action_safe

def chase_committed_target(view_data, agent_info, enemy_detector, memory, ep, current_region_id, visible_regions, region_names):
    committed_id = memory.get_target()
    if not committed_id:
        return None

    enemies = enemy_detector.get_alive_agents() + enemy_detector.get_alive_monsters()
    target_info = next((e for e in enemies if e.get("id") == committed_id), None)
    if not target_info or target_info.get("hp", 0) <= 0:
        memory.clear_target()
        return None

    target_zone = target_info.get("zone") or target_info.get("regionId") or target_info.get("region")
    if target_zone != current_region_id:
        if ep >= 3:
            target_reg = next((r for r in visible_regions if r.get("id") == target_zone), None)
            if target_reg:
                is_death = target_reg.get("isDeathZone") or target_reg.get("isDeadZone") or False
                if not is_death:
                    step = strategy.get_next_step(view_data, target_zone)
                    if step:
                        dest_name = region_names.get(step, "Unknown")
                        thought = f"Chasing target! Moving to {dest_name}"
                        action = actions_helper.move_to(step, thought)
                        if is_action_safe(view_data, action, agent_info, enemy_detector):
                            return action
    return None

def hunt_vulnerable_target(view_data, agent_info, enemy_detector, ep, current_region_id, visible_regions, region_names):
    if ep < 3:
        return None

    equipped = agent_info.get_equipped()
    eq_weapon = equipped.get("weapon")
    if not eq_weapon:
        return None

    current_region = view_data.get("currentRegion", {}) or {}
    connections = current_region.get("connections") or current_region.get("links") or []
    regions_map = {r.get("id"): r for r in visible_regions}

    best_hunt_region_id = None
    vulnerable_enemy_name = ""

    for agent in enemy_detector.get_alive_agents():
        t_id = agent.get("id")
        t_name = agent.get("name")
        t_hp = agent.get("hp", 0)
        t_zone = agent.get("zone") or agent.get("regionId") or agent.get("region")
        if t_zone in connections and t_hp <= 25:
            target_reg = regions_map.get(t_zone)
            if target_reg:
                is_death = target_reg.get("isDeathZone") or target_reg.get("isDeadZone") or False
                if not is_death:
                    monsters = target_reg.get("monsters", []) or []
                    has_guardian = False
                    for m in monsters:
                        m_type = m.get("type", "").lower() or m.get("name", "").lower()
                        if "guardian" in m_type:
                            if m.get("alertActive", False):
                                has_guardian = True
                                break
                    if not has_guardian:
                        best_hunt_region_id = t_zone
                        vulnerable_enemy_name = t_name
                        break

    if best_hunt_region_id:
        dest_name = region_names.get(best_hunt_region_id, "Unknown")
        thought = f"Hunting vulnerable target {vulnerable_enemy_name} in {dest_name}"
        action = actions_helper.move_to(best_hunt_region_id, thought)
        if is_action_safe(view_data, action, agent_info, enemy_detector):
            return action

    return None

def roam_and_rest(view_data, agent_info, enemy_detector, memory, current_region_id, region_names):
    current_region = view_data.get("currentRegion", {}) or {}
    connections = current_region.get("connections") or current_region.get("links") or []

    best_roam_id = None
    for r_id in connections:
        dest_name = region_names.get(r_id, "Unknown")
        thought = f"Exploring new region: {dest_name}"
        action = actions_helper.move_to(r_id, thought)
        if is_action_safe(view_data, action, agent_info, enemy_detector):
            if not memory.is_region_visited(r_id):
                memory.add_visited_region(r_id)
                return action
            if best_roam_id is None:
                best_roam_id = r_id

    if best_roam_id:
        dest_name = region_names.get(best_roam_id, "Unknown")
        thought = f"Exploring new region: {dest_name}"
        memory.add_visited_region(best_roam_id)
        return actions_helper.move_to(best_roam_id, thought)

    thought = "No urgent tactical actions. Resting to recover EP"
    return actions_helper.rest(thought)