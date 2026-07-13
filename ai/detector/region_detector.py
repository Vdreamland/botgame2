def detect_region_enemies(view):
    """
    Detect enemies in visible and connected regions
    Returns: dict mapping region name/ID to list of enemy strings
    """
    detected = {}
    
    # 1. Gather all regions (current, connected, other visible)
    current_region = view.get('currentRegion', {})
    current_id = current_region.get('id')
    current_name = current_region.get('name') or current_id
    
    # Track regions to check
    regions_to_check = []
    seen_regions = set()
    
    if current_id:
        regions_to_check.append(current_region)
        seen_regions.add(current_id)
        
    for r in view.get('connectedRegions', []):
        r_id = r.get('id') if isinstance(r, dict) else r
        if r_id and r_id not in seen_regions:
            # We only have complete data if it's a dict
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
            
    # Process each region
    self_id = view.get('self', {}).get('id') or view.get('self', {}).get('agentId')
    
    for r in regions_to_check:
        r_id = r.get('id')
        r_name = r.get('name') or r_id
        
        enemies = []
        
        # Check players/agents in this region
        agents_in_region = r.get('agents', []) or r.get('players', [])
        for agent in agents_in_region:
            agent_id = agent.get('id') or agent.get('agentId')
            # Ignore self
            if agent_id == self_id:
                continue
                
            # Only count alive ones
            if agent.get('isAlive', True):
                hp = agent.get('hp', 100)
                name = agent.get('name') or f"Agent_{agent_id[:4]}" if agent_id else "Unknown Agent"
                enemies.append(f"Player: {name} [HP {hp}]")
                
        # Check monsters/guardians
        monsters = r.get('monsters', [])
        for m in monsters:
            if m.get('isAlive', True):
                m_type = m.get('type') or m.get('name') or "Monster"
                hp = m.get('hp')
                hp_str = f" [HP {hp}]" if hp is not None else ""
                enemies.append(f"Monster: {m_type}{hp_str}")
                
        # Guardians
        guardians = r.get('guardians', [])
        for g in guardians:
            if g.get('isAlive', True):
                g_type = g.get('type') or g.get('name') or "Guardian"
                hp = g.get('hp')
                hp_str = f" [HP {hp}]" if hp is not None else ""
                enemies.append(f"Guardian: {g_type}{hp_str}")
                
        if enemies:
            detected[r_name] = enemies
            
    return detected