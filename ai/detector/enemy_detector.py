def _is_entity_alive(entity):
    if not isinstance(entity, dict):
        return False
    is_alive_camel = entity.get('isAlive')
    if is_alive_camel is not None:
        return bool(is_alive_camel)
    is_alive_snake = entity.get('is_alive')
    if is_alive_snake is not None:
        return bool(is_alive_snake)
    hp = entity.get('hp')
    if hp is not None:
        try:
            return float(hp) > 0
        except (ValueError, TypeError):
            pass
    return True

def detect_region_enemies(view):
    detected = {}
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
            
    self_data = view.get('self', {}) or {}
    self_id = self_data.get('id') or self_data.get('agentId') or self_data.get('agent_id')
    
    region_id_to_name = {}
    coord_to_region_name = {}
    
    for r in regions_to_check:
        r_id = r.get('id')
        r_name = r.get('name') or r_id
        if r_id:
            region_id_to_name[r_id] = r_name
            region_id_to_name[r_name] = r_name
            
        coords = r.get('hexCoords') or r.get('hex_coords')
        if coords:
            if isinstance(coords, list):
                coord_to_region_name[tuple(coords)] = r_name
            elif isinstance(coords, dict):
                q = coords.get('q') or coords.get('x')
                r_val = coords.get('r') or coords.get('y')
                if q is not None and r_val is not None:
                    coord_to_region_name[(q, r_val)] = r_name
                    
        x = r.get('x')
        y = r.get('y')
        if x is not None and y is not None:
            coord_to_region_name[(x, y)] = r_name

    def get_entity_region_name(entity):
        r_id = entity.get('regionId') or entity.get('region_id') or entity.get('location')
        if not r_id and isinstance(entity.get('position'), dict):
            pos = entity.get('position', {})
            r_id = pos.get('regionId') or pos.get('region_id') or pos.get('id')
        elif not r_id and isinstance(entity.get('position'), str):
            r_id = entity.get('position')
            
        if r_id:
            val = region_id_to_name.get(r_id) or region_id_to_name.get(str(r_id))
            if val:
                return val
            return str(r_id)
            
        coords = entity.get('hexCoords') or entity.get('hex_coords')
        if coords:
            if isinstance(coords, list):
                key = tuple(coords)
                if key in coord_to_region_name:
                    return coord_to_region_name[key]
            elif isinstance(coords, dict):
                q = coords.get('q') or coords.get('x')
                r_val = coords.get('r') or coords.get('y')
                if q is not None and r_val is not None:
                    key = (q, r_val)
                    if key in coord_to_region_name:
                        return coord_to_region_name[key]
                        
        x = entity.get('x')
        y = entity.get('y')
        if x is not None and y is not None:
            key = (x, y)
            if key in coord_to_region_name:
                return coord_to_region_name[key]
                
        return None

    visible_agents = view.get('visibleAgents') or []
    for agent in visible_agents:
        if not isinstance(agent, dict):
            continue
        agent_id = agent.get('id') or agent.get('agentId') or agent.get('agent_id')
        if agent_id == self_id:
            continue
        if _is_entity_alive(agent):
            hp = agent.get('hp', 100)
            name = agent.get('name') or agent.get('username') or agent.get('agentName') or (f"Agent_{agent_id[:4]}" if agent_id else "Unknown Agent")
            r_name = get_entity_region_name(agent)
            if r_name:
                if r_name not in detected:
                    detected[r_name] = []
                is_guardian = agent.get('isGuardian', False)
                prefix = "Guardian" if is_guardian else "Player"
                detected[r_name].append(f"{prefix}: {name} [HP {hp}]")
                
    visible_monsters = view.get('visibleMonsters') or []
    for m in visible_monsters:
        if not isinstance(m, dict):
            continue
        if _is_entity_alive(m):
            m_type = m.get('type') or m.get('name') or m.get('monsterId') or "Monster"
            hp = m.get('hp')
            hp_str = f" [HP {hp}]" if hp is not None else ""
            r_name = get_entity_region_name(m)
            if r_name:
                if r_name not in detected:
                    detected[r_name] = []
                detected[r_name].append(f"Monster: {m_type}{hp_str}")
                
    visible_npcs = view.get('visibleNPCs') or []
    for npc in visible_npcs:
        if not isinstance(npc, dict):
            continue
        if _is_entity_alive(npc):
            npc_type = npc.get('type') or npc.get('name') or npc.get('npcId') or "NPC"
            hp = npc.get('hp')
            hp_str = f" [HP {hp}]" if hp is not None else ""
            r_name = get_entity_region_name(npc)
            if r_name:
                if r_name not in detected:
                    detected[r_name] = []
                detected[r_name].append(f"Guardian: {npc_type}{hp_str}")
                
    return detected