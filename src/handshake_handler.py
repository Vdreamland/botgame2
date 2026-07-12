import asyncio
from src.log.log_connections import log_info, log_warning, log_error

async def handle_handshake(client, bot_name, entry_type, log_sender, credits, game_id, is_alive):
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
        return "blocked", credits

    if decision == "PAID_ONLY":
        log_error(bot_name, "Free entry not permitted (PAID_ONLY).")
        return "blocked", credits

    if decision in ("ASK_ENTRY_TYPE", "FREE_ONLY"):
        hello_msg = {
            "type": "hello",
            "entryType": entry_type
        }
        await client.send(hello_msg)

    return decision, credits