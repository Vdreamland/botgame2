import logging
import sys

logger = logging.getLogger("botgame.game")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

def log_game_turn(bot_name, turn, status):
    logger.info(f"[{bot_name}] [Turn {turn}] Status: {status}")

def log_game_detail(bot_name, log_entry):
    logger.info(f"[{bot_name}]  -> Game Log: {log_entry}")

def log_game_waiting(bot_name, turn):
    logger.info(f"[{bot_name}] [Turn {turn}] Game status: waiting. Waiting for other agents...")

def log_game_ended(bot_name):
    logger.info(f"[{bot_name}] Game has ended.")

def log_game_finished(bot_name, status):
    logger.info(f"[{bot_name}] Game finished or Agent is no longer alive. Status: {status}")

def log_game_reenter(bot_name):
    logger.info(f"[{bot_name}] Gameplay frames detected. Re-entering active loop.")