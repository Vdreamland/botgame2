class FacilityDetector:
    def __init__(self, view_data):
        self.view_data = view_data or {}
        self.visible_facilities = []
        
        import sys
        import json

        added_pairs = set()

        def add_fac(fac_dict, r_id):
            if not isinstance(fac_dict, dict) or not r_id:
                return
            f_type = fac_dict.get("type") or fac_dict.get("name") or "facility"
            pair = (r_id, f_type)
            if pair not in added_pairs:
                added_pairs.add(pair)
                fac_dict["regionId"] = r_id
                self.visible_facilities.append(fac_dict)

        def parse_fac_data(data, r_id):
            if not data or not r_id:
                return
            if isinstance(data, str):
                add_fac({"type": data, "status": "Ready"}, r_id)
            elif isinstance(data, dict):
                add_fac(data, r_id)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, str):
                        add_fac({"type": item, "status": "Ready"}, r_id)
                    elif isinstance(item, dict):
                        add_fac(item, r_id)

        current_region = self.view_data.get("currentRegion", {})
        print(f"[FACILITY_DEBUG] currentRegion: {json.dumps(current_region)}", file=sys.stderr)
        
        visible_regions = self.view_data.get("visibleRegions", [])
        for r in visible_regions:
            print(f"[FACILITY_DEBUG] visibleRegion {r.get('id')}: {json.dumps(r)}", file=sys.stderr)

        if isinstance(current_region, dict):
            r_id = current_region.get("id")
            if r_id:
                for key in ["facilities", "facility", "visibleFacilities", "facilityType"]:
                    parse_fac_data(current_region.get(key), r_id)

        for reg in visible_regions:
            if isinstance(reg, dict):
                r_id = reg.get("id")
                if r_id:
                    for key in ["facilities", "facility", "visibleFacilities", "facilityType"]:
                        parse_fac_data(reg.get(key), r_id)

        root_facs = self.view_data.get("visibleFacilities") or self.view_data.get("facilities")
        if isinstance(root_facs, list):
            for fac in root_facs:
                if isinstance(fac, dict):
                    r_id = fac.get("regionId") or fac.get("region")
                    if r_id:
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
                    status_str = status.capitalize()
                    fac_str_list.append(f"{f_name} [{status_str}]")
                
                layer_map[dist][r_name] = ", ".join(sorted(fac_str_list))
        return layer_map