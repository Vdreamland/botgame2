import asyncio
from src.config import VERSION, WS_JOIN_URL, WEB_LOG_URL
from src.websocket import GameWebSocket
from src.log.log_connections import log_info, log_warning, log_error
from src.log.logs_games import GameLogSender

from src.ai.detector.agent_info import AgentInfoDetector
from src.ai.detector.enemy_info import EnemyInfoDetector
from src.ai.detector.deadzone_detector import DeadZoneDetector
from src.ai.detector.ground_item_detector import GroundItemDetector
from src.ai.memory import AgentMemory
from src.ai.decision_maker import get_decision

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
            welcome = await asyncio.wait_for(client.recv(), timeout=15.0)
            decision = welcome.get("decision")

            credits = welcome.get("account", {}).get("credits", 0)
            log_info(bot_name, f"WELCOME Handshake -> Decision: {decision}, Credits: {credits}")

            if decision == "ALREADY_IN_GAME":
                await log_sender.send_log({"type": "status_update", "status": "playing", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": is_alive})
            elif decision in ("ASK_ENTRY_TYPE", "FREE_ONLY"):
                await log_sender.send_log({"type": "status_update", "status": "lobby", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": is_alive})

            if decision == "BLOCKED":
                missing = welcome.get("readiness", {}).get("freeRoom", {}).get("missing", [])
                log_error(bot_name, f"Readiness BLOCKED. Reasons: {missing}")
                
                codes = []
                for m in missing:
                    if isinstance(m, dict):
                        codes.append(m.get("code"))
                    else:
                        codes.append(str(m))
                        
                if "ACTIVE_FREE_GAME_EXISTS" in codes:
                    log_warning(bot_name, "Previous session still active on server. Waiting 10 seconds...")
                    await asyncio.sleep(10.0)
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

            expect_immediate_frame = (decision == "ALREADY_IN_GAME")
            accumulated_events = []
            pending_messages = []
            last_logged_turn = -1

            memory = AgentMemory(bot_name)

            while True:
                try:
                    if pending_messages:
                        msg = pending_messages.pop(0)
                    else:
                        current_timeout = 5.0 if expect_immediate_frame else 120.0
                        msg = await asyncio.wait_for(client.recv(), timeout=current_timeout)
                        expect_immediate_frame = False
                except asyncio.TimeoutError:
                    if expect_immediate_frame:
                        log_warning(bot_name, "No immediate frames on ALREADY_IN_GAME. Post-death delay likely. Retrying shortly...")
                    else:
                        log_warning(bot_name, "Connection inactive for 120 seconds. Reconnecting...")
                    break

                msg_type = msg.get("type")

                active_game_id = msg.get("gameId")
                if active_game_id:
                    game_id = active_game_id

                if msg_type == "log":
                    log_data = msg.get("log") or {}
                    event_msg = log_data.get("message")
                    
                    if event_msg:
                        accumulated_events.append(event_msg)
                        
                    log_entry_type = log_data.get("type")
                    if log_entry_type == "death":
                        details = log_data.get("details", {})
                        target_name = details.get("targetName", "")
                        
                        if target_name.lower() == bot_name.lower():
                            log_info(bot_name, f"Death detected via global log: {event_msg}")
                            await log_sender.send_log({"type": "detail", "message": f"Fatal Event : {event_msg}"})
                            await log_sender.send_log({"type": "detail", "message": "=== AGENT ELIMINATED / DIED ==="})
                            await log_sender.send_log({"type": "status_update", "status": "playing", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": False})
                            log_info(bot_name, "Waiting 15 seconds for server to clear slot...")
                            await asyncio.sleep(15.0)
                            break
                    continue

                elif msg_type == "queued":
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

                    hp = self_data.get("hp", 0)
                    max_hp = self_data.get("maxHp") or self_data.get("max_hp", 100)
                    ep = self_data.get("ep", 0)
                    is_alive = self_data.get("isAlive", True) and hp > 0

                    if turn != last_logged_turn:
                        log_info(bot_name, f"Processing Turn {turn} (HP: {hp}/{max_hp}, EP: {ep}, Status: {status})")
                        last_logged_turn = turn

                    await asyncio.sleep(0.05)

                    while True:
                        try:
                            next_raw = await asyncio.wait_for(client.recv(), timeout=0.01)
                            if not next_raw:
                                continue
                            next_type = next_raw.get("type")
                            if next_type == "log":
                                log_data = next_raw.get("log") or {}
                                event_msg = log_data.get("message")
                                if event_msg:
                                    accumulated_events.append(event_msg)
                                log_entry_type = log_data.get("type")
                                if log_entry_type == "death":
                                    details = log_data.get("details", {})
                                    target_name = details.get("targetName", "")
                                    if target_name.lower() == bot_name.lower():
                                        pending_messages.append(next_raw)
                                        break
                            else:
                                pending_messages.append(next_raw)
                                break
                        except asyncio.TimeoutError:
                            break

                    recent_logs = view.get("recentLogs", []) or []
                    all_logs = list(recent_logs) + accumulated_events
                    accumulated_events = []

                    await log_sender.send_agent_info(view, turn, all_logs)

                    if recent_logs:
                        for log_entry in recent_logs:
                            log_msg = ""
                            if isinstance(log_entry, dict):
                                log_msg = log_entry.get("message", "")
                            else:
                                log_msg = str(log_entry)
                            if log_msg and bot_name.lower() in log_msg.lower():
                                log_info(bot_name, f"Event: {log_msg}")

                    if is_alive and status != "finished":
                        agent_info = AgentInfoDetector(view)
                        enemy_detector = EnemyInfoDetector(view)
                        deadzone_detector = DeadZoneDetector(view)
                        ground_detector = GroundItemDetector(view)

                        action = get_decision(view, agent_info, enemy_detector, deadzone_detector, ground_detector, memory)
                        if action:
                            thought = action.get("thought")
                            if thought:
                                await log_sender.send_log({"type": "detail", "message": f"AI Thought -> {thought}"})
                            
                            action_payload = {
                                "type": action.get("type", "action"),
                                "action": action.get("action"),
                                "data": action.get("data")
                            }
                            await client.send(action_payload)

                    if not is_alive:
                        log_info(bot_name, f"Death detected on Turn {turn}! HP: {hp}, isAlive: {self_data.get('isAlive')}. Exiting game loop...")
                        await log_sender.send_log({"type": "detail", "message": "=== AGENT ELIMINATED / DIED ==="})
                        await log_sender.send_log({"type": "status_update", "status": "playing", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": False})
                        await asyncio.sleep(15.0)
                        break
                    elif status == "finished":
                        log_info(bot_name, f"Game status finished on Turn {turn}. Exiting game loop...")
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
                    log_info(bot_name, "Game ended message received. Exiting game loop...")
                    await log_sender.send_log({"type": "ended"})
                    await log_sender.send_log({"type": "status_update", "status": "lobby", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": is_alive})
                    break

    except Exception as e:
        if "ConnectionClosed" in type(e).__name__:
            log_info(bot_name, f"Match finished or connection terminated. Sockets closed cleanly ({e}).")
        else:
            log_error(bot_name, f"Error in connection loop: {e}")
    finally:
        await log_sender.send_log({"type": "status_update", "status": "lobby", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": is_alive})
        await asyncio.sleep(0.5)
        await log_sender.close()