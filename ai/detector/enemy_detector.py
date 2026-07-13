def _is_entity_alive(entity):
    if not isinstance(entity, dict):
        return False
    
    # 1. Cek properti isAlive (camelCase)
    is_alive_camel = entity.get('isAlive')
    if is_alive_camel is not None:
        return bool(is_alive_camel)
        
    # 2. Cek properti is_alive (snake_case)
    is_alive_snake = entity.get('is_alive')
    if is_alive_snake is not None:
        return bool(is_alive_snake)
        
    # 3. Verifikasi sisa HP (jika HP <= 0 maka entitas dianggap mati)
    hp = entity.get('hp')
    if hp is not None:
        try:
            return float(hp) > 0
        except (ValueError, TypeError):
            pass
            
    # Fallback jika tidak ada informasi status (dianggap hidup)
    return True

def detect_region_enemies(view):
    """
    Detect enemies in visible and connected regions
    Returns: dict mapping region name/ID to list of enemy strings
    """
    detected = {}
    
    # 1. Kumpulkan semua wilayah (wilayah saat ini, wilayah tetangga, wilayah terang lainnya)
    current_region = view.get('currentRegion', {}) or {}
    current_id = current_region.get('id')
    
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
            
    # 2. Identifikasi identitas bot sendiri untuk diabaikan
    self_data = view.get('self', {}) or {}
    self_id = self_data.get('id') or self_data.get('agentId') or self_data.get('agent_id')
    
    for r in regions_to_check:
        r_id = r.get('id')
        r_name = r.get('name') or r_id
        
        enemies = []
        
        # A. Deteksi Agen / Pemain Lain
        agents_in_region = r.get('agents') or r.get('players') or []
        for agent in agents_in_region:
            if not isinstance(agent, dict):
                continue
            agent_id = agent.get('id') or agent.get('agentId') or agent.get('agent_id')
            if agent_id == self_id:
                continue
                
            if _is_entity_alive(agent):
                hp = agent.get('hp', 100)
                name = agent.get('name') or agent.get('username') or agent.get('agentName') or f"Agent_{agent_id[:4]}" if agent_id else "Unknown Agent"
                enemies.append(f"Player: {name} [HP {hp}]")
                
        # B. Deteksi Monster biasa
        monsters = r.get('monsters') or []
        for m in monsters:
            if not isinstance(m, dict):
                continue
            if _is_entity_alive(m):
                m_type = m.get('type') or m.get('name') or m.get('monsterId') or "Monster"
                hp = m.get('hp')
                hp_str = f" [HP {hp}]" if hp is not None else ""
                enemies.append(f"Monster: {m_type}{hp_str}")
                
        # C. Deteksi Guardian
        guardians = r.get('guardians') or []
        for g in guardians:
            if not isinstance(g, dict):
                continue
            if _is_entity_alive(g):
                g_type = g.get('type') or g.get('name') or g.get('guardianId') or "Guardian"
                hp = g.get('hp')
                hp_str = f" [HP {hp}]" if hp is not None else ""
                enemies.append(f"Guardian: {g_type}{hp_str}")
                
        if enemies:
            detected[r_name] = enemies
            
    return detected