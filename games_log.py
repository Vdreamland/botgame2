import json
from typing import Dict, Any

def handle_game_message(msg_type: str, msg: Dict[str, Any], context: Any):
    if msg_type in ("agent_view", "turn_advanced"):
        view = msg.get("view") or msg.get("agentView") or msg.get("agent_view") or msg.get("data") or {}
        
        player = view.get("self") or view.get("player") or {}
        game_state = view.get("game") or view.get("gameState") or {}
        
        name = player.get("name", "Unknown")
        context.agent_name = name
        context.agent_id = player.get("id")
        
        hp = player.get("hp", 0)
        ep = player.get("ep", 0)
        x = player.get("x", 0)
        y = player.get("y", 0)
        is_alive = player.get("isAlive") if player.get("isAlive") is not None else player.get("is_alive", True)
        
        turn = game_state.get("turn", 1)
        
        eff_stats = player.get("effectiveStats") or {}
        atk = player.get("atk") or eff_stats.get("atk") or player.get("baseAtk", 0)
        defense = player.get("def") or eff_stats.get("def") or player.get("baseDef", 0)
        kills = player.get("kills") if player.get("kills") is not None else player.get("killCount", 0)
        
        region_data = view.get("currentRegion") or view.get("current_region") or {}
        terrain = region_data.get("terrain", "unknown") if isinstance(region_data, dict) else "unknown"
        
        print(f"\nTurn {turn} {name}")
        print(f"HP: {hp} | EP: {ep} | ATK: {atk} | DEF: {defense} | KILL: {kills}")
        print(f"Location: ({x}, {y}) ({terrain})")
        
        if not is_alive:
            print("[Alert] Agent has died. Connection closing...")

    elif msg_type == "action_result":
        success = msg.get("success", True)
        action = msg.get("action", "unknown")
        if success:
            print(f"[Action] Success: Executed '{action}'")
        else:
            err_msg = msg.get("error", {}).get("message", "Unknown error")
            print(f"[Action] Failed: Executed '{action}' - Error: {err_msg}")

    elif msg_type == "item_picked":
        agent_id = msg.get("agentId")
        if agent_id == context.agent_id:
            item = msg.get("item", {})
            item_name = item.get("name", "an item")
            print(f"[Activity] You picked up: {item_name}")

    elif msg_type == "agent_equipped":
        agent_id = msg.get("agentId")
        if agent_id == context.agent_id:
            item_name = msg.get("name", "an item")
            print(f"[Activity] You equipped: {item_name}")

    elif msg_type == "ruin_state_changed":
        occupied_by = msg.get("occupiedBy")
        cleared_by = msg.get("clearedBy")
        if occupied_by == context.agent_id or cleared_by == context.agent_id:
            gauge = msg.get("gauge", 0)
            max_gauge = msg.get("maxGauge", 3)
            print(f"[Ruin] Your exploration gauge is now {gauge}/{max_gauge}")

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