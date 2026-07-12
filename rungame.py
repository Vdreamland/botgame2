import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.connection import connect_and_play
from src.config import load_active_accounts
from web.web_server import start_web_server

async def bot_worker(bot_name, api_key, entry_type):
    while True:
        try:
            await connect_and_play(bot_name, api_key, entry_type)
        except Exception as e:
            print(f"Error in bot worker {bot_name}: {e}")
        await asyncio.sleep(5)

async def main():
    asyncio.create_task(start_web_server())
    await asyncio.sleep(0.5)
    
    accounts = load_active_accounts()
    if not accounts:
        print("No active accounts found in .env.")
        return
        
    print(f"Starting {len(accounts)} bot(s)...")
    tasks = []
    for acc in accounts:
        tasks.append(bot_worker(acc["name"], acc["api_key"], acc["entry_type"]))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMulti-bot manager manually terminated.")