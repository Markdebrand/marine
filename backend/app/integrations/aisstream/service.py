# service.py
"""
AISBridgeService: Servicio para conectar y manejar el stream de AISSTREAM y emitir eventos a Socket.IO
"""
import asyncio
import websockets
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List

class AISBridgeService:
    def __init__(self, sio_server, api_key, bounding_boxes=None):
        self.sio_server = sio_server
        self.api_key = api_key
        self.bounding_boxes = bounding_boxes or [[[-90, -180], [90, 180]]]
        self._task = None
        self._running = False
        self._ships: Dict[str, List[List[float]]] = {}

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except Exception:
                pass

    async def _run(self):
        url = "wss://stream.aisstream.io/v0/stream"
        async def batch_sender():
            while self._running:
                try:
                    # Enviar batch de todos los barcos cada 2 segundos
                    positions = []
                    for ship_id, pos_list in self._ships.items():
                        if pos_list:
                            lat, lon = pos_list[-1]
                            positions.append({
                                "id": ship_id,
                                "lat": lat,
                                "lon": lon,
                            })
                    await self.sio_server.emit("ais_position_batch", {"positions": positions})
                except Exception as e:
                    logging.error(f"Error enviando batch AIS: {e}")
                await asyncio.sleep(2)

        while self._running:
            try:
                async with websockets.connect(url) as websocket:
                    subscribe_message = {"APIKey": self.api_key, "BoundingBoxes": self.bounding_boxes}
                    await websocket.send(json.dumps(subscribe_message))
                    # Lanzar el batch sender en paralelo
                    batch_task = asyncio.create_task(batch_sender())
                    try:
                        async for message_json in websocket:
                            if not self._running:
                                break
                            try:
                                message = json.loads(message_json)
                                if message.get("MessageType") == "PositionReport":
                                    ais_message = message['Message']['PositionReport']
                                    ship_id = str(ais_message['UserID'])
                                    lat = float(ais_message['Latitude'])
                                    lon = float(ais_message['Longitude'])
                                    log_line = f"[{datetime.now(timezone.utc)}] ShipId: {ship_id} Latitude: {lat} Longitude: {lon}"
                                    logging.info(log_line)
                                    # Mantener historial
                                    if ship_id not in self._ships:
                                        self._ships[ship_id] = []
                                    self._ships[ship_id].append([lat, lon])
                                    if len(self._ships[ship_id]) > 100:
                                        self._ships[ship_id] = self._ships[ship_id][-100:]
                                    # Emitir evento a todos los clientes conectados
                                    await self.sio_server.emit("ais_position", {
                                        "ship_id": ship_id,
                                        "lat": lat,
                                        "lon": lon,
                                        "positions": self._ships[ship_id],
                                    })
                            except Exception as e:
                                logging.error(f"Error procesando mensaje AISSTREAM: {e}")
                    finally:
                        batch_task.cancel()
                        try:
                            await batch_task
                        except Exception:
                            pass
            except Exception as e:
                logging.error(f"Error en conexión AISSTREAM: {e}")
                # Log extra para depuración
                logging.error(f"AISSTREAM API KEY usada: {self.api_key}")
                import traceback
                logging.error(traceback.format_exc())
                await asyncio.sleep(5)

    def get_positions(self):
        return [[ship_id, positions] for ship_id, positions in self._ships.items()]
