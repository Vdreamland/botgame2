class ZoneDetector:
    def __init__(self, view_data):
        self.view_data = view_data or {}
        self.current_region = self.view_data.get("currentRegion", {})
        self.visible_regions = self.view_data.get("visibleRegions", [])

    def get_location(self):
        return self.current_region.get("name", "Unknown")

    def get_terrain(self):
        return self.current_region.get("terrain", "Unknown")

    def get_weather(self):
        return self.current_region.get("weather", "None")

    def get_links_count(self):
        links = self.current_region.get("links") or self.current_region.get("connections")
        if isinstance(links, list):
            return len(links)
        elif isinstance(links, int):
            return links
        return 0

    def get_vision(self):
        terrain = self.get_terrain().lower()
        weather = self.get_weather().lower()

        terrain_mod = 0
        if terrain == "plains":
            terrain_mod = 1
        elif terrain == "hills":
            terrain_mod = 2
        elif terrain == "forest":
            terrain_mod = -1
        elif terrain == "cave":
            terrain_mod = -2

        weather_mod = 0
        if weather == "clear":
            weather_mod = 0
        elif weather == "rain":
            weather_mod = -1
        elif weather == "fog":
            weather_mod = -2
        elif weather == "storm":
            weather_mod = -2

        has_binoculars = False
        inventory = self.view_data.get("self", {}).get("inventory", [])
        for item in inventory:
            if isinstance(item, dict) and item.get("name") == "Binoculars":
                has_binoculars = True
                break

        binoculars_mod = 1 if has_binoculars else 0
        total_vision = terrain_mod + weather_mod + binoculars_mod
        return f"+{total_vision}" if total_vision > 0 else str(total_vision)

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