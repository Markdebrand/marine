# service.py
"""
AISBridgeService: Servicio para conectar y manejar el stream de AISSTREAM y emitir eventos a Socket.IO
"""
import asyncio
import websockets
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Iterable

class AISBridgeService:
    def __init__(self, sio_server, api_key, bounding_boxes=None):
        self.sio_server = sio_server
        self.api_key = api_key
        self.bounding_boxes = bounding_boxes or [[[-90, -180], [90, 180]]]
        self._task = None
        self._running = False
        # ship_id -> history of [lat, lon]
        self._ships: Dict[str, List[List[float]]] = {}
        # ship_id -> (lat, lon) cache for quick reads
        self._last_pos: Dict[str, Tuple[float, float]] = {}

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
                    for ship_id, (lat, lon) in self._last_pos.items():
                        positions.append({
                            "id": ship_id,
                            "lat": lat,
                            "lon": lon,
                        })
                    logging.getLogger("socketio.server").debug(
                        "Emitting ais_position_batch count=%d", len(positions)
                    )
                    await self.sio_server.emit("ais_position_batch", {"positions": positions})
                except Exception as e:
                    logging.getLogger("socketio.server").warning("Error sending AIS batch: %s", e)
                await asyncio.sleep(2)

        while self._running:
            try:
                # Limpiar barcos al reconectar para evitar duplicados
                self._ships.clear()
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
                                    # Log detallado solo en DEBUG para evitar ruido
                                    logging.getLogger(__name__).debug(
                                        "Ship %s lat=%s lon=%s", ship_id, lat, lon
                                    )
                                    # Mantener historial
                                    emitir = False
                                    if ship_id not in self._ships:
                                        self._ships[ship_id] = []
                                        emitir = True  # Primera vez que llega este barco
                                    else:
                                        # Solo emitir si la posición cambió respecto a la última
                                        last_pos = self._ships[ship_id][-1] if self._ships[ship_id] else None
                                        if last_pos is None or last_pos[0] != lat or last_pos[1] != lon:
                                            emitir = True
                                    self._ships[ship_id].append([lat, lon])
                                    if len(self._ships[ship_id]) > 100:
                                        self._ships[ship_id] = self._ships[ship_id][-100:]
                                    self._last_pos[ship_id] = (lat, lon)
                                    if emitir:
                                        # Emitir evento a todos los clientes conectados
                                        logging.getLogger("socketio.server").debug(
                                            "Emitting ais_position ship=%s", ship_id
                                        )
                                        await self.sio_server.emit("ais_position", {
                                            "id": ship_id,
                                            "lat": lat,
                                            "lon": lon,
                                            # histórico opcional (no usado por el cliente pero útil para debug)
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
                logging.getLogger(__name__).error("AISSTREAM connection error: %s", e)
                # Log extra para depuración
                logging.getLogger(__name__).debug("AISSTREAM API KEY used: %s", self.api_key)
                import traceback
                logging.getLogger(__name__).debug(traceback.format_exc())
                await asyncio.sleep(5)

    def _iter_last_positions(
        self, bbox: Optional[Tuple[float, float, float, float]] = None
    ) -> Iterable[Tuple[str, float, float]]:
        """Iterate last known positions optionally filtered by bbox (west,south,east,north)."""
        if bbox is None:
            for ship_id, (lat, lon) in self._last_pos.items():
                yield ship_id, lat, lon
            return
        west, south, east, north = bbox
        # Handle antimeridian wrap simply by requiring west<=lon<=east; if west>east skip filter.
        use_lon_filter = east >= west
        for ship_id, (lat, lon) in self._last_pos.items():
            if lat < south or lat > north:
                continue
            if use_lon_filter and (lon < west or lon > east):
                continue
            yield ship_id, lat, lon

    def get_positions(self):
        """Backwards-compatible: returns full histories."""
        return [[ship_id, positions] for ship_id, positions in self._ships.items()]

    def get_positions_page(
        self,
        page: int = 1,
        page_size: int = 1000,
        bbox: Optional[Tuple[float, float, float, float]] = None,
    ) -> dict:
        """
        Return a paginated list of last positions per ship.
        Response shape: { total, page, page_size, items: [{id, lat, lon}] }
        """
        # Build filtered list
        items = [
            {"id": ship_id, "lat": lat, "lon": lon}
            for ship_id, lat, lon in self._iter_last_positions(bbox)
        ]
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = items[start:end]
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": page_items,
        }
