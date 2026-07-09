class DeadZoneDetector:
    def __init__(self, view_data):
        self.view_data = view_data or {}

    def get_region_status(self, region_data):
        if not isinstance(region_data, dict):
            return "SafeZone"
        is_death = region_data.get("isDeathZone") or region_data.get("isDeadZone") or False
        return "DeadZone" if is_death else "SafeZone"