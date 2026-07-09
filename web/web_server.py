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

def run_http_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

connected_clients = set()

async def handler(websocket):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            websockets_to_remove = []
            for client in connected_clients:
                if client != websocket:
                    try:
                        await client.send(message)
                    except Exception:
                        websockets_to_remove.append(client)
            for client in websockets_to_remove:
                connected_clients.remove(client)
    except Exception:
        pass
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

async def start_web_server():
    t = threading.Thread(target=run_http_server, daemon=True)
    t.start()
    await websockets.serve(handler, "localhost", WS_PORT)