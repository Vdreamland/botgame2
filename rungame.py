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
    
    dead_games = set()
    wait_for_game_id = None
    
    while True:
        try:
            profile = api_client.get_profile_me()
            profile_data = profile.get("data", {}) if "data" in profile else profile
            active_games = profile_data.get("currentGames", [])
            
            # Jika sedang menunggu game lama selesai, cek statusnya secara senyap
            if wait_for_game_id:
                is_still_running = False
                for game in active_games:
                    if game.get("gameId") == wait_for_game_id and game.get("gameStatus") != "finished":
                        is_still_running = True
                        break
                if is_still_running:
                    # Tunggu senyap selama 10 detik tanpa mencetak log inisialisasi apa pun
                    await asyncio.sleep(10)
                    continue
                else:
                    print(f"\n[Lobby] Previous game {wait_for_game_id} has finished. Resuming matchmaking.")
                    wait_for_game_id = None

            is_already_in_game = False
            for game in active_games:
                g_id = game.get("gameId")
                
                if g_id in dead_games:
                    continue
                    
                if game.get("isAlive") and game.get("gameStatus") != "finished":
                    is_already_in_game = True
                    break
            
            # Tampilkan log awal koneksi murni
            print(f"Initializing bot instance: {bot.name} (Index: {bot.index})")
            print("Retrieving dynamic authoritative game version...")
            print(f"Dynamic game version: {current_version}")
            print("Validating profile and active status...")
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
                result = await ws_client.connect_and_join(entry_type=bot.room_preference)
                
                # Jika matchmaking diblokir karena ada game aktif lain yang belum selesai
                if result == "BLOCKED":
                    for game in active_games:
                        if game.get("gameStatus") != "finished":
                            wait_for_game_id = game.get("gameId")
                            print(f"[Lobby] Matchmaking is currently blocked. Waiting for previous game {wait_for_game_id} to finish...")
                            break
                            
        except Exception:
            pass
            
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())