import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

WS_JOIN_URL = os.getenv("WS_JOIN_URL", "wss://cdn.clawroyale.ai/ws/join")
ACCOUNTS_FILE = os.getenv("ACCOUNTS_FILE", "accounts.json")
DEFAULT_ENTRY_TYPE = os.getenv("ENTRY_TYPE", "free")

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

try:
    max_bots_str = os.getenv("MAX_ACTIVE_BOTS", "-1")
    MAX_ACTIVE_BOTS = int(max_bots_str) if max_bots_str else -1
except ValueError:
    MAX_ACTIVE_BOTS = -1

def load_active_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        raise FileNotFoundError(f"Accounts file not found: {ACCOUNTS_FILE}")
        
    with open(ACCOUNTS_FILE, "r") as f:
        accounts = json.load(f)
        
    if not isinstance(accounts, list):
        raise ValueError("Accounts file must contain a JSON array")
        
    processed = []
    for index, acc in enumerate(accounts):
        name = acc.get("name", f"BOT_{index + 1}")
        api_key = acc.get("api_key", "")
        entry_type = acc.get("entry_type", DEFAULT_ENTRY_TYPE)
        if not entry_type:
            entry_type = DEFAULT_ENTRY_TYPE
            
        processed.append({
            "name": name,
            "api_key": api_key,
            "entry_type": entry_type
        })
        
    if MAX_ACTIVE_BOTS > 0:
        return processed[:MAX_ACTIVE_BOTS]
        
    return processed