import asyncio

def get_next_step(view_data, target_id):
    view = view_data
    current_region = view.get("currentRegion", {}) or {}
    start_id = current_region.get("id")

    if not start_id or not target_id:
        return None

    if start_id == target_id:
        return start_id

    visible_regions = view.get("visibleRegions", []) or []
    regions = {start_id: current_region}
    for r in visible_regions:
        if isinstance(r, dict):
            r_id = r.get("id")
            if r_id:
                regions[r_id] = r

    queue = [(start_id, [start_id])]
    visited = {start_id: 0}
    shortest_paths = []
    min_dist = 99999

    while queue:
        curr_id, path = queue.pop(0)
        if len(path) - 1 > min_dist:
            continue
        if curr_id == target_id:
            if len(path) - 1 < min_dist:
                min_dist = len(path) - 1
                shortest_paths = [path]
            elif len(path) - 1 == min_dist:
                shortest_paths.append(path)
            continue

        curr_reg = regions.get(curr_id, {})
        conns = curr_reg.get("connections") or curr_reg.get("links") or []
        for neighbor_id in conns:
            if neighbor_id in regions:
                if neighbor_id not in visited or visited[neighbor_id] == len(path):
                    visited[neighbor_id] = len(path)
                    queue.append((neighbor_id, path + [neighbor_id]))

    if not shortest_paths:
        return None

    best_path = None
    best_score = -9999999

    for path in shortest_paths:
        score = 0
        for node_id in path[1:]:
            r_data = regions.get(node_id, {})
            is_death = r_data.get("isDeathZone") or r_data.get("isDeadZone") or False
            if is_death:
                score -= 1000

            monsters = r_data.get("monsters", []) or []
            agents = r_data.get("agents", []) or []

            has_guardian = False
            for m in monsters:
                m_type = m.get("type", "").lower() or m.get("name", "").lower()
                if "guardian" in m_type:
                    has_guardian = True
                    break
            for a in agents:
                if "guardian" in a.get("name", "").lower():
                    has_guardian = True
                    break

            if has_guardian:
                score -= 1000

            g_items = r_data.get("groundItems", []) or []
            for item in g_items:
                name = item.get("name", "").lower()
                if "smoltz" in name:
                    score += 100
                elif any(k in name for k in ("sword", "katana", "sniper", "plate")):
                    score += 50
                elif any(k in name for k in ("bandage", "medkit", "energy", "food")):
                    score += 20

            interactables = r_data.get("interactables", []) or []
            for fac in interactables:
                if not fac.get("isUsed", False):
                    f_type = fac.get("type")
                    if f_type in ("medical_facility", "supply_cache"):
                        score += 30

            score += len(monsters) * 15
            score -= len(agents) * 40

        if score > best_score:
            best_score = score
            best_path = path

    if best_path and len(best_path) > 1:
        return best_path[1]

    return None