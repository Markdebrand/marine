import asyncio
import json
from typing import Any, Dict, List, Optional

import aiohttp


WS_URL = "wss://stream.aisstream.io/v0/stream"


class AISStreamClient:
    def __init__(
        self,
        api_key: str,
        *,
        bounding_boxes: Optional[List[List[float]]] = None,
        filter_message_types: Optional[List[str]] = None,
        filter_mmsi: Optional[List[str]] = None,
        on_message=None,
        reconnect_backoff: float = 2.0,
        reconnect_backoff_max: float = 60.0,
    ) -> None:
        self.api_key = api_key
        self.bounding_boxes = bounding_boxes or [[-90, -180], [90, 180]]
        self.filter_message_types = filter_message_types or ["PositionReport"]
        self.filter_mmsi = filter_mmsi or []
        self.on_message = on_message
        self._task: Optional[asyncio.Task] = None
        self._running = asyncio.Event()
        self._backoff = reconnect_backoff
        self._backoff_max = reconnect_backoff_max

    async def _emit(self, data: Dict[str, Any]):
        if self.on_message:
            await self.on_message(data)

    async def _connect_and_stream(self):
        session_timeout = aiohttp.ClientTimeout(total=None, sock_read=None, sock_connect=30)
        async with aiohttp.ClientSession(timeout=session_timeout) as session:
            while self._running.is_set():
                try:
                    async with session.ws_connect(WS_URL, heartbeat=30) as ws:
                        # Reset backoff tras conexión
                        self._backoff = 2.0
                        subscribe = {
                            "Apikey": self.api_key,
                            "BoundingBoxes": self.bounding_boxes,
                            "FiltersShipMMSI": self.filter_mmsi,
                            "FilterMessageTypes": self.filter_message_types,
                        }
                        await ws.send_str(json.dumps(subscribe))
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    payload = json.loads(msg.data)
                                except Exception:
                                    continue
                                await self._emit(payload)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                break
                            elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED):
                                break
                except Exception:
                    # Esperar backoff y reintentar
                    await asyncio.sleep(self._backoff)
                    self._backoff = min(self._backoff * 2.0, self._backoff_max)

    async def start(self):
        if self._task and not self._task.done():
            return
        self._running.set()
        self._task = asyncio.create_task(self._connect_and_stream(), name="aisstream-client")

    async def stop(self):
        self._running.clear()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=3)
            except asyncio.TimeoutError:
                self._task.cancel()
            finally:
                self._task = None
