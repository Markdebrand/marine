# aisstream_client.py
"""
Cliente y manejador de stream AISSTREAM para integración en FastAPI.
"""
import asyncio
import websockets
import json
import threading
from datetime import datetime, timezone
from typing import Dict, List
import os

from fastapi import APIRouter

AISSTREAM_API_KEY = os.getenv("AISSTREAM_API_KEY")
BOUNDING_BOXES = [[[-90, -180], [90, 180]]]

# Historial de posiciones por barco: { ship_id: [[lat, lon], ...] }
ships: Dict[str, List[List[float]]] = {}
ships_lock = threading.Lock()

router = APIRouter()

@router.get("/aisstream/positions")
def get_positions():
    with ships_lock:
        data = [[ship_id, positions] for ship_id, positions in ships.items()]
    return data

async def connect_ais_stream():
    async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
        subscribe_message = {"APIKey": AISSTREAM_API_KEY, "BoundingBoxes": BOUNDING_BOXES}
        subscribe_message_json = json.dumps(subscribe_message)
        await websocket.send(subscribe_message_json)
        async for message_json in websocket:
            try:
                message = json.loads(message_json)
                if "MessageType" not in message:
                    continue
                if message["MessageType"] == "PositionReport":
                    ais_message = message['Message']['PositionReport']
                    ship_id = str(ais_message['UserID'])
                    lat = float(ais_message['Latitude'])
                    lon = float(ais_message['Longitude'])
                    log_line = f"[{datetime.now(timezone.utc)}] ShipId: {ship_id} Latitude: {lat} Longitude: {lon}\n"
                    with open("ship_positions.log", "a", encoding="utf-8") as logf:
                        logf.write(log_line)
                    with ships_lock:
                        if ship_id not in ships:
                            ships[ship_id] = []
                        ships[ship_id].append([lat, lon])
                        if len(ships[ship_id]) > 100:
                            ships[ship_id] = ships[ship_id][-100:]
            except Exception as e:
                print("Error procesando mensaje AISSTREAM:", e)

def start_aisstream_thread():
    loop = asyncio.new_event_loop()
    t = threading.Thread(target=_start_async_loop, args=(loop,), daemon=True)
    t.start()

def _start_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(connect_ais_stream())
