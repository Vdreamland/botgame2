import networkx as nx

def detect_connected_regions(view):
    """
    Detect all connected and visible regions
    Returns: list of region dicts
    """
    current_region = view.get('currentRegion', {})
    current_id = current_region.get('id')
    current_name = current_region.get('name') or current_id
    
    # Track visible regions data
    visible_regions_map = {}
    for r in view.get('visibleRegions', []):
        r_id = r.get('id')
        if r_id:
            visible_regions_map[r_id] = r
            
    # Include current region details if visible
    if current_id and current_id not in visible_regions_map:
        visible_regions_map[current_id] = current_region
        
    detected_list = []
    seen_ids = set()
    
    # 1. Current region first
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
        
    # 2. Adjacent connected regions
    for r in view.get('connectedRegions', []):
        # connectedRegions can contain objects or bare IDs
        r_id = r.get('id') if isinstance(r, dict) else r
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
                # Outside vision
                detected_list.append({
                    'id': r_id,
                    'name': r_id,
                    'terrain': 'unknown',
                    'is_death_zone': False,
                    'is_visible': False
                })
            seen_ids.add(r_id)
            
    # 3. Other visible regions in sight (e.g. ruins, court, etc.)
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
    
    # 1. Gather all regions
    current_region = view.get('currentRegion', {})
    current_id = current_region.get('id')
    current_name = current_region.get('name') or current_id
    
    regions_to_check = []
    seen_regions = set()
    
    if current_id:
        regions_to_check.append(current_region)
        seen_regions.add(current_id)
        
    for r in view.get('connectedRegions', []):
        r_id = r.get('id') if isinstance(r, dict) else r
        if r_id and r_id not in seen_regions:
            if isinstance(r, dict):
                regions_to_check.append(r)
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
        
        # Check facilities (e.g. cave, refinery)
        facility = r.get('facility')
        if facility:
            f_type = facility.get('type')
            if f_type:
                # Format like "Cave" or "Refinery [2]"
                level = facility.get('level')
                level_str = f" [{level}]" if level is not None else ""
                items.append(f"{f_type.capitalize()}{level_str}")
                
        # Check ruins
        ruins = r.get('ruins')
        if ruins:
            ruins_name = ruins.get('name') or "Ruins"
            items.append(f"{ruins_name}")
            
        # Check ground items
        ground_items = r.get('items', []) or r.get('groundItems', [])
        for item in ground_items:
            item_name = item.get('name') or item.get('type') or "Item"
            qty = item.get('qty', 1)
            qty_str = f" x{qty}" if qty > 1 else ""
            items.append(f"{item_name}{qty_str}")
            
        if items:
            detected[r_name] = items
            
    return detected