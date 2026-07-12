import asyncio
from helpers import AppConfig, ClawRoyaleAPIClient
from helpers.websocket_client import ClawRoyaleWebSocketClient

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
    
    try:
        print("Validating profile and active status...")
        profile = api_client.get_profile_me()
        active_games = profile.get("currentGames", [])
        
        is_already_in_game = False
        for game in active_games:
            if game.get("isAlive") and game.get("gameStatus") != "finished":
                is_already_in_game = True
                break
                
        print(f"Profile validated. Active session state: {is_already_in_game}")
    except Exception as e:
        print(f"Failed to validate account profile: {e}")
        return
        
    ws_client = ClawRoyaleWebSocketClient(api_key=bot.api_key, version=current_version, auth_type="mr-auth")
    
    if is_already_in_game:
        print("Active game detected. Resuming session...")
        await ws_client.connect_direct_agent()
    else:
        print(f"No active session. Entering matchmaking queue: {bot.room_preference}")
        await ws_client.connect_and_join(entry_type=bot.room_preference)

if __name__ == "__main__":
    asyncio.run(main())