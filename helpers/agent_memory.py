import os
import json
from pathlib import Path
from typing import Dict, Any

class AgentMemoryManager:
    def __init__(self, filename: str = "claw-royale-context.json"):
        self.filepath = Path(os.path.expanduser("~")) / ".claw-royale" / filename
        self.memory: Dict[str, Any] = self._default_memory()

    def _default_memory(self) -> Dict[str, Any]:
        return {
            "overall": {
                "identity": {"name": "", "playstyle": ""},
                "strategy": {"deathzone": "", "guardians": "", "weather": ""},
                "history": {"totalGames": 0, "wins": 0, "avgKills": 0.0, "lessons": []}
            },
            "temp": {
                "gameId": "",
                "startedAt": "",
                "currentStrategy": "",
                "knownAgents": [],
                "notes": ""
            }
        }

    def load(self) -> Dict[str, Any]:
        if not self.filepath.exists():
            self.save()
            return self.memory
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.memory = json.load(f)
        except Exception:
            self.memory = self._default_memory()
        return self.memory

    def save(self):
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=4)

    def clear_temp(self):
        self.memory["temp"] = self._default_memory()["temp"]
        self.save()