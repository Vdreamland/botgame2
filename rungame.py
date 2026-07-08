import os
import sys
import time
import asyncio
import requests
from dotenv import load_dotenv
from src.config import get_headers, get_all_bot_keys
from src.api import get_account_state, redeem_welcome_code
from src.websocket_handler import run_ws_loop

load_dotenv()

active_bots = {}

async def run_bot(bot_name, api_key):
 headers = get_headers(api_key)
 first_run = True
 dead_games = set()
 while True:
  account_data = get_account_state(headers=headers)
  if not account_data:
   print(f"[{bot_name}] Failed to retrieve account data. Retrying in 10 seconds...")
   await asyncio.sleep(10)
   continue

  if first_run:
   print(f"[{bot_name}] Account loaded: {account_data.get('name')} | Balance: {account_data.get('balance')} sMoltz")
   print(f"[{bot_name}] Checking onboarding bundle claim (WELCOME)...")
   redeem_welcome_code(headers=headers)
   first_run = False

  current_games = account_data.get("currentGames", [])
  active_game = next((g for g in current_games if g.get("isAlive") and g.get("gameStatus") != "finished" and g.get("gameId") not in dead_games), None)

  if not active_game:
   active_bots[bot_name] = "idle"

  try:
   active_bots[bot_name] = "playing"
   success, played_game_id = await run_ws_loop(active_game=active_game, headers=headers)
   if success is False and played_game_id:
    dead_games.add(played_game_id)
   active_bots[bot_name] = "finished"
   print(f"\n[{bot_name}] Session finished. Checking for next match in 5 seconds...")
   await asyncio.sleep(5)
  except asyncio.CancelledError:
   break
  except Exception as e:
   print(f"[{bot_name}] Error in connection loop: {e}")
   active_bots[bot_name] = "reconnecting"
   print(f"[{bot_name}] Reconnecting in 1 second...")
   await asyncio.sleep(1)

async def amain(tasks):
 await asyncio.gather(*tasks)

def main():
 bots = get_all_bot_keys()
 if not bots:
  print("No active bot API keys found in .env.")
  return

 print(f"Loaded {len(bots)} bots. Starting concurrent gameplay loop...")

 global active_bots
 active_bots = {bot_name: "initializing" for bot_name, _ in bots}

 tasks = []
 for bot_name, api_key in bots:
  tasks.append(run_bot(bot_name, api_key))

 try:
  asyncio.run(amain(tasks))
 except KeyboardInterrupt:
  print("\nShutting down bot safely...")
  sys.exit(0)

from web.web_server import start_server

if __name__ == "__main__":
 start_server()
 main()