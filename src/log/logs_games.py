import json
import websockets
import logging
import sys

logger = logging.getLogger("botgame.game")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

class GameLogSender:
    def __init__(self, bot_name, web_log_url):
        self.bot_name = bot_name
        self.web_log_url = web_log_url
        self.ws = None

    async def connect(self):
        try:
            self.ws = await websockets.connect(self.web_log_url)
        except Exception:
            self.ws = None
            logger.info(f"[{self.bot_name}] Web log server offline. Falling back to PowerShell.")

    async def close(self):
        if self.ws:
            await self.ws.close()

    async def send_log(self, payload):
        if self.ws:
            try:
                payload["bot_name"] = self.bot_name
                await self.ws.send(json.dumps(payload))
                return
            except Exception:
                self.ws = None
        
        if payload.get("type") == "turn":
            logger.info(f"[{self.bot_name}] [Turn {payload.get('turn')}] Status: {payload.get('status')}")
        elif payload.get("type") == "detail":
            logger.info(f"[{self.bot_name}]  -> Game Log: {payload.get('message')}")
        elif payload.get("type") == "waiting":
            logger.info(f"[{self.bot_name}] [Turn {payload.get('turn')}] Game status: waiting. Waiting for other agents...")
        elif payload.get("type") == "ended":
            logger.info(f"[{self.bot_name}] Game has ended.")
        elif payload.get("type") == "finished":
            logger.info(f"[{self.bot_name}] Game finished or Agent is no longer alive. Status: {payload.get('status')}")
        elif payload.get("type") == "reenter":
            logger.info(f"[{self.bot_name}] Gameplay frames detected. Re-entering active loop.")