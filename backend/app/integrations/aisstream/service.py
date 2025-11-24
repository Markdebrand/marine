# service.py
import asyncio
import websockets
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Iterable
from collections import defaultdict

class AISBridgeService:
    def __init__(self, sio_server, api_key, bounding_boxes=None):
        self.sio_server = sio_server
        self.api_key = api_key
        self.bounding_boxes = bounding_boxes or [[[-90, -180], [90, 180]]]
        self._task = None
        self._running = False
        
        # Para datos de posición (existente)
        self._ships: Dict[str, List[List[float]]] = {}
        self._last_pos: Dict[str, Tuple[float, float]] = {}
        
        # NUEVO: Para datos estáticos de barcos
        self._ship_static_data: Dict[str, dict] = {}
        self._static_data_listeners: Dict[str, asyncio.Future] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()

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
                    # Enviar una copia segura de la lista de barcos cada 2 segundos
                    items_copy = list(self._last_pos.items())
                    positions = []
                    for ship_id, (lat, lon) in items_copy:
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
                self._last_pos.clear()
                
                async with websockets.connect(url) as websocket:
                    # Suscribirse a ambos tipos de mensajes
                    subscribe_message = {
                        "APIKey": self.api_key, 
                        "BoundingBoxes": self.bounding_boxes,
                        "FilterMessageTypes": ["PositionReport", "ShipStaticData"]  # Añadimos ShipStaticData
                    }
                    
                    await websocket.send(json.dumps(subscribe_message))
                    print("✓ Servicio AISBridge conectado y suscrito a PositionReport + ShipStaticData")
                    
                    # Lanzar el batch sender en paralelo
                    batch_task = asyncio.create_task(batch_sender())
                    try:
                        async for message_json in websocket:
                            if not self._running:
                                break
                            try:
                                message = json.loads(message_json)
                                
                                # Procesar PositionReport (existente)
                                if message.get("MessageType") == "PositionReport":
                                    ais_message = message['Message']['PositionReport']
                                    ship_id = str(ais_message['UserID'])
                                    lat = float(ais_message['Latitude'])
                                    lon = float(ais_message['Longitude'])
                                    
                                    # Mantener historial (código existente)
                                    emitir = False
                                    if ship_id not in self._ships:
                                        self._ships[ship_id] = []
                                        emitir = True
                                    else:
                                        last_pos = self._ships[ship_id][-1] if self._ships[ship_id] else None
                                        if last_pos is None or last_pos[0] != lat or last_pos[1] != lon:
                                            emitir = True
                                    
                                    self._ships[ship_id].append([lat, lon])
                                    if len(self._ships[ship_id]) > 100:
                                        self._ships[ship_id] = self._ships[ship_id][-100:]
                                    self._last_pos[ship_id] = (lat, lon)
                                    
                                    if emitir:
                                        await self.sio_server.emit("ais_position", {
                                            "id": ship_id,
                                            "lat": lat,
                                            "lon": lon,
                                            "positions": self._ships[ship_id],
                                        })
                                
                                # NUEVO: Procesar ShipStaticData
                                elif message.get("MessageType") == "ShipStaticData":
                                    ais_message = message['Message']['ShipStaticData']
                                    ship_id = str(ais_message['UserID'])
                                    
                                    # Almacenar datos estáticos
                                    processed_data = self._process_static_data(ais_message)
                                    self._ship_static_data[ship_id] = processed_data
                                    
                                    # Notificar a cualquier listener esperando este MMSI
                                    if ship_id in self._static_data_listeners:
                                        future = self._static_data_listeners[ship_id]
                                        if not future.done():
                                            future.set_result(processed_data)
                                        del self._static_data_listeners[ship_id]
                                    
                                    # print(f"✓ Datos estáticos recibidos para MMSI: {ship_id}")
                                    
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
                await asyncio.sleep(5)

    # NUEVO: Método para solicitar datos estáticos de un barco
    async def get_ship_static_data(self, mmsi: str, timeout: float = 30.0) -> Optional[dict]:
        """
        Obtiene datos estáticos de un barco por MMSI.
        Si ya tenemos los datos, los devuelve inmediatamente.
        Si no, espera a recibirlos del stream.
        """
        # Si ya tenemos los datos, devolverlos
        if mmsi in self._ship_static_data:
            return self._ship_static_data[mmsi]
        
        # Si no, crear un future para esperar los datos
        future = asyncio.Future()
        self._static_data_listeners[mmsi] = future
        
        try:
            # Esperar a que lleguen los datos
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            # Si timeout, limpiar el listener
            if mmsi in self._static_data_listeners:
                del self._static_data_listeners[mmsi]
            return None
        except Exception as e:
            if mmsi in self._static_data_listeners:
                del self._static_data_listeners[mmsi]
            raise e

    # NUEVO: Procesar datos estáticos
    def _process_static_data(self, ais_message):
        """Procesa datos estáticos del barco"""
        dimensions = ais_message.get('Dimension', {})
        ship_id = str(ais_message.get('UserID', 'N/A'))
        
        # Procesar ETA
        eta_obj = ais_message.get('Eta', {})
        eta_formatted = "N/A"
        if isinstance(eta_obj, dict) and eta_obj:
            month = eta_obj.get('Month', 0)
            day = eta_obj.get('Day', 0)
            hour = eta_obj.get('Hour', 0)
            minute = eta_obj.get('Minute', 0)
            
            # Validar que los valores sean válidos
            if month > 0 and day > 0:
                # Usar año actual como referencia
                current_year = datetime.now(timezone.utc).year
                eta_formatted = f"{current_year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
        
        return {
            "ship_name": ais_message.get('Name', ais_message.get('ShipName', 'N/A')).strip(),
            "imo_number": ais_message.get('ImoNumber', ais_message.get('IMONumber', 'N/A')),
            "call_sign": ais_message.get('CallSign', 'N/A'),
            "ship_type": self._get_ship_type_text(ais_message.get('ShipType', ais_message.get('Type', 0))),
            "dimensions": {
                "a": dimensions.get('A', 0),
                "b": dimensions.get('B', 0),
                "c": dimensions.get('C', 0),
                "d": dimensions.get('D', 0),
                "length": dimensions.get('A', 0) + dimensions.get('B', 0),
                "width": dimensions.get('C', 0) + dimensions.get('D', 0)
            },
            "fix_type": ais_message.get('FixType', 'N/A'),
            "eta": eta_formatted,  # Ahora formateado correctamente
            "draught": ais_message.get('Draught', ais_message.get('MaximumStaticDraught', 'N/A')),
            "destination": ais_message.get('Destination', 'N/A'),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # NUEVO: Convertir código de tipo de barco a texto
    def _get_ship_type_text(self, type_code):
        """Convierte el código de tipo de barco a texto descriptivo."""
        ship_types = {
            0: "Not available",
            20: "Wing in ground (WIG)",
            29: "Wing in ground (WIG), Hazardous category D",
            30: "Fishing",
            31: "Towing",
            32: "Towing: length exceeds 200m or breadth exceeds 25m",
            33: "Dredging or underwater ops",
            34: "Diving ops",
            35: "Military ops",
            36: "Sailing",
            37: "Pleasure Craft",
            40: "High speed craft (HSC)",
            49: "High speed craft (HSC), Hazardous category D",
            50: "Pilot Vessel",
            51: "Search and Rescue vessel",
            52: "Tug",
            53: "Port Tender",
            54: "Anti-pollution equipment",
            55: "Law Enforcement",
            58: "Medical Transport",
            59: "Noncombatant ship according to RR Resolution No. 18",
            60: "Passenger",
            69: "Passenger, Hazardous category D",
            70: "Cargo",
            79: "Cargo, Hazardous category D",
            80: "Tanker",
            89: "Tanker, Hazardous category D",
            90: "Other Type",
            99: "Other Type, Hazardous category D"
        }
        return ship_types.get(type_code, f"Unknown ({type_code})")

    def _iter_last_positions(
        self, bbox: Optional[Tuple[float, float, float, float]] = None
    ) -> Iterable[Tuple[str, float, float]]:
        """Iterate last known positions optionally filtered by bbox (west,south,east,north)."""
        # CREAR UNA COPIA SEGURA para iterar
        items_copy = list(self._last_pos.items())
        
        if bbox is None:
            for ship_id, (lat, lon) in items_copy:
                yield ship_id, lat, lon
            return
            
        west, south, east, north = bbox
        use_lon_filter = east >= west
        for ship_id, (lat, lon) in items_copy:
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
