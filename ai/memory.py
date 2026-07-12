class AgentMemory:
    def __init__(self, bot_name):
        self.bot_name = bot_name
        self.visited_regions = set()
        self.last_target_id = None
        self.used_facility_ids = set()

    def add_visited_region(self, region_id):
        self.visited_regions.add(region_id)

    def is_region_visited(self, region_id):
        return region_id in self.visited_regions

    def set_target(self, target_id):
        self.last_target_id = target_id

    def get_target(self):
        return self.last_target_id

    def clear_target(self):
        self.last_target_id = None

    def mark_facility_used(self, facility_id):
        self.used_facility_ids.add(facility_id)

    def is_facility_used(self, facility_id):
        return facility_id in self.used_facility_ids

    def reset_memory(self):
        self.visited_regions.clear()
        self.last_target_id = None
        self.used_facility_ids.clear()