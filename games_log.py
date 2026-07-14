from typing import Dict, Any, Optional

def print_game_state(status: Dict[str, Any], regions: Any, region_items: Dict[str, Any], region_enemies: Dict[str, Any], ruin: Optional[Dict[str, Any]], is_death_zone: bool):
    color_red = "\033[91m"
    color_reset = "\033[0m"
    current_zone_label = f" {color_red}[deadzone]{color_reset}" if is_death_zone else ""
    
    print(f"\n--- [DAY {status['day']} TURN {status['turn']}] ---")
    print(f"Agent: {status['name']} | HP: {status['hp']} | EP: {status['ep']} | ATK: {status['atk']} | DEF: {status['def']} | KILL: {status['kill']}")
    
    if ruin:
        status_val = ruin["status"].capitalize() if isinstance(ruin["status"], str) else ruin["status"]
        print(f"Location: {status['region_name']}{current_zone_label} | Status : {status_val} | Gauge : {ruin['gauge']} / {ruin['max_gauge']} | Explorer : {ruin['explorer']}")
    else:
        terrain_cap = status['terrain'].capitalize() if status['terrain'] else "Unknown"
        weather_cap = status['weather'].capitalize() if status['weather'] else "Unknown"
        print(f"Location: {status['region_name']}{current_zone_label} | Terrain : {terrain_cap} | Weather : {weather_cap} | Vision {status['vision']} | Link {status['num_links']}")
    
    print(f"Weapon : {status['weapon']} | Armour : {status['armor']}")
    print(f"Inventory : {inv_display if 'inv_display' in locals() else status['inventory']}")
    
    if status['hp'] > 0:
        layers = {}
        for r in regions:
            dist = r.get("layer", 1)
            if dist == 0:
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

def print_action_intention(next_action: Dict[str, Any], regions: Any, friendly_name_lookup_func, view: Dict[str, Any]):
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
        friendly_name = friendly_name_lookup_func(view, target_id)
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
        friendly_name = friendly_name_lookup_func(view, target_obj)
        if friendly_name:
            print(f"[Intention] Bot decides to interact with: {friendly_name}")
        else:
            print(f"[Intention] Bot decides to interact with facility ID: {target_obj}")
    elif act_type == "explore":
        print(f"[Intention] Bot decides to Explore Ruins to acquire Relic")
    elif act_type == "attack":
        target_obj = act_data.get("targetId")
        friendly_name = friendly_name_lookup_func(view, target_obj)
        if friendly_name:
            print(f"[Intention] Bot decides to Attack: {friendly_name}")
        else:
            print(f"[Intention] Bot decides to Attack target ID: {target_obj}")