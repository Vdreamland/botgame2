def detect_connected_regions(view):
    """
    Detect all connected and visible regions
    Returns: list of region dicts
    """
    current_region = view.get('currentRegion', {}) or {}
    current_id = current_region.get('id')
    current_name = current_region.get('name') or current_id
    
    visible_regions_map = {}
    for r in view.get('visibleRegions', []):
        r_id = r.get('id')
        if r_id:
            visible_regions_map[r_id] = r
            
    if current_id and current_id not in visible_regions_map:
        visible_regions_map[current_id] = current_region
        
    detected_list = []
    seen_ids = set()
    
    if current_id:
        curr_detail = visible_regions_map.get(current_id, current_region)
        detected_list.append({
            'id': current_id,
            'name': current_name,
            'terrain': curr_detail.get('terrain', 'unknown'),
            'is_death_zone': curr_detail.get('isDeathZone', False) or curr_detail.get('is_death_zone', False),
            'is_visible': True
        })
        seen_ids.add(current_id)
        
    connections = current_region.get('connections', []) or []
    for r_id in connections:
        if r_id and r_id not in seen_ids:
            if r_id in visible_regions_map:
                detail = visible_regions_map[r_id]
                detected_list.append({
                    'id': r_id,
                    'name': detail.get('name') or r_id,
                    'terrain': detail.get('terrain', 'unknown'),
                    'is_death_zone': detail.get('isDeathZone', False) or detail.get('is_death_zone', False),
                    'is_visible': True
                })
            else:
                detected_list.append({
                    'id': r_id,
                    'name': r_id,
                    'terrain': 'unknown',
                    'is_death_zone': False,
                    'is_visible': False
                })
            seen_ids.add(r_id)
            
    for r_id, detail in visible_regions_map.items():
        if r_id not in seen_ids:
            detected_list.append({
                'id': r_id,
                'name': detail.get('name') or r_id,
                'terrain': detail.get('terrain', 'unknown'),
                'is_death_zone': detail.get('isDeathZone', False) or detail.get('is_death_zone', False),
                'is_visible': True
            })
            seen_ids.add(r_id)
            
    return detected_list

def detect_region_items(view):
    """
    Detect items and facilities in visible and connected regions
    Returns: dict mapping region name/ID to list of item/facility strings
    """
    detected = {}
    
    current_region = view.get('currentRegion', {}) or {}
    current_id = current_region.get('id')
    
    visible_regions_map = {}
    for r in view.get('visibleRegions', []):
        r_id = r.get('id')
        if r_id:
            visible_regions_map[r_id] = r
            
    regions_to_check = []
    seen_regions = set()
    
    if current_id:
        regions_to_check.append(current_region)
        seen_regions.add(current_id)
        
    connections = current_region.get('connections', []) or []
    for r_id in connections:
        if r_id and r_id not in seen_regions:
            if r_id in visible_regions_map:
                regions_to_check.append(visible_regions_map[r_id])
            else:
                regions_to_check.append({'id': r_id})
            seen_regions.add(r_id)
            
    for r in view.get('visibleRegions', []):
        r_id = r.get('id')
        if r_id and r_id not in seen_regions:
            regions_to_check.append(r)
            seen_regions.add(r_id)
            
    for r in regions_to_check:
        r_id = r.get('id')
        r_name = r.get('name') or r_id
        
        items = []
        
        interactables = r.get('interactables', []) or []
        for inter in interactables:
            if isinstance(inter, dict):
                f_type = inter.get('type') or inter.get('name') or inter.get('id')
                if f_type:
                    f_name = f_type.replace('_', ' ').title()
                    level = inter.get('level')
                    level_str = f" [{level}]" if level is not None else ""
                    items.append(f"{f_name}{level_str}")
                    
                    nested_items = inter.get('items', []) or inter.get('inventory', []) or []
                    for n_item in nested_items:
                        if isinstance(n_item, dict):
                            n_name = n_item.get('name') or n_item.get('type') or n_item.get('typeId')
                            if n_name:
                                items.append(f"Inside {f_name}: {n_name}")
                    
        facility = r.get('facility')
        if facility:
            f_type = facility.get('type')
            if f_type:
                f_name = f_type.replace('_', ' ').title()
                level = facility.get('level')
                level_str = f" [{level}]" if level is not None else ""
                items.append(f"{f_name}{level_str}")
                
        ruins = r.get('ruins')
        if ruins:
            ruins_name = ruins.get('name') or "Ruins"
            items.append(f"{ruins_name}")
            
        ground_items = r.get('items', []) or r.get('groundItems', []) or []
        for item in ground_items:
            item_name = item.get('name') or item.get('type') or item.get('typeId') or "Item"
            qty = item.get('qty', 1)
            qty_str = f" x{qty}" if qty > 1 else ""
            items.append(f"{item_name}{qty_str}")
            
        if items:
            detected[r_name] = items
            
    return detected