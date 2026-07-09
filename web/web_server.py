import asyncio
import os
import json
import logging
from aiohttp import web

logging.getLogger("aiohttp").setLevel(logging.CRITICAL)

PORT = int(os.getenv("PORT", 8000))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

connected_clients = set()
bot_history = {}

async def index_handler(request):
    return web.FileResponse(os.path.join(DIRECTORY, "index.html"))

async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    connected_clients.add(ws)
    
    for bot_name, history in bot_history.items():
        for cached_msg in history:
            try:
                await ws.send_str(cached_msg)
            except Exception:
                pass
                
    try:
        async def broadcast(message):
            websockets_to_remove = []
            for client in connected_clients:
                if client != ws:
                    try:
                        await client.send_str(message)
                    except Exception:
                        websockets_to_remove.append(client)
            for client in websockets_to_remove:
                if client in connected_clients:
                    connected_clients.remove(client)

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                message = msg.data
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
            elif msg.type == web.WSMsgType.ERROR:
                pass
    except Exception:
        pass
    finally:
        if ws in connected_clients:
            connected_clients.remove(ws)
    return ws

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_get("/ws", ws_handler)
    app.router.add_static("/", path=DIRECTORY, name="static")
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()