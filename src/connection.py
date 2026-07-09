import asyncio
from src.config import VERSION, WS_JOIN_URL
from src.websocket import GameWebSocket
from src.log.log_connections import log_info, log_warning, log_error

async def connect_and_play(bot_name, api_key, entry_type):
    if not api_key:
        log_error(bot_name, "API key is empty. Skipping connection.")
        return

    headers = {
        "Authorization": f"mr-auth {api_key}",
        "X-Version": VERSION
    }
    
    log_info(bot_name, f"Connecting to {WS_JOIN_URL}...")
    
    try:
        async with GameWebSocket(WS_JOIN_URL, headers) as client:
            log_info(bot_name, "Connected successfully. Waiting for welcome frame...")
            
            welcome = await client.recv()
            decision = welcome.get("decision")
            log_info(bot_name, f"Welcome frame received. Decision: {decision}")
            
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
                log_info(bot_name, f"Sending hello frame (entryType: {entry_type})...")
                await client.send(hello_msg)
            elif decision == "ALREADY_IN_GAME":
                log_info(bot_name, "Skipping hello frame, proxying directly to gameplay loop...")
            
            game_id = None
            agent_id = None
            in_gameplay = False
            
            while True:
                msg = await client.recv()
                msg_type = msg.get("type")
                
                if msg_type == "queued":
                    log_info(bot_name, "Enqueued in matchmaking. Waiting for match...")
                    
                elif msg_type == "assigned":
                    game_id = msg.get("gameId")
                    agent_id = msg.get("agentId")
                    log_info(bot_name, f"Match found! Game ID: {game_id} | Agent ID: {agent_id}")
                    in_gameplay = True
                    
                elif msg_type == "not_selected":
                    log_warning(bot_name, "Not selected in this matchmaker cycle. Re-dialing required.")
                    return
                    
                elif msg_type == "error":
                    error_code = msg.get("code")
                    log_error(bot_name, f"Matchmaking error: {error_code}")
                    return
                    
                elif msg_type in ("agent_view", "turn_advanced"):
                    if not in_gameplay:
                        log_info(bot_name, "Gameplay frames detected. Re-entering active loop.")
                        in_gameplay = True
                        
                    status = msg.get("status")
                    turn = msg.get("turn")
                    log_info(bot_name, f"[Turn {turn}] Status: {status}")
                    
                    view = msg.get("view", {})
                    self_data = view.get("self", {})
                    recent_logs = view.get("recentLogs", [])
                    if recent_logs:
                        for log_entry in recent_logs:
                            log_info(bot_name, f" -> Game Log: {log_entry}")
                    
                    if status == "finished" or not self_data.get("isAlive", True):
                        log_info(bot_name, f"Game finished or Agent is no longer alive. Status: {status}")
                        break
                        
                elif msg_type == "waiting":
                    turn = msg.get("turn")
                    log_info(bot_name, f"[Turn {turn}] Game status: waiting. Waiting for other agents...")
                    
                elif msg_type == "game_ended":
                    log_info(bot_name, "Game has ended.")
                    break
                    
                else:
                    log_info(bot_name, f"Incoming game message: {msg_type}")
                    
    except Exception as e:
        log_error(bot_name, f"Error in connection loop: {e}")