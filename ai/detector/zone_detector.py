from .deadzone_detector import DeadZoneDetector

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

        from src.helper import TERRAIN_MODS, WEATHER_MODS, UTILITY

        terrain_data = TERRAIN_MODS.get(terrain, {})
        terrain_mod = terrain_data.get("vision", 0)

        weather_data = WEATHER_MODS.get(weather, {})
        weather_mod = weather_data.get("vision", 0)

        has_binoculars = False
        inventory = self.view_data.get("self", {}).get("inventory", [])
        for item in inventory:
            if isinstance(item, dict):
                name = item.get("name", "").lower()
                type_id = item.get("typeId", "").lower()
                if "binoculars" in UTILITY:
                    u_type = UTILITY["binoculars"].get("type", "").lower()
                    if name == u_type or type_id == u_type:
                        has_binoculars = True
                        break

        binoculars_mod = 0
        if has_binoculars and "binoculars" in UTILITY:
            binoculars_mod = UTILITY["binoculars"].get("vision_bonus", 1)

        total_vision = terrain_mod + weather_mod + binoculars_mod
        return f"+{total_vision}" if total_vision > 0 else str(total_vision)

    def detect_zones(self):
        start_id = self.current_region.get("id")
        if not start_id:
            return {}

        distances = self.get_region_distances()
        dead_detector = DeadZoneDetector(self.view_data)

        regions_by_id = {start_id: self.current_region}
        for r in self.visible_regions:
            r_id = r.get("id")
            if r_id:
                regions_by_id[r_id] = r

        layers = {}
        for r_id, dist in distances.items():
            if r_id == start_id:
                continue
            if dist not in layers:
                layers[dist] = []
            reg_data = regions_by_id.get(r_id)
            if reg_data:
                r_name = reg_data.get("name", "Unknown")
                status = dead_detector.get_region_status(reg_data)
                r_display = f"{r_name} [{status}]"
                if r_display not in layers[dist]:
                    layers[dist].append(r_display)

        for dist in layers:
            layers[dist].sort()

        return layers

    def get_region_name_to_id_map(self):
        region_map = {}
        start_id = self.current_region.get("id")
        start_name = self.current_region.get("name")
        if start_name and start_id:
            region_map[start_name] = start_id

        for r in self.visible_regions:
            r_id = r.get("id")
            r_name = r.get("name")
            if r_name and r_id:
                region_map[r_name] = r_id
        return region_map

    def get_region_distances(self):
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
        distances = {start_id: 0}

        while queue:
            curr_id, dist = queue.pop(0)
            curr_reg = regions_by_id.get(curr_id, {})
            conns = curr_reg.get("connections") or curr_reg.get("links") or []
            for neighbor_id in conns:
                if neighbor_id in regions_by_id and neighbor_id not in visited:
                    visited.add(neighbor_id)
                    distances[neighbor_id] = dist + 1
                    queue.append((neighbor_id, dist + 1))
        return distances