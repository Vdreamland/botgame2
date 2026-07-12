import asyncio
from src.config import VERSION, WS_JOIN_URL, WEB_LOG_URL
from src.websocket import GameWebSocket
from src.log.log_connections import log_info, log_warning, log_error
from src.log.logs_games import GameLogSender
from src.handshake_handler import handle_handshake
from src.game_loop_handler import run_game_loop

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

    try:
        async with GameWebSocket(WS_JOIN_URL, headers) as client:
            decision, credits = await handle_handshake(
                client, bot_name, entry_type, log_sender, credits, game_id, is_alive
            )
            
            if decision != "blocked":
                await run_game_loop(
                    client, bot_name, entry_type, log_sender, decision, credits, game_id, is_alive
                )

    except Exception as e:
        if "ConnectionClosed" in type(e).__name__:
            log_info(bot_name, f"Match finished or connection terminated. Sockets closed cleanly ({e}).")
        else:
            log_error(bot_name, f"Error in connection loop: {e}")
    finally:
        await log_sender.send_log({"type": "status_update", "status": "lobby", "credits": credits, "game_id": game_id, "entry_type": entry_type, "is_alive": is_alive})
        await asyncio.sleep(0.5)
        await log_sender.close()