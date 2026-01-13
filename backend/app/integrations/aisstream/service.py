# service.py
import asyncio
import websockets
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Iterable
from collections import defaultdict
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from app.db.database import SessionLocal
from app.db.models.marine_vessel import MarineVessel

class AISBridgeService:
    def __init__(self, sio_server, api_key, bounding_boxes=None, redis_client=None):
        self.sio_server = sio_server
        self.api_key = api_key
        self.bounding_boxes = bounding_boxes or [[[-90, -180], [90, 180]]]
        self.redis_client = redis_client
        self._task = None
        self._running = False
        self.redis_positions_key = "ais:positions"

        
        # Para datos de posición (existente)
        self._ships: Dict[str, List[List[float]]] = {}
        self._last_pos: Dict[str, Tuple[float, float]] = {}
        
        # NUEVO: Para datos estáticos de barcos
        self._ship_static_data: Dict[str, dict] = {}
        self._static_data_listeners: Dict[str, asyncio.Future] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._syncer_task = None
        self._syncer_running = False

    async def start(self):
        self._running = True
        self._syncer_running = True
        self._task = asyncio.create_task(self._run())
        self._syncer_task = asyncio.create_task(self._static_data_syncer_loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except Exception:
                pass
        
        self._syncer_running = False
        if self._syncer_task:
            self._syncer_task.cancel()
            try:
                await self._syncer_task
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
                                    
                                    # Sync to Redis if client is available
                                    if self.redis_client:
                                        try:
                                            # Store as "lat,lon" string for efficiency
                                            self.redis_client.hset(
                                                self.redis_positions_key, 
                                                ship_id, 
                                                f"{lat},{lon}"
                                            )
                                        except Exception as rx:
                                            logging.getLogger(__name__).warning(f"Redis write error: {rx}")
                                    
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
                                    
                                    # Caching en Redis y agendar a DB
                                    if self.redis_client:
                                        self._buffer_static_data(ship_id, processed_data)
                                    
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

    def get_ship_position(self, mmsi: str) -> Optional[Tuple[float, float]]:
        """Devuelve la última posición (lat, lon) conocida en memoria, o Redis si hay fallback."""
        # 1. Intentar memoria local
        if mmsi in self._last_pos:
            return self._last_pos[mmsi]
            
        # 2. Intentar Redis si está disponible
        if self.redis_client:
            try:
                # El formato en Redis es "lat,lon" string
                pos_str = self.redis_client.hget(self.redis_positions_key, mmsi)
                if pos_str:
                    val = pos_str.decode('utf-8') if isinstance(pos_str, bytes) else str(pos_str)
                    lat_s, lon_s = val.split(',')
                    return (float(lat_s), float(lon_s))
            except Exception as e:
                logging.getLogger(__name__).warning(f"Error fetching position from Redis for {mmsi}: {e}")
                
        return None

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
        
        items_copy = []
        
        # If we are the writer (active), use local memory
        if self._running:
            items_copy = list(self._last_pos.items())
        # If we are a reader (passive) and have Redis, fetch from Redis
        elif self.redis_client:
            try:
                # Calculate approximate number of items to decide on approach?
                # For now just fetch all. HGETALL is O(N)
                all_pos = self.redis_client.hgetall(self.redis_positions_key)
                for sid_bytes, pos_bytes in all_pos.items():
                    try:
                        sid = sid_bytes.decode('utf-8') if isinstance(sid_bytes, bytes) else str(sid_bytes)
                        val = pos_bytes.decode('utf-8') if isinstance(pos_bytes, bytes) else str(pos_bytes)
                        # val expected is "lat,lon"
                        lat_s, lon_s = val.split(',')
                        items_copy.append((sid, (float(lat_s), float(lon_s))))
                    except (ValueError, IndexError):
                        continue
            except Exception as e:
                logging.getLogger(__name__).error(f"Error fetching filtered positions from Redis: {e}")
                return
        else:
            # No data source available
            return

        if bbox is None:
            for ship_id, (lat, lon) in items_copy:
                yield ship_id, lat, lon
            return
            
        west, south, east, north = bbox
        
        # Handle dateline crossing if necessary (simplistic approach for now)
        # Standard filter
        use_lon_filter = east >= west
        
        for ship_id, (lat, lon) in items_copy:
            if lat < south or lat > north:
                continue
            if use_lon_filter:
                if (lon < west or lon > east):
                    continue
            else:
                 # Crossing dateline: keep if lon >= west OR lon <= east
                 if not (lon >= west or lon <= east):
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

    def _buffer_static_data(self, ship_id: str, data: dict):
        """Guarda datos estáticos en Redis e indica que está pendiente de sync."""
        try:
            # Hash único para datos estáticos
            self.redis_client.hset("ais:static_data", ship_id, json.dumps(data))
            # Set de IDs pendientes de sync
            self.redis_client.sadd("ais:pending_static_updates", ship_id)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Error buffering static data in Redis: {e}")

    async def _static_data_syncer_loop(self):
        """Sincroniza periódicamente los datos estáticos de Redis a Postgres."""
        if not self.redis_client:
            logging.info("Redis client not available, skipping static data DB sync loop.")
            return

        batch_size = 50
        while self._syncer_running:
            try:
                # Obtener un lote de MMSIs pendientes
                # spop(count) retorna una lista de elementos removidos
                pending_mmsis = self.redis_client.spop("ais:pending_static_updates", batch_size)
                
                if pending_mmsis:
                    # Convertir a lista de strings (redis retorna bytes si no decode_responses)
                    # Pero en cache_adapter parece que decode_responses=False...
                    # Si pending_mmsis viene en bytes, decodificar.
                    mmsi_list = []
                    for m in pending_mmsis:
                        if isinstance(m, bytes):
                            mmsi_list.append(m.decode('utf-8'))
                        elif isinstance(m, str):
                            mmsi_list.append(m)
                    
                    if mmsi_list:
                        # Recuperar datos del hash
                        # hmget retorna lista en orden de claves
                        raw_data_list = self.redis_client.hmget("ais:static_data", mmsi_list)
                        
                        vessels_to_upsert = []
                        for mmsi, raw_json in zip(mmsi_list, raw_data_list):
                            if raw_json:
                                try:
                                    data_dict = json.loads(raw_json)
                                    vessels_to_upsert.append({
                                        "mmsi": mmsi,
                                        "data": data_dict
                                    })
                                except Exception:
                                    pass
                        
                        if vessels_to_upsert:
                             # Ejecutar upsert en hilo aparte para no bloquear loop
                            await asyncio.to_thread(self._upsert_vessels_to_db, vessels_to_upsert)
                            
                # Pausa antes del siguiente lote
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.getLogger(__name__).error(f"Error in static data syncer loop: {e}")
                await asyncio.sleep(5)

    def _upsert_vessels_to_db(self, vessel_batch: List[dict]):
        """Upsert batch of vessels to Postgres synchronously."""
        if not vessel_batch:
            return
            
        session = SessionLocal()
        try:
            # Preparar datos para insert
            # MarineVessel: mmsi, imo, name, type, ext_refs
            rows = []
            for item in vessel_batch:
                mmsi = item["mmsi"]
                d = item["data"]
                
                # Mapeo
                ship_name = d.get("ship_name") or "Unknown"
                imo = d.get("imo_number")
                if imo == "N/A": 
                    imo = None
                
                # Convertir IMO a string
                imo_str = str(imo) if imo else None
                
                ship_type_str = d.get("ship_type")
                
                # New columns
                dims = d.get("dimensions") or {}
                # length / width from dict or calc
                length = dims.get("length")
                width = dims.get("width")
                
                # Campos extra a JSONB
                ext_refs = {
                    "call_sign": d.get("call_sign"),
                    "dimensions": dims,
                    "fix_type": d.get("fix_type"),
                    "eta": d.get("eta"),
                    "draught": d.get("draught"),
                    "destination": d.get("destination"),
                    "timestamp": d.get("timestamp")
                }
                
                rows.append({
                    "mmsi": mmsi,
                    "imo": imo_str,
                    "name": ship_name,
                    "type": ship_type_str,
                    "length": length,
                    "width": width,
                    "ext_refs": ext_refs
                })

            stmt = insert(MarineVessel).values(rows)
            # ON CONFLICT DO UPDATE
            stmt = stmt.on_conflict_do_update(
                index_elements=[MarineVessel.mmsi],
                set_={
                    "imo": stmt.excluded.imo,
                    "name": stmt.excluded.name,
                    "type": stmt.excluded.type,
                    "length": stmt.excluded.length,
                    "width": stmt.excluded.width,
                    "ext_refs": stmt.excluded.ext_refs,
                    "updated_at": datetime.now(timezone.utc)
                }
            )
            session.execute(stmt)
            session.commit()
            logging.info(f"Synced {len(rows)} vessels to DB.")
        except Exception as e:
            logging.getLogger(__name__).error(f"Error upserting vessels to DB: {e}")
            session.rollback()
        finally:
            session.close()
