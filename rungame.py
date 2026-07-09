import asyncio
import sys
import os
from src.config import load_active_accounts, DEFAULT_ENTRY_TYPE
from src.connection import connect_and_play
from src.log.log_connections import log_error, log_info
from web.web_server import start_web_server

async def bot_worker(bot_name, api_key, entry_type):
    while True:
        try:
            await connect_and_play(bot_name, api_key, entry_type)
        except Exception as e:
            log_error(bot_name, f"Bot crashed: {e}")
        log_info(bot_name, "Reconnecting in 5 seconds...")
        await asyncio.sleep(5)

async def main():
    start_web_server()
    await asyncio.sleep(1)

    accounts = load_active_accounts()
    if not accounts:
        log_error("SYSTEM", "No active accounts found in .env")
        return

    tasks = []
    for account in accounts:
        bot_name = account.get("name")
        api_key = account.get("api_key")
        entry_type = account.get("entry_type") or DEFAULT_ENTRY_TYPE
        if bot_name and api_key:
            tasks.append(asyncio.create_task(bot_worker(bot_name, api_key, entry_type)))

    if tasks:
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_info("SYSTEM", "Shutdown requested...")
        sys.exit(0)