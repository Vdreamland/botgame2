import asyncio
from src.config import VERSION, WS_JOIN_URL, WEB_LOG_URL
from src.websocket import GameWebSocket
from src.log.log_connections import log_info, log_warning, log_error
from src.log.logs_games import GameLogSender

async def connect_and_play(bot_name, api_key, entry_type):
    if not api_key:
        log_error(bot_name, "API key is empty. Skipping connection.")
        return

    headers = {
        "Authorization": f"mr-auth {api_key}",
        "X-Version": VERSION
    }
    
    log_info(bot_name, "Reconnecting to join a new match room...")
    log_sender = GameLogSender(bot_name, WEB_LOG_URL)
    await log_sender.connect()
    
    credits = 0
    game_id = None
    is_alive = True
    await log_sender.send_log({"type": "status_update", "status": "lobby", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": is_alive})
    
    has_logged_queue = False
    has_logged_wait = False
    has_logged_gameplay = False
    
    try:
        async with GameWebSocket(WS_JOIN_URL, headers) as client:
            welcome = await client.recv()
            decision = welcome.get("decision")
            
            credits = welcome.get("account", {}).get("credits", 0)
            
            if decision == "ALREADY_IN_GAME":
                await log_sender.send_log({"type": "status_update", "status": "playing", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": is_alive})
            elif decision in ("ASK_ENTRY_TYPE", "FREE_ONLY"):
                await log_sender.send_log({"type": "status_update", "status": "lobby", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": is_alive})
            
            if decision == "BLOCKED":
                missing = welcome.get("readiness", {}).get("freeRoom", {}).get("missing", [])
                log_error(bot_name, f"Readiness BLOCKED. Reasons: {missing}")
                return
            
            if decision == "PAID_ONLY":
                log_error(bot_name, "Free entry not permitted (PAID_ONLY).")
                return
            
            if decision in ("ASK_ENTRY_TYPE", "FREE_ONLY"):
                hello_msg = {
                    "type": "hello",
                    "entryType": entry_type
                }
                await client.send(hello_msg)
            
            game_id = None
            agent_id = None
            in_gameplay = False
            
            while True:
                try:
                    msg = await asyncio.wait_for(client.recv(), timeout=60.0)
                except asyncio.TimeoutError:
                    log_warning(bot_name, "Connection inactive for 60 seconds. Reconnecting...")
                    break

                msg_type = msg.get("type")
                
                active_game_id = msg.get("gameId")
                if active_game_id:
                    game_id = active_game_id
                
                if msg_type == "queued":
                    if not has_logged_queue:
                        log_info(bot_name, "Queue active. Searching for match...")
                        has_logged_queue = True
                    await log_sender.send_log({"type": "status_update", "status": "matchmaking", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": is_alive})
                    
                elif msg_type == "assigned":
                    game_id = msg.get("gameId")
                    agent_id = msg.get("agentId")
                    log_info(bot_name, f"Match found! Room ID: {game_id}")
                    in_gameplay = True
                    is_alive = True
                    await log_sender.send_log({"type": "status_update", "status": "playing", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": is_alive})
                    
                elif msg_type == "not_selected":
                    return
                    
                elif msg_type == "error":
                    error_code = msg.get("code")
                    log_error(bot_name, f"Matchmaking error: {error_code}")
                    return
                    
                elif msg_type in ("agent_view", "turn_advanced"):
                    has_logged_wait = False
                    if not has_logged_gameplay:
                        log_info(bot_name, "Ready in game. Active loop entered.")
                        has_logged_gameplay = True
                        
                    status = msg.get("status")
                    turn = msg.get("turn")
                    await log_sender.send_log({"type": "turn", "turn": turn, "status": status, "game_id": game_id})
                    
                    view = msg.get("view", {})
                    self_data = view.get("self", {})
                    is_alive = self_data.get("isAlive", True) and self_data.get("hp", 0) > 0
                    
                    await log_sender.send_agent_info(view)
                    
                    recent_logs = view.get("recentLogs", [])
                    if recent_logs:
                        for log_entry in recent_logs:
                            if isinstance(log_entry, dict):
                                entry_turn = log_entry.get("turn")
                                if entry_turn is not None and entry_turn != turn:
                                    continue
                                log_msg = log_entry.get("message", "")
                            else:
                                log_msg = str(log_entry)
                            if log_msg:
                                await log_sender.send_log({"type": "detail", "message": log_msg})
                    
                    if not is_alive:
                        log_info(bot_name, "Agent died.")
                        await log_sender.send_log({"type": "detail", "message": "=== AGENT ELIMINATED / DIED ==="})
                        await log_sender.send_log({"type": "status_update", "status": "playing", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": False})
                        break
                    elif status == "finished":
                        await log_sender.send_log({"type": "finished", "status": status})
                        await log_sender.send_log({"type": "status_update", "status": "lobby", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": is_alive})
                        break
                    else:
                        await log_sender.send_log({"type": "status_update", "status": "playing", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": is_alive})
                        
                elif msg_type == "waiting":
                    has_logged_gameplay = False
                    if not has_logged_wait:
                        log_info(bot_name, "Waiting for other agents...")
                        has_logged_wait = True
                    turn = msg.get("turn")
                    await log_sender.send_log({"type": "waiting", "turn": turn})
                    
                elif msg_type == "game_ended":
                    await log_sender.send_log({"type": "ended"})
                    await log_sender.send_log({"type": "status_update", "status": "lobby", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": is_alive})
                    break
                    
    except Exception as e:
        log_error(bot_name, f"Error in connection loop: {e}")
    finally:
        await log_sender.send_log({"type": "status_update", "status": "lobby", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": is_alive})
        await log_sender.close()