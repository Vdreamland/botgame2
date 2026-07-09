class ZoneDetector:
    def __init__(self, view_data):
        self.view_data = view_data or {}
        self.current_region = self.view_data.get("currentRegion", {})
        self.visible_regions = self.view_data.get("visibleRegions", [])

    def detect_zones(self):
        start_id = self.current_region.get("id")
        if not start_id:
            return {}

        regions_by_id = {start_id: self.current_region}
        for r in self.visible_regions:
            r_id = r.get("id")
            if r_id:
                regions_by_id[r_id] = r

        queue = [(start_id, 0)]
        visited = {start_id}
        layers = {}

        while queue:
            curr_id, dist = queue.pop(0)
            if curr_id != start_id:
                if dist not in layers:
                    layers[dist] = []
                r_name = regions_by_id[curr_id].get("name", "Unknown")
                if r_name not in layers[dist]:
                    layers[dist].append(r_name)

            curr_reg = regions_by_id.get(curr_id, {})
            conns = curr_reg.get("connections") or curr_reg.get("links") or []
            for neighbor_id in conns:
                if neighbor_id in regions_by_id and neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, dist + 1))

        for dist in layers:
            layers[dist].sort()

        return layers