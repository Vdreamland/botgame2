import os
from dotenv import load_dotenv

load_dotenv()

WS_JOIN_URL = os.getenv("WS_JOIN_URL", "wss://api.cloudroyale.xyz/ws/join")
DEFAULT_ENTRY_TYPE = os.getenv("ROOM_PREFERENCE", "free")
ROOM_PREFERENCE = DEFAULT_ENTRY_TYPE
WEB_LOG_URL = os.getenv("WEB_LOG_URL", "ws://127.0.0.1:8080")
VERSION = os.getenv("VERSION", "v2.0.0")
NUM_BOTS = int(os.getenv("NUM_BOTS", "0"))

def load_active_accounts():
    accounts = []
    for i in range(1, NUM_BOTS + 1):
        name = os.getenv(f"BOT{i}_NAME")
        api_key = os.getenv(f"BOT{i}_API_KEY")
        if name and api_key:
            accounts.append({
                "name": name,
                "api_key": api_key,
                "entry_type": ROOM_PREFERENCE
            })
    return accounts