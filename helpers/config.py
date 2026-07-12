import os
from typing import List
from dotenv import load_dotenv

class BotAccountConfig:
    def __init__(self, index: int, name: str, api_key: str, room_preference: str):
        self.index = index
        self.name = name
        self.api_key = api_key
        self.room_preference = room_preference

class AppConfig:
    def __init__(self):
        load_dotenv()
        self.num_bots: int = int(os.getenv("NUM_BOTS", "1"))
        self.global_room_preference: str = os.getenv("ROOM_PREFERENCE", "free")
        self.bots: List[BotAccountConfig] = []
        self._load_bot_accounts()

    def _load_bot_accounts(self):
        for i in range(1, self.num_bots + 1):
            name = os.getenv(f"BOT{i}_NAME")
            api_key = os.getenv(f"BOT{i}_API_KEY")
            
            if not name or not api_key:
                continue
                
            room_pref = os.getenv(f"BOT{i}_ROOM_PREFERENCE", self.global_room_preference)
            self.bots.append(
                BotAccountConfig(
                    index=i,
                    name=name,
                    api_key=api_key,
                    room_preference=room_pref
                )
            )