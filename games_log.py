import json
from typing import Dict, Any

async def handle_game_message(msg_type: str, msg: Dict[str, Any], context: Any):
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
        
        # Bandingkan status baru dengan status cetakan terakhir (Deduplication)
        current_state = (turn, hp, ep, x, y, kills, terrain)
        last_printed = getattr(context, "last_state", None)
        
        if last_printed != current_state:
            print(f"\nTurn {turn} {name}")
            print(f"HP: {hp} | EP: {ep} | ATK: {atk} | DEF: {defense} | KILL: {kills}")
            print(f"Location: ({x}, {y}) ({terrain})")
            context.last_state = current_state
        
        if not is_alive:
            print("[Alert] Agent has died. Connection closing...")
            game_id = msg.get("gameId") or view.get("gameId") or game_state.get("gameId")
            if game_id and hasattr(context, "dead_games") and context.dead_games is not None:
                context.dead_games.add(game_id)
            if context.ws:
                await context.ws.close()

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
                
            # Deteksi kematian secara aktif via World Log jika data agent_view dihentikan oleh server
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