import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "")
VERSION = os.getenv("VERSION", "")
WS_JOIN_URL = os.getenv("WS_JOIN_URL", "wss://cdn.clawroyale.ai/ws/join")

if not API_KEY or not VERSION:
    raise ValueError("API_KEY and VERSION must be set in .env")