class GroundItemDetector:
    def __init__(self, view_data):
        self.view_data = view_data or {}
        self.visible_items = []
        
        current_region = self.view_data.get("currentRegion", {})
        if isinstance(current_region, dict):
            r_id = current_region.get("id")
            items = current_region.get("items")
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and r_id:
                        item["regionId"] = r_id
                        self.visible_items.append(item)
                        
        for reg in self.view_data.get("visibleRegions", []):
            if isinstance(reg, dict):
                r_id = reg.get("id")
                items = reg.get("items")
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and r_id:
                            item["regionId"] = r_id
                            self.visible_items.append(item)

    def get_items_by_region(self):
        items_by_reg = {}
        for item in self.visible_items:
            if not isinstance(item, dict):
                continue
            r_id = item.get("regionId") or item.get("region")
            if not r_id:
                continue
            if r_id not in items_by_reg:
                items_by_reg[r_id] = []
            items_by_reg[r_id].append(item)
        return items_by_reg

    def get_formatted_items_by_layer(self, region_distances):
        region_id_to_name = {
            self.view_data.get("currentRegion", {}).get("id"): self.view_data.get("currentRegion", {}).get("name", "Unknown")
        }
        for r in self.view_data.get("visibleRegions", []):
            r_id = r.get("id")
            r_name = r.get("name")
            if r_id and r_name:
                region_id_to_name[r_id] = r_name

        items_by_reg = self.get_items_by_region()
        layer_map = {}

        for r_id, items in items_by_reg.items():
            dist = region_distances.get(r_id)
            if dist is not None:
                if dist not in layer_map:
                    layer_map[dist] = {}
                
                r_name = region_id_to_name.get(r_id, "Unknown")
                grouped = {}
                for item in items:
                    name = item.get("name", "Unknown")
                    qty = item.get("quantity", 1)
                    grouped[name] = grouped.get(name, 0) + qty
                
                items_str_list = [f"{name} [{qty}]" for name, qty in sorted(grouped.items())]
                layer_map[dist][r_name] = ", ".join(items_str_list)
        
        return layer_map