import asyncio
from src.log.log_connections import log_info, log_warning, log_error

async def handle_handshake(ws, bot_name, entry_type):
    try:
        welcome = await ws.recv()
        w_type = welcome.get("type")
        if w_type == "welcome":
            decision = welcome.get("decision")
            if decision == "ALREADY_IN_GAME":
                log_info(f"[{bot_name}] Already in game session. Bypassing handshake...")
                return "playing"
            elif decision == "BLOCKED":
                penalty_seconds = welcome.get("penaltySeconds", 10)
                log_warning(f"[{bot_name}] Blocked (active free game exists). Waiting {penalty_seconds}s before exit...")
                await asyncio.sleep(penalty_seconds)
                return "blocked"
            elif decision in ["ASK_ENTRY_TYPE", "FREE_ONLY"]:
                selected = entry_type
                if decision == "FREE_ONLY" and entry_type == "paid":
                    log_warning(f"[{bot_name}] Paid room requested but server restricted to FREE_ONLY. Overriding...")
                    selected = "free"
                await ws.send({"type": "hello", "entryType": selected})
                log_info(f"[{bot_name}] Sent hello with entryType: {selected}")
                return "matchmaking"
            else:
                log_error(f"[{bot_name}] Unknown welcome decision: {decision}")
                return "error"
        else:
            log_error(f"[{bot_name}] Expected welcome frame, got: {w_type}")
            return "error"
    except Exception as e:
        log_error(f"[{bot_name}] Exception during handshake: {e}")
        return "error"