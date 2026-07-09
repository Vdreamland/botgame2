class FacilityDetector:
    def __init__(self, view_data):
        self.view_data = view_data or {}
        self.visible_facilities = []

        added_pairs = set()

        def add_fac(fac_dict, r_id):
            if not isinstance(fac_dict, dict) or not r_id:
                return
            f_type = fac_dict.get("type") or fac_dict.get("name")
            if not f_type:
                return
            pair = (r_id, f_type)
            if pair not in added_pairs:
                added_pairs.add(pair)
                
                is_used = fac_dict.get("isUsed", False)
                status = "Used" if is_used else "Ready"
                
                self.visible_facilities.append({
                    "type": f_type,
                    "regionId": r_id,
                    "status": status,
                    "name": fac_dict.get("name", f_type)
                })

        current_region = self.view_data.get("currentRegion", {})
        if isinstance(current_region, dict):
            r_id = current_region.get("id")
            interactables = current_region.get("interactables")
            if isinstance(interactables, list):
                for fac in interactables:
                    add_fac(fac, r_id)

        for reg in self.view_data.get("visibleRegions", []):
            if isinstance(reg, dict):
                r_id = reg.get("id")
                interactables = reg.get("interactables")
                if isinstance(interactables, list):
                    for fac in interactables:
                        add_fac(fac, r_id)

    def get_facilities_by_region(self):
        fac_by_reg = {}
        for fac in self.visible_facilities:
            if not isinstance(fac, dict):
                continue
            r_id = fac.get("regionId") or fac.get("region")
            if not r_id:
                continue
            if r_id not in fac_by_reg:
                fac_by_reg[r_id] = []
            fac_by_reg[r_id].append(fac)
        return fac_by_reg

    def get_formatted_facilities_by_layer(self, region_distances):
        region_id_to_name = {
            self.view_data.get("currentRegion", {}).get("id"): self.view_data.get("currentRegion", {}).get("name", "Unknown")
        }
        for r in self.view_data.get("visibleRegions", []):
            r_id = r.get("id")
            r_name = r.get("name")
            if r_id and r_name:
                region_id_to_name[r_id] = r_name

        fac_by_reg = self.get_facilities_by_region()
        layer_map = {}

        for r_id, facs in fac_by_reg.items():
            dist = region_distances.get(r_id)
            if dist is not None:
                if dist not in layer_map:
                    layer_map[dist] = {}
                
                r_name = region_id_to_name.get(r_id, "Unknown")
                fac_str_list = []
                for fac in facs:
                    f_type = fac.get("type") or fac.get("name") or "facility"
                    f_name = f_type.replace("_", " ").title()
                    status = fac.get("status", "Ready")
                    if status == "Used":
                        fac_str_list.append(f"{f_name} [Already Used]")
                    else:
                        fac_str_list.append(f_name)
                
                layer_map[dist][r_name] = ", ".join(sorted(fac_str_list))
        return layer_map