import asyncio
import json
import websockets
from src.config import API_KEY, VERSION, WS_JOIN_URL
from src.log.log_connections import log_info, log_warning, log_error

async def connect_and_play():
    headers = {
        "Authorization": f"mr-auth {API_KEY}",
        "X-Version": VERSION
    }
    
    log_info(f"Connecting to {WS_JOIN_URL}...")
    try:
        async with websockets.connect(WS_JOIN_URL, additional_headers=headers) as ws:
            log_info("Connected successfully. Waiting for welcome frame...")
            welcome_raw = await ws.recv()
            welcome = json.loads(welcome_raw)
            
            decision = welcome.get("decision")
            log_info(f"Welcome frame received. Decision: {decision}")
            
            if decision == "BLOCKED":
                missing = welcome.get("readiness", {}).get("freeRoom", {}).get("missing", [])
                log_error(f"Readiness BLOCKED. Reasons: {missing}")
                return
            
            if decision == "PAID_ONLY":
                log_error("Free entry not permitted (PAID_ONLY).")
                return
            
            if decision in ("ASK_ENTRY_TYPE", "FREE_ONLY"):
                hello_msg = {
                    "type": "hello",
                    "entryType": "free"
                }
                log_info("Sending hello frame (entryType: free)...")
                await ws.send(json.dumps(hello_msg))
            elif decision == "ALREADY_IN_GAME":
                log_info("Skipping hello frame, proxying directly to gameplay loop...")
            
            game_id = None
            agent_id = None
            
            while True:
                msg_raw = await ws.recv()
                msg = json.loads(msg_raw)
                msg_type = msg.get("type")
                
                if msg_type == "queued":
                    log_info("Enqueued in matchmaking. Waiting for match...")
                    continue
                
                elif msg_type == "assigned":
                    game_id = msg.get("gameId")
                    agent_id = msg.get("agentId")
                    log_info(f"Match found! Game ID: {game_id} | Agent ID: {agent_id}")
                    break
                
                elif msg_type == "not_selected":
                    log_warning("Not selected in this matchmaker cycle. Re-dialing required.")
                    return
                
                elif msg_type == "error":
                    error_code = msg.get("code")
                    log_error(f"Matchmaking error: {error_code}")
                    return
                
                else:
                    log_warning(f"Unexpected pre-game message: {msg}")
            
            log_info("Entering active gameplay loop on the same socket.")
            while True:
                game_msg_raw = await ws.recv()
                game_msg = json.loads(game_msg_raw)
                
                msg_type = game_msg.get("type")
                status = game_msg.get("status")
                turn = game_msg.get("turn")
                
                if msg_type in ("agent_view", "turn_advanced"):
                    view = game_msg.get("view", {})
                    self_data = view.get("self", {})
                    current_region = view.get("currentRegion", {})
                    hp = self_data.get("hp")
                    ep = self_data.get("ep")
                    region_name = current_region.get("name", "Unknown")
                    alive_agents = view.get("aliveCount", "Unknown")
                    
                    log_info(f"[Turn {turn}] Status: {status} | HP: {hp} | EP: {ep} | Region: {region_name} | Alive Agents: {alive_agents}")
                    
                    recent_logs = view.get("recentLogs", [])
                    if recent_logs:
                        for log_entry in recent_logs:
                            log_info(f" -> Game Log: {log_entry}")
                    
                    if status == "finished" or not self_data.get("isAlive", True):
                        log_info(f"Game finished or Agent is no longer alive. Status: {status}")
                        break
                
                elif msg_type == "waiting":
                    log_info(f"[Turn {turn}] Game status: waiting. Waiting for other agents...")
                
                elif msg_type == "game_ended":
                    log_info("Game has ended.")
                    break
                
                else:
                    log_info(f"Incoming game message: {msg_type}")
                    
    except websockets.exceptions.ConnectionClosed as e:
        log_error(f"WebSocket connection closed: {e}")
    except Exception as e:
        log_error(f"Error in connection loop: {e}")