import asyncio
from src.connection import connect_and_play
from src.log.log_connections import log_info

async def main():
    while True:
        await connect_and_play()
        log_info("Session finished. Checking for next match in 5 seconds...")
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_info("Bot manually terminated by user.")