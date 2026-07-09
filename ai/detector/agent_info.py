from .zone_detector import ZoneDetector

class AgentInfoDetector:
    def __init__(self, view_data):
        self.view_data = view_data or {}
        self.self_data = self.view_data.get("self", {})
        self.zone_detector = ZoneDetector(self.view_data)

    def get_location(self):
        return self.zone_detector.get_location()

    def get_terrain(self):
        return self.zone_detector.get_terrain()

    def get_weather(self):
        return self.zone_detector.get_weather()

    def get_vision(self):
        return self.zone_detector.get_vision()

    def get_links_count(self):
        return self.zone_detector.get_links_count()

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

    def get_zones(self):
        return self.zone_detector.detect_zones()