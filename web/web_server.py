import asyncio
import http.server
import socketserver
import threading
import json
import os
import websockets
import logging

logging.getLogger("websockets").setLevel(logging.CRITICAL)
logging.getLogger("websockets.server").setLevel(logging.CRITICAL)
logging.getLogger("websockets.protocol").setLevel(logging.CRITICAL)

PORT = 8000
WS_PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        pass

def run_http_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

connected_clients = set()
connected_browsers = set()
connected_bots = set()
bot_history = {}

async def handler(websocket):
    connected_clients.add(websocket)
    connected_browsers.add(websocket)
 
    is_bot = False

    async def broadcast(message):
        websockets_to_remove = []
        for client in list(connected_browsers):
            if client != websocket:
                try:
                    await asyncio.wait_for(client.send(message), timeout=1.0)
                except Exception:
                    websockets_to_remove.append(client)
        for client in websockets_to_remove:
            if client in connected_browsers:
                connected_browsers.remove(client)
            if client in connected_clients:
                connected_clients.remove(client)

    async def process_messages():
        nonlocal is_bot
        async for message in websocket:
            try:
                payload = json.loads(message)
                bot_name = payload.get("bot_name")
                if bot_name:
                    is_bot = True
                    if websocket in connected_browsers:
                        connected_browsers.remove(websocket)
                    connected_bots.add(websocket)
                    if bot_name not in bot_history:
                        bot_history[bot_name] = []
                    bot_history[bot_name].append(message)
                    if len(bot_history[bot_name]) > 500:
                        bot_history[bot_name].pop(0)
            except Exception:
                pass
 
            await broadcast(message)

    processor_task = asyncio.create_task(process_messages())

    await asyncio.sleep(0.1)

    if not is_bot:
        for bot_name, history in bot_history.items():
            for cached_msg in history:
                try:
                    await websocket.send(cached_msg)
                except Exception:
                    pass

    try:
        await processor_task
    except Exception:
        pass
    finally:
        processor_task.cancel()
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        if websocket in connected_browsers:
            connected_browsers.remove(websocket)
        if websocket in connected_bots:
            connected_bots.remove(websocket)

async def start_web_server():
    t = threading.Thread(target=run_http_server, daemon=True)
    t.start()
    await websockets.serve(handler, "127.0.0.1", WS_PORT)