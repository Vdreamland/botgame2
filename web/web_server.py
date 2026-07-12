import asyncio
import json
import threading
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

app_http = FastAPI()
app_http.mount("/", StaticFiles(directory="web", html=True), name="web")

app_ws = FastAPI()

connected_browsers = set()
connected_bots = set()
bot_history = {}

@app_ws.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    is_bot = False
    bot_name = None
    
    try:
        try:
            message_str = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
            payload = json.loads(message_str)
            bot_name = payload.get("bot_name")
        except asyncio.TimeoutError:
            pass
        except Exception:
            pass

        if bot_name:
            is_bot = True
            connected_bots.add(websocket)
            if bot_name not in bot_history:
                bot_history[bot_name] = []
            bot_history[bot_name].append(message_str)
            if len(bot_history[bot_name]) > 500:
                bot_history[bot_name].pop(0)
            await broadcast(message_str)
        else:
            connected_browsers.add(websocket)
            for b_name, history in bot_history.items():
                for cached_msg in history:
                    try:
                        await websocket.send_text(cached_msg)
                    except Exception:
                        pass

        while True:
            message_str = await websocket.receive_text()
            if is_bot:
                payload = json.loads(message_str)
                b_name = payload.get("bot_name")
                if b_name:
                    if b_name not in bot_history:
                        bot_history[b_name] = []
                    bot_history[b_name].append(message_str)
                    if len(bot_history[b_name]) > 500:
                        bot_history[b_name].pop(0)
                await broadcast(message_str)

    except WebSocketDisconnect:
        pass
    finally:
        if websocket in connected_browsers:
            connected_browsers.remove(websocket)
        if websocket in connected_bots:
            connected_bots.remove(websocket)

async def broadcast(message: str):
    browsers_to_remove = []
    for client in list(connected_browsers):
        try:
            await client.send_text(message)
        except Exception:
            browsers_to_remove.append(client)
    for client in browsers_to_remove:
        if client in connected_browsers:
            connected_browsers.remove(client)

async def start_web_server():
    t_http = threading.Thread(
        target=lambda: uvicorn.run(app_http, host="127.0.0.1", port=8000, log_level="critical"),
        daemon=True
    )
    t_http.start()
    
    config = uvicorn.Config(app_ws, host="127.0.0.1", port=8080, log_level="critical")
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())

if __name__ == "__main__":
    async def main():
        await start_web_server()
        while True:
            await asyncio.sleep(3600)
    asyncio.run(main())