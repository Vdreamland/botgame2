import json
from typing import Dict, Any
from ai.detector import extract_agent_status, detect_connected_regions

async def handle_game_message(msg_type: str, msg: Dict[str, Any], context: Any):
    if msg_type in ("agent_view", "turn_advanced"):
        view = msg.get("view") or msg.get("agentView") or msg.get("agent_view") or msg.get("data") or {}
        
        status = extract_agent_status(view)
        regions = detect_connected_regions(view)
        
        name = status["name"]
        context.agent_name = name
        context.agent_id = status["id"]
        
        hp = status["hp"]
        ep = status["ep"]
        x = status["x"]
        y = status["y"]
        is_alive = status["is_alive"]
        turn = status["turn"]
        day = status["day"]
        atk = status["atk"]
        defense = status["def"]
        kills = status["kill"]
        terrain = status["terrain"]
        
        current_state = (turn, hp, ep, x, y, kills, terrain)
        last_printed = getattr(context, "last_state", None)
        
        if last_printed != current_state:
            print(f"\n--- [DAY {day} TURN {turn}] ---")
            print(f"Agent: {name} | HP: {hp} | EP: {ep} | ATK: {atk} | DEF: {defense} | KILL: {kills}")
            print(f"Location: ({x}, {y}) ({terrain})")
            
            # Kode warna ANSI untuk konsol/terminal
            color_green = "\033[92m"
            color_red = "\033[91m"
            color_reset = "\033[0m"
            
            # Format horizontal: nama [safezone] / nama [deadzone]
            region_strings = []
            for r in regions:
                is_dead = r.get("is_death_zone", False)
                if is_dead:
                    zone_label = f"{color_red}[deadzone]{color_reset}"
                else:
                    zone_label = f"{color_green}[safezone]{color_reset}"
                region_strings.append(f"{r['name']} {zone_label}")
            
            joined_regions = " / ".join(region_strings)
            print(f"Region detector : {joined_regions}")
            
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
            print("[Alert] Agent has died. Connection closing...")
            game_id = msg.get("gameId") or view.get("gameId") or view.get("game", {}).get("gameId")
            if game_id and hasattr(context, "dead_games") and context.dead_games is not None:
                context.dead_games.add(game_id)
            if context.ws:
                await context.ws.close()

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
                if name_lower in lower_msg:
                    if "killed" in lower_msg or "died" in lower_msg or "eliminated" in lower_msg:
                        print("[Alert] Agent has died (Detected via world log). Connection closing...")
                        game_id = msg.get("gameId") or log_data.get("gameId")
                        if game_id and hasattr(context, "dead_games") and context.dead_games is not None:
                            context.dead_games.add(game_id)
                        if context.ws:
                            await context.ws.close()