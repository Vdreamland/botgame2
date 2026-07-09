import asyncio
from src.config import load_active_accounts
from src.connection import connect_and_play
from src.log.log_connections import log_info, log_error

async def bot_worker(account):
    bot_name = account["name"]
    api_key = account["api_key"]
    entry_type = account["entry_type"]
    
    while True:
        try:
            await connect_and_play(bot_name, api_key, entry_type)
        except Exception as e:
            log_error(bot_name, f"Worker exception occurred: {e}")
            
        log_info(bot_name, "Session finished. Checking for next match in 5 seconds...")
        await asyncio.sleep(5)

async def main():
    try:
        accounts = load_active_accounts()
    except Exception as e:
        print(f"Failed to load accounts configuration: {e}")
        return
        
    if not accounts:
        print("No active accounts found to run.")
        return
        
    print(f"Starting {len(accounts)} bot(s)...")
    tasks = [asyncio.create_task(bot_worker(acc)) for acc in accounts]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Multi-bot manager manually terminated.")