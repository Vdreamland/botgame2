import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

WS_JOIN_URL = os.getenv("WS_JOIN_URL", "wss://cdn.clawroyale.ai/ws/join")
DEFAULT_ENTRY_TYPE = os.getenv("ROOM_PREFERENCE", os.getenv("ENTRY_TYPE", "free"))

WEB_LOG_URL = os.getenv("WEB_LOG_URL", "ws://127.0.0.1:8080")

api_base = "https://cdn.clawroyale.ai/api"
if "moltyroyale.com" in WS_JOIN_URL:
    api_base = "https://cdn.moltyroyale.com/api"

fetched_version = None
try:
    with urllib.request.urlopen(f"{api_base}/version", timeout=5) as response:
        if response.status == 200:
            res_data = json.loads(response.read().decode())
            if isinstance(res_data, dict):
                if res_data.get("success") and isinstance(res_data.get("data"), dict):
                    fetched_version = res_data["data"].get("version")
                else:
                    fetched_version = res_data.get("version")
except Exception:
    pass

VERSION = fetched_version or os.getenv("VERSION", "")
if not VERSION:
    raise ValueError("VERSION must be set in .env (failed to fetch version dynamically)")

NUM_BOTS = int(os.getenv("NUM_BOTS", "0"))

def load_active_accounts():
    processed = []
    for i in range(1, NUM_BOTS + 1):
        name = os.getenv(f"BOT{i}_NAME")
        api_key = os.getenv(f"BOT{i}_API_KEY")
        if name and api_key:
            processed.append({
                "name": name,
                "api_key": api_key,
                "entry_type": DEFAULT_ENTRY_TYPE
            })
    return processed