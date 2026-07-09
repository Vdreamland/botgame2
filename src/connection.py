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
    
    log_info(bot_name, "Connecting to game server...")
    log_sender = GameLogSender(bot_name, WEB_LOG_URL)
    await log_sender.connect()
    
    credits = 0
    game_id = None
    await log_sender.send_log({"type": "status_update", "status": "lobby", "credits": credits, "game_id": game_id})
    
    try:
        async with GameWebSocket(WS_JOIN_URL, headers) as client:
            welcome = await client.recv()
            decision = welcome.get("decision")
            
            credits = welcome.get("account", {}).get("credits", 0)
            
            if decision == "ALREADY_IN_GAME":
                log_info(bot_name, "Active session detected. Rejoining match room...")
                await log_sender.send_log({"type": "status_update", "status": "playing", "credits": credits, "game_id": game_id})
            elif decision in ("ASK_ENTRY_TYPE", "FREE_ONLY"):
                log_info(bot_name, "Authentication successful. Entering lobby...")
                await log_sender.send_log({"type": "status_update", "status": "lobby", "credits": credits, "game_id": game_id})
            
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
                msg = await client.recv()
                msg_type = msg.get("type")
                
                active_game_id = msg.get("gameId")
                if active_game_id:
                    game_id = active_game_id
                
                if msg_type == "queued":
                    log_info(bot_name, "Queue active. Searching for available match cycle...")
                    await log_sender.send_log({"type": "status_update", "status": "matchmaking", "credits": credits, "game_id": game_id})
                    
                elif msg_type == "assigned":
                    game_id = msg.get("gameId")
                    agent_id = msg.get("agentId")
                    log_info(bot_name, f"Match found! Room ID: {game_id}. Entering room...")
                    in_gameplay = True
                    await log_sender.send_log({"type": "status_update", "status": "playing", "credits": credits, "game_id": game_id})
                    
                elif msg_type == "not_selected":
                    log_warning(bot_name, "Not selected in this cycle. Retrying matchmaker...")
                    return
                    
                elif msg_type == "error":
                    error_code = msg.get("code")
                    log_error(bot_name, f"Matchmaking error: {error_code}")
                    return
                    
                elif msg_type in ("agent_view", "turn_advanced"):
                    status = msg.get("status")
                    turn = msg.get("turn")
                    await log_sender.send_log({"type": "turn", "turn": turn, "status": status, "game_id": game_id})
                    
                    view = msg.get("view", {})
                    self_data = view.get("self", {})
                    is_alive = self_data.get("isAlive", True)
                    
                    if not is_alive:
                        await log_sender.send_log({"type": "status_update", "status": "dead", "credits": credits, "game_id": game_id})
                    elif status == "finished":
                        await log_sender.send_log({"type": "status_update", "status": "lobby", "credits": credits, "game_id": game_id})
                        break
                    else:
                        await log_sender.send_log({"type": "status_update", "status": "playing", "credits": credits, "game_id": game_id})
                        
                elif msg_type == "waiting":
                    turn = msg.get("turn")
                    await log_sender.send_log({"type": "waiting", "turn": turn})
                    
                elif msg_type == "game_ended":
                    await log_sender.send_log({"type": "status_update", "status": "lobby", "credits": credits, "game_id": game_id})
                    break
                    
    except Exception as e:
        log_error(bot_name, f"Error in connection loop: {e}")
    finally:
        await log_sender.send_log({"type": "status_update", "status": "lobby", "credits": credits, "game_id": game_id})
        await log_sender.close()