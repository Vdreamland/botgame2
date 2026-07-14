import json
from typing import Dict, Any
from ai.detector import extract_agent_status, detect_connected_regions, detect_region_items, detect_region_enemies
from ai.decision_maker import decide_next_action

async def _handle_agent_death(msg: Dict[str, Any], view: Dict[str, Any], context: Any, source: str):
    print(f"[Alert] Agent has died (Detected via {source}). Connection closing...")
    game_id = msg.get("gameId") or view.get("gameId") or view.get("game", {}).get("gameId")
    if game_id and hasattr(context, "dead_games") and context.dead_games is not None:
        context.dead_games.add(game_id)
    if context.ws:
        await context.ws.close()

def _find_entity_name(view: Dict[str, Any], target_id: str) -> str:
    """Helper terpadu untuk mencari nama entitas/item/fasilitas berdasarkan ID dari data view."""
    if not target_id:
        return ""
    
    # 1. Periksa fasilitas dan item di region aktif saat ini
    curr_reg = view.get("currentRegion", {}) or {}
    for inter in (curr_reg.get("interactables", []) or []):
        if isinstance(inter, dict) and inter.get("id") == target_id:
            f_type = inter.get("type") or inter.get("name") or "facility"
            return f_type.replace('_', ' ').title() + f" at {curr_reg.get('name', 'Current Region')}"
            
    for item in (curr_reg.get("items", []) or curr_reg.get("groundItems", []) or []):
        if isinstance(item, dict) and item.get("id") == target_id:
            return item.get("name") or item.get("type") or item.get("typeId") or ""

    # 2. Periksa fasilitas dan item di region lain yang terlihat
    for r in (view.get("visibleRegions", []) or []):
        if isinstance(r, dict):
            for inter in (r.get("interactables", []) or []):
                if isinstance(inter, dict) and inter.get("id") == target_id:
                    f_type = inter.get("type") or inter.get("name") or "facility"
                    return f_type.replace('_', ' ').title() + f" at {r.get('name', 'Visible Region')}"
            for item in (r.get("items", []) or r.get("groundItems", []) or []):
                if isinstance(item, dict) and item.get("id") == target_id:
                    return item.get("name") or item.get("type") or item.get("typeId") or ""

    # 3. Periksa inventaris atau equipment milik agen sendiri
    self_data = view.get("self", {}) or {}
    for item in (self_data.get("inventory", []) or []):
        if isinstance(item, dict) and item.get("id") == target_id:
            return item.get("name") or item.get("type") or item.get("typeId") or ""
            
    for item in (self_data.get("equipment", {}) or {}).values():
        if isinstance(item, dict) and item.get("id") == target_id:
            return item.get("name") or item.get("type") or item.get("typeId") or ""

    # 4. Periksa agen, monster, atau NPC yang terlihat di sekitar
    for category in ("visibleAgents", "visibleMonsters", "visibleNPCs"):
        for entity in (view.get(category, []) or []):
            if isinstance(entity, dict):
                ent_id = entity.get("id") or entity.get("agentId") or entity.get("monsterId") or entity.get("npcId")
                if ent_id == target_id:
                    return entity.get("name") or entity.get("username") or entity.get("agentName") or entity.get("type") or ""
                    
    return ""

async def handle_game_message(msg_type: str, msg: Dict[str, Any], context: Any):
    if msg_type in ("agent_view", "turn_advanced"):
        view = msg.get("view") or msg.get("agentView") or msg.get("agent_view") or msg.get("data") or {}
        
        status = extract_agent_status(msg)
        regions = detect_connected_regions(view)
        region_items = detect_region_items(view)
        region_enemies = detect_region_enemies(view)
        
        name = status["name"]
        context.agent_name = name
        context.agent_id = status["id"]
        
        hp = status["hp"]
        ep = status["ep"]
        x = status["x"]
        y = status["y"]
        is_alive = status["is_alive"]
        global_turn = status["global_turn"]
        turn = status["turn"]
        day = status["day"]
        atk = status["atk"]
        defense = status["def"]
        kills = status["kill"]
        region_name = status["region_name"]
        is_death_zone = status["is_death_zone"]
        terrain = status["terrain"]
        weather = status["weather"]
        vision = status["vision"]
        num_links = status["num_links"]
        ruin = status["ruin"]
        weapon_name = status["weapon"]
        armor_name = status["armor"]
        inv_display = status["inventory"]
        
        current_state = (global_turn, hp, ep, x, y, kills, region_name, terrain, is_death_zone, weather, vision, num_links, str(ruin), str(region_enemies))
        last_printed = getattr(context, "last_state", None)
        
        if last_printed != current_state:
            color_red = "\033[91m"
            color_reset = "\033[0m"
            
            current_zone_label = f" {color_red}[deadzone]{color_reset}" if is_death_zone else ""
            
            print(f"\n--- [DAY {day} TURN {turn}] ---")
            print(f"Agent: {name} | HP: {hp} | EP: {ep} | ATK: {atk} | DEF: {defense} | KILL: {kills}")
            
            if ruin:
                status_val = ruin["status"].capitalize() if isinstance(ruin["status"], str) else ruin["status"]
                print(f"Location: {region_name}{current_zone_label} | Status : {status_val} | Gauge : {ruin['gauge']} / {ruin['max_gauge']} | Explorer : {ruin['explorer']}")
            else:
                terrain_cap = terrain.capitalize() if terrain else "Unknown"
                weather_cap = weather.capitalize() if weather else "Unknown"
                print(f"Location: {region_name}{current_zone_label} | Terrain : {terrain_cap} | Weather : {weather_cap} | Vision {vision} | Link {num_links}")
            
            print(f"Weapon : {weapon_name} | Armour : {armor_name}")
            print(f"Inventory : {inv_display}")
            
            if hp > 0:
                layers = {}
                for r in regions:
                    dist = r.get("layer", 1)
                    if dist == 0:  # Abaikan Layer 0 (tempat agen berdiri)
                        continue
                    
                    if dist not in layers:
                        layers[dist] = []
                    
                    is_dead = r.get("is_death_zone", False)
                    zone_label = f" {color_red}[deadzone]{color_reset}" if is_dead else ""
                    layers[dist].append(f"{r['name']}{zone_label}")

                print()
                print("Region detector :")
                if layers:
                    for dist in sorted(layers.keys()):
                        joined = ", ".join(layers[dist])
                        print(f"Layer {dist} : {joined}")
                else:
                    print("none")
            
            print()
            if region_items:
                print("Region Item detector :")
                for r_name, items in region_items.items():
                    print(f"{r_name} > {', '.join(items)}")
            else:
                print("Region Item detector : none")
            
            print()
            if region_enemies:
                print("Region Enemy detector :")
                for r_name, enemies in region_enemies.items():
                    print(f"{r_name} > {', '.join(enemies)}")
            else:
                print("Region Enemy detector : none")
            
            try:
                next_action = decide_next_action(view, context)
                if next_action and next_action.get("type") == "action":
                    act_data = next_action.get("data", {})
                    act_type = act_data.get("type")
                    
                    if act_type == "move":
                        target_id = act_data.get("regionId")
                        target_name = target_id
                        for r in regions:
                            if r.get("id") == target_id:
                                target_name = r.get("name")
                                break
                        print(f"[Intention] Bot decides to move to: {target_name} to search or retrieve items")
                    elif act_type in ("pickup", "equip", "use_item", "drop"):
                        target_id = act_data.get("itemId")
                        friendly_name = _find_entity_name(view, target_id)
                        action_labels = {"pickup": "pick up", "equip": "equip", "use_item": "use item", "drop": "drop"}
                        label = action_labels.get(act_type, "process")
                        
                        if friendly_name:
                            print(f"[Intention] Bot decides to {label}: {friendly_name}")
                        else:
                            print(f"[Intention] Bot decides to {label} item ID: {target_id}")
                    elif act_type == "rest":
                        print(f"[Intention] Bot decides to Rest to restore EP")
                    elif act_type == "interact":
                        target_obj = act_data.get("targetId")
                        friendly_name = _find_entity_name(view, target_obj)
                        if friendly_name:
                            print(f"[Intention] Bot decides to interact with: {friendly_name}")
                        else:
                            print(f"[Intention] Bot decides to interact with facility ID: {target_obj}")
                    elif act_type == "explore":
                        print(f"[Intention] Bot decides to Explore Ruins to acquire Relic")
                    elif act_type == "attack":
                        target_obj = act_data.get("targetId")
                        friendly_name = _find_entity_name(view, target_obj)
                        if friendly_name:
                            print(f"[Intention] Bot decides to Attack: {friendly_name}")
                        else:
                            print(f"[Intention] Bot decides to Attack target ID: {target_obj}")
                    
                    if context.ws:
                        await context.ws.send(json.dumps(next_action))
            except Exception as e:
                print(f"[DEBUG ERROR] Gagal mengeksekusi decide_next_action: {e}")
            
            context.last_state = current_state
        
        last_hp = getattr(context, "last_hp", None)
        if last_hp is not None and last_hp != hp:
            diff = last_hp - hp
            if diff > 0:
                print(f"[Status Update] You took {diff} damage! HP is now {hp}/{view.get('self', {}).get('maxHp', 100)}")
            elif diff < 0:
                print(f"[Status Update] You healed {abs(diff)} HP! HP is now {hp}/{view.get('self', {}).get('maxHp', 100)}")
        context.last_hp = hp
        
        if not is_alive:
            await _handle_agent_death(msg, view, context, "state view")
            
    elif msg_type == "can_act_changed":
        can_act = msg.get("canAct", False)
        if can_act:
            print("[Action Ready] Cooldown over. You can act now!")
            
    elif msg_type == "error":
        err_msg = msg.get("error", {}).get("message", json.dumps(msg))
        print(f"[Server Error] {err_msg}")
        
    elif msg_type == "log":
        log_data = msg.get("log", {})
        message = log_data.get("message", "")
        agent_id = msg.get("agentId") or log_data.get("agentId")
        
        if (agent_id == context.agent_id) or (context.agent_name and context.agent_name in message):
            if message:
                print(f"[World Log] {message}")
                
        if context.agent_name:
            lower_msg = message.lower()
            name_lower = context.agent_name.lower()
            
            is_my_death = False
            if f"{name_lower} died" in lower_msg:
                is_my_death = True
            elif f"{name_lower} perished" in lower_msg:
                is_my_death = True
            elif f"{name_lower} was killed" in lower_msg:
                is_my_death = True
            elif f"{name_lower} was eliminated" in lower_msg:
                is_my_death = True
            elif f"{name_lower} has been eliminated" in lower_msg:
                is_my_death = True
            elif lower_msg.startswith(name_lower) and ("killed" in lower_msg or "died" in lower_msg or "perished" in lower_msg or "eliminated" in lower_msg):
                is_my_death = True
            elif f"killed {name_lower}" in lower_msg or f"eliminated {name_lower}" in lower_msg:
                is_my_death = True
                
            if is_my_death:
                await _handle_agent_death(msg, {}, context, "world log")