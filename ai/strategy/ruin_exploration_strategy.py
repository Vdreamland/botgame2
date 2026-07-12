def get_best_ruin_target(view_data):
    view = view_data
    current_region = view.get("currentRegion", {}) or {}
    start_id = current_region.get("id")

    if not start_id:
        return None

    visible_regions = view.get("visibleRegions", []) or []
    regions = {start_id: current_region}
    for r in visible_regions:
        if isinstance(r, dict):
            r_id = r.get("id")
            if r_id:
                regions[r_id] = r

    my_id = view.get("self", {}).get("id")
    candidates = []

    for r_id, r in regions.items():
        is_ruin = r.get("isRuin") or r.get("name", "").startswith("S:")
        is_empty = r.get("isEmpty", False)
        occupant = r.get("ruinOccupant")

        if is_ruin and not is_empty:
            if not occupant or occupant == my_id:
                candidates.append(r)

    if not candidates:
        return None

    best_target_id = None
    min_dist = 99999

    for cand in candidates:
        target_id = cand.get("id")
        if start_id == target_id:
            return target_id

        queue = [(start_id, 0)]
        visited = {start_id}
        dist = 99999

        while queue:
            curr_id, d = queue.pop(0)
            if curr_id == target_id:
                dist = d
                break

            curr_reg = regions.get(curr_id, {})
            conns = curr_reg.get("connections") or curr_reg.get("links") or []
            for neighbor_id in conns:
                if neighbor_id in regions and neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, d + 1))

        if dist < min_dist:
            min_dist = dist
            best_target_id = target_id

    return best_target_id