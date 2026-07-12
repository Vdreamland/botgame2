import asyncio
from helpers import AppConfig, ClawRoyaleAPIClient
from helpers.websocket_client import ClawRoyaleWebSocketClient
from games_log import handle_game_message

async def main():
    config = AppConfig()
    if not config.bots:
        print("No bot accounts configured in .env. Exiting.")
        return
        
    bot = config.bots[0]
    print(f"Initializing bot instance: {bot.name} (Index: {bot.index})")
    
    temp_client = ClawRoyaleAPIClient(api_key=bot.api_key, version="", auth_type="mr-auth")
    try:
        print("Retrieving dynamic authoritative game version...")
        version_info = temp_client.get_version()
        current_version = version_info.get("version")
        print(f"Dynamic game version: {current_version}")
    except Exception as e:
        print(f"Failed to fetch live version: {e}")
        return

    api_client = ClawRoyaleAPIClient(api_key=bot.api_key, version=current_version, auth_type="mr-auth")
    
    print("[Loop] Starting automated match supervisor...")
    while True:
        try:
            print("\n[Loop] Fetching active session status from profile...")
            profile = api_client.get_profile_me()
            profile_data = profile.get("data", {}) if "data" in profile else profile
            active_games = profile_data.get("currentGames", [])
            
            is_already_in_game = False
            for game in active_games:
                if game.get("isAlive") and game.get("gameStatus") != "finished":
                    is_already_in_game = True
                    break
                    
            ws_client = ClawRoyaleWebSocketClient(
                api_key=bot.api_key, 
                version=current_version, 
                auth_type="mr-auth",
                message_handler=handle_game_message
            )
            
            if is_already_in_game:
                print("[Loop] Active session found. Resuming game...")
                await ws_client.connect_direct_agent()
            else:
                print(f"[Loop] No active session. Queueing for a new '{bot.room_preference.upper()}' match...")
                await ws_client.connect_and_join(entry_type=bot.room_preference)
                
        except Exception as e:
            print(f"[Loop Error] {e}")
            
        print("[Loop] Session terminated. Checking status again in 5 seconds...")
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())