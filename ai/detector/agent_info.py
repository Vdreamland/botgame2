class AgentInfoDetector:
    def __init__(self, view_data):
        self.view_data = view_data or {}
        self.self_data = self.view_data.get("self", {})
        self.current_region = self.view_data.get("currentRegion", {})

    def get_location(self):
        return self.current_region.get("name", "Unknown")

    def get_terrain(self):
        return self.current_region.get("terrain", "Unknown")

    def get_weather(self):
        return self.current_region.get("weather", "None")

    def get_vision(self):
        return self.current_region.get("vision", 0)

    def get_links_count(self):
        links = self.current_region.get("links")
        if isinstance(links, list):
            return len(links)
        elif isinstance(links, int):
            return links
        return 0

    def get_hp(self):
        return self.self_data.get("hp", 0)

    def get_max_hp(self):
        return self.self_data.get("maxHp", 0)

    def get_ep(self):
        return self.self_data.get("ep", 0)

    def get_max_ep(self):
        return self.self_data.get("maxEp", 0)

    def get_atk(self):
        return self.self_data.get("atk", 0)

    def get_def(self):
        return self.self_data.get("def", 0)

    def get_kills(self):
        return self.self_data.get("kills", 0)

    def get_equipped(self):
        return self.self_data.get("equipment", {})

    def get_inventory(self):
        return self.self_data.get("inventory", [])

    def get_max_inventory(self):
        return self.self_data.get("maxInventory", 10)