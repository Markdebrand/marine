from typing import Any, Dict, List, Optional

import asyncio
import socketio

from app.integrations.aisstream.client import AISStreamClient
from app.config.settings import (
    AISSTREAM_BOUNDING_BOXES,
    AISSTREAM_FILTER_MMSI,
    AISSTREAM_FILTER_TYPES,
    AISSTREAM_BATCH_MS,
)


class AISBridgeService:
    """Recibe mensajes de AISStream y los reenvía a Socket.IO.

    Por ahora reenviamos todo como evento "ais_raw" para máxima flexibilidad
    y, específicamente, si el payload contiene "MessageType" == "PositionReport",
    emitimos también "ais_position" con un formato amigable para el mapa.
    """

    def __init__(self, sio: socketio.AsyncServer, api_key: str) -> None:
        self.sio = sio
        self.client = AISStreamClient(
            api_key,
            bounding_boxes=AISSTREAM_BOUNDING_BOXES,
            filter_message_types=AISSTREAM_FILTER_TYPES,
            filter_mmsi=AISSTREAM_FILTER_MMSI,
            on_message=self._on_message,
        )
        self._started = False
        self._batch_ms = AISSTREAM_BATCH_MS
        self._batch_queue: List[Dict[str, Any]] = []
        self._batch_task: Optional[asyncio.Task] = None

    async def _on_message(self, data: Dict[str, Any]):
        # Emit raw para que se pueda inspeccionar en el frontend si se desea
        await self.sio.emit("ais_raw", data)
        # Extraer posición si la estructura concuerda
        try:
            msg_type = data.get("MessageType") or data.get("Message", {}).get("MessageType")
            if msg_type == "PositionReport":
                message = data.get("Message") or data
                # El modelo de aisstream suele encapsular en {"MetaData":..., "Message":{...}}
                # Buscamos campos comunes: MMSI, Latitude, Longitude, SOG, COG, Heading
                mmsi = message.get("UserID") or message.get("MMSI")
                lat = message.get("Latitude") or message.get("lat")
                lon = message.get("Longitude") or message.get("lon")
                cog = message.get("COG") or message.get("courseOverGround")
                sog = message.get("SOG") or message.get("speedOverGround")
                hdg = message.get("Heading") or message.get("trueHeading")
                if lat is not None and lon is not None and mmsi is not None:
                    pos = {
                        "id": str(mmsi),
                        "lat": float(lat),
                        "lon": float(lon),
                        "cog": float(cog) if cog is not None else None,
                        "sog": float(sog) if sog is not None else None,
                        "heading": float(hdg) if hdg is not None else None,
                    }
                    if self._batch_ms and self._batch_ms > 0:
                        self._batch_queue.append(pos)
                        # Ensure task exists
                        if not self._batch_task or self._batch_task.done():
                            self._batch_task = asyncio.create_task(self._batch_loop(), name="aisstream-batcher")
                    else:
                        await self.sio.emit("ais_position", pos)
        except Exception:
            # Evitar que un error de parseo tumbe el loop; podríamos loggear si se desea
            return

    async def _batch_loop(self):
        # Sleep the batch window then flush
        await asyncio.sleep(self._batch_ms / 1000.0)
        if not self._batch_queue:
            return
        batch = self._batch_queue.copy()
        self._batch_queue.clear()
        await self.sio.emit("ais_position_batch", {"positions": batch})

    async def start(self):
        if self._started:
            return
        await self.client.start()
        self._started = True

    async def stop(self):
        if not self._started:
            return
        await self.client.stop()
        self._started = False
