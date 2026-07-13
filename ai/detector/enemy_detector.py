from helpers.game_math import MONSTER_FALLBACK_STATS

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

def _get_monster_stats(m_type, raw_hp=None, raw_ep=None, raw_atk=None, raw_def=None):
    name_lower = str(m_type).lower()
    fallback = {"hp": 0, "ep": 0, "atk": 0, "def": 0}
    
    if "guardian" in name_lower:
        fallback = MONSTER_FALLBACK_STATS["guardian"]
    elif "wolf" in name_lower:
        fallback = MONSTER_FALLBACK_STATS["wolf"]
    elif "bear" in name_lower:
        fallback = MONSTER_FALLBACK_STATS["bear"]
    elif "bandit" in name_lower:
        fallback = MONSTER_FALLBACK_STATS["bandit"]
        
    hp = raw_hp if (raw_hp is not None and raw_hp != 0) else fallback["hp"]
    ep = raw_ep if (raw_ep is not None and raw_ep != 0) else fallback["ep"]
    atk = raw_atk if (raw_atk is not None and raw_atk != 0) else fallback["atk"]
    defense = raw_def if (raw_def is not None and raw_def != 0) else fallback["def"]
    
    return hp, ep, atk, defense

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

    def get_entity_equipment(entity):
        wpn = entity.get('equippedWeapon')
        if isinstance(wpn, dict):
            wpn_name = wpn.get('name') or wpn.get('id') or "None"
        else:
            wpn_name = entity.get('equippedWeaponId') or "None"
            
        arm = entity.get('equippedArmor')
        if isinstance(arm, dict):
            arm_name = arm.get('name') or arm.get('id') or "None"
        else:
            arm_name = entity.get('equippedArmorId') or "None"
            
        return wpn_name, arm_name

    visible_agents = view.get('visibleAgents') or []
    for agent in visible_agents:
        if not isinstance(agent, dict):
            continue
        agent_id = agent.get('id') or agent.get('agentId') or agent.get('agent_id')
        if agent_id == self_id:
            continue
        if _is_entity_alive(agent):
            name = agent.get('name') or agent.get('username') or agent.get('agentName') or (f"Agent_{agent_id[:4]}" if agent_id else "Unknown Agent")
            if "hermit" in name.lower():
                continue
            hp = agent.get('hp', 100)
            ep = agent.get('ep', 0)
            atk = agent.get('atk', 0)
            defense = agent.get('def', 0)
            r_name = get_entity_region_name(agent)
            if r_name:
                if r_name not in detected:
                    detected[r_name] = []
                is_guardian = agent.get('isGuardian', False)
                prefix = "G" if is_guardian else "P"
                wpn_name, arm_name = get_entity_equipment(agent)
                detected[r_name].append(f"{prefix} : {name} HP:{hp}/EP:{ep}/ATK:{atk}/DEF:{defense}/Wpn:{wpn_name}/Arm:{arm_name}/")
                
    visible_monsters = view.get('visibleMonsters') or []
    for m in visible_monsters:
        if not isinstance(m, dict):
            continue
        if _is_entity_alive(m):
            m_type = m.get('type') or m.get('name') or m.get('monsterId') or "Monster"
            if "hermit" in m_type.lower():
                continue
            r_name = get_entity_region_name(m)
            if r_name:
                if r_name not in detected:
                    detected[r_name] = []
                raw_hp = m.get('hp')
                raw_ep = m.get('ep')
                raw_atk = m.get('atk')
                raw_def = m.get('def')
                hp, ep, atk, defense = _get_monster_stats(m_type, raw_hp, raw_ep, raw_atk, raw_def)
                detected[r_name].append(f"M : {m_type} HP:{hp}/EP:{ep}/ATK:{atk}/DEF:{defense}/")
                
    visible_npcs = view.get('visibleNPCs') or []
    for npc in visible_npcs:
        if not isinstance(npc, dict):
            continue
        if _is_entity_alive(npc):
            npc_type = npc.get('type') or npc.get('name') or npc.get('npcId') or "NPC"
            if "hermit" in npc_type.lower():
                continue
            r_name = get_entity_region_name(npc)
            if r_name:
                if r_name not in detected:
                    detected[r_name] = []
                raw_hp = npc.get('hp')
                raw_ep = npc.get('ep')
                raw_atk = npc.get('atk')
                raw_def = npc.get('def')
                hp, ep, atk, defense = _get_monster_stats(npc_type, raw_hp, raw_ep, raw_atk, raw_def)
                detected[r_name].append(f"G : {npc_type} HP:{hp}/EP:{ep}/ATK:{atk}/DEF:{defense}/")
                
    return detected