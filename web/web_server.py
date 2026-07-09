import asyncio
import json
import os
import websockets
import logging
import mimetypes
import http

logging.getLogger("websockets").setLevel(logging.CRITICAL)
logging.getLogger("websockets.server").setLevel(logging.CRITICAL)
logging.getLogger("websockets.protocol").setLevel(logging.CRITICAL)

PORT = int(os.getenv("PORT", 8000))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

connected_clients = set()
bot_history = {}

async def process_request(path, request_headers):
    clean_path = path.split("?")[0]
    if clean_path == "/":
        clean_path = "/index.html"
        
    file_path = os.path.join(DIRECTORY, clean_path.lstrip("/"))
    if not os.path.abspath(file_path).startswith(DIRECTORY):
        return http.HTTPStatus.FORBIDDEN, [], b"Forbidden"
        
    if os.path.exists(file_path) and os.path.isfile(file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"
        with open(file_path, "rb") as f:
            body = f.read()
        headers = [
            ("Content-Type", mime_type),
            ("Content-Length", str(len(body)))
        ]
        return http.HTTPStatus.OK, headers, body
        
    if clean_path == "/ws":
        return None
        
    return http.HTTPStatus.NOT_FOUND, [], b"Not Found"

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

        async def process_messages():
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

        await process_messages()
                
    except Exception:
        pass
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

async def start_web_server():
    await websockets.serve(handler, "0.0.0.0", PORT, process_request=process_request)