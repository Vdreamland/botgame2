import asyncio
import http.server
import socketserver
import threading
import json
import os
import websockets

PORT = 8000
WS_PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        pass

def run_http_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

connected_clients = set()
bot_history = {}

async def handler(websocket):
    connected_clients.add(websocket)
    
    for bot_name, history in bot_history.items():
        for cached_msg in history:
            try:
                await websocket.send(cached_msg)
            except Exception:
                pass
                
    try:
        async def broadcast(message):
            websockets_to_remove = []
            for client in connected_clients:
                if client != websocket:
                    try:
                        await client.send(message)
                    except Exception:
                        websockets_to_remove.append(client)
            for client in websockets_to_remove:
                if client in connected_clients:
                    connected_clients.remove(client)

        async for message in websocket:
            try:
                payload = json.loads(message)
                bot_name = payload.get("bot_name")
                if bot_name:
                    if bot_name not in bot_history:
                        bot_history[bot_name] = []
                    bot_history[bot_name].append(message)
                    if len(bot_history[bot_name]) > 50:
                        bot_history[bot_name].pop(0)
            except Exception:
                pass
            await broadcast(message)
            
    except Exception:
        pass
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

async def start_web_server():
    t = threading.Thread(target=run_http_server, daemon=True)
    t.start()
    await websockets.serve(handler, "localhost", WS_PORT)