import os
import requests
from src.websocket import GameWebSocket
from src.log.log_connections import log_info, log_error
from src.handshake_handler import handle_handshake
from src.game_loop_handler import run_game_loop

async def ensure_ready(api_key):
    api_url = os.environ.get("WS_JOIN_URL", "").replace("/ws/join", "/api").replace("wss://", "https://").replace("ws://", "http://")
    version_url = f"{api_url}/version"
    version_header = {"X-Version": os.environ.get("VERSION", "2.0.0")}
    try:
        res = requests.get(version_url, headers=version_header, timeout=5)
        if res.status_code == 426:
            log_error("X-Version mismatch with server. Please update .env VERSION.")
            return False
    except Exception:
        pass
    return True

async def connect_and_play(bot_name, api_key, entry_type):
    ready = await ensure_ready(api_key)
    if not ready:
        return

    url = os.environ.get("WS_JOIN_URL", "wss://cdn.clawroyale.ai/ws/join")
    headers = [
        ("Authorization", f"mr-auth {api_key}"),
        ("X-Version", os.environ.get("VERSION", "2.0.0"))
    ]

    async with GameWebSocket(url, headers) as ws:
        state = await handle_handshake(ws, bot_name, entry_type)
        if state in ["playing", "matchmaking"]:
            await run_game_loop(ws, bot_name, state)