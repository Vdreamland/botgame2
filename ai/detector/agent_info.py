from .zone_detector import ZoneDetector
from .deadzone_detector import DeadZoneDetector
from .enemy_info import EnemyInfoDetector

class AgentInfoDetector:
    def __init__(self, view_data):
        self.view_data = view_data or {}
        self.self_data = self.view_data.get("self", {})
        self.zone_detector = ZoneDetector(self.view_data)
        self.deadzone_detector = DeadZoneDetector(self.view_data)
        self.enemy_detector = EnemyInfoDetector(self.view_data)

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
        eq_weapon = self.self_data.get("equippedWeapon") or self.self_data.get("weapon")
        eq_armor = self.self_data.get("equippedArmor") or self.self_data.get("armor")
        
        equipped = {}
        if eq_weapon:
            equipped["weapon"] = eq_weapon
        if eq_armor:
            equipped["armor"] = eq_armor
            
        if not equipped and "equipment" in self.self_data:
            equipped = self.self_data.get("equipment", {})
            
        return equipped

    def get_inventory(self):
        return self.self_data.get("inventory", [])

    def get_max_inventory(self):
        return self.self_data.get("maxInventory", 10)

    def get_zones(self):
        return self.zone_detector.detect_zones()

    def get_current_zone_status(self):
        return self.deadzone_detector.get_region_status(self.zone_detector.current_region)

    def get_current_region_id(self):
        return self.current_region.get("id", "")

    def get_region_name_to_id_map(self):
        return self.zone_detector.get_region_name_to_id_map()

    def get_enemy_logs(self):
        distances = self.zone_detector.get_region_distances()
        enemies_map = self.enemy_detector.get_enemies_by_layer(distances)
        
        if not enemies_map:
            return []
        
        log_lines = ["Enemy Info :"]
        first_block = True
        for dist in sorted(enemies_map.keys()):
            for r_name, enemy_list in enemies_map[dist].items():
                if not first_block:
                    log_lines.append("")
                else:
                    first_block = False
                log_lines.append(f"{r_name} :")
                for enemy_str in enemy_list:
                    log_lines.append(enemy_str)
        return log_lines