import logging
import sys

logger = logging.getLogger("botgame.connection")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

def log_info(bot_name, message):
    logger.info(f"[{bot_name}] {message}")

def log_warning(bot_name, message):
    logger.warning(f"[{bot_name}] {message}")

def log_error(bot_name, message):
    logger.error(f"[{bot_name}] {message}")