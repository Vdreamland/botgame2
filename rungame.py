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
    
    temp_client = ClawRoyaleAPIClient(api_key=bot.api_key, version="", auth_type="mr-auth")
    try:
        version_info = temp_client.get_version()
        current_version = version_info.get("version")
    except Exception as e:
        print(f"Failed to fetch live version: {e}")
        return

    api_client = ClawRoyaleAPIClient(api_key=bot.api_key, version=current_version, auth_type="mr-auth")
    
    # Inisialisasi set memori lokal untuk mencatat gameId yang sudah mati
    dead_games = set()
    
    while True:
        print(f"Initializing bot instance: {bot.name} (Index: {bot.index})")
        print("Retrieving dynamic authoritative game version...")
        print(f"Dynamic game version: {current_version}")
        print("Validating profile and active status...")
        
        try:
            profile = api_client.get_profile_me()
            profile_data = profile.get("data", {}) if "data" in profile else profile
            active_games = profile_data.get("currentGames", [])
            
            is_already_in_game = False
            for game in active_games:
                g_id = game.get("gameId")
                
                # Jika gameId ini sudah pernah tercatat mati di memori lokal, abaikan
                if g_id in dead_games:
                    continue
                    
                if game.get("isAlive") and game.get("gameStatus") != "finished":
                    is_already_in_game = True
                    break
                    
            print(f"Profile validated. Active session state: {is_already_in_game}")
            
            ws_client = ClawRoyaleWebSocketClient(
                api_key=bot.api_key, 
                version=current_version, 
                auth_type="mr-auth",
                message_handler=handle_game_message,
                dead_games=dead_games
            )
            
            if is_already_in_game:
                print("Active game detected. Resuming session...")
                await ws_client.connect_direct_agent()
            else:
                print(f"No active session. Entering matchmaking queue: {bot.room_preference}")
                await ws_client.connect_and_join(entry_type=bot.room_preference)
                
        except Exception:
            pass
            
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())