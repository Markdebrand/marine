from __future__ import annotations

import asyncio
import math
import random
import time
from typing import Any, List, Dict

import socketio


class AISSimpleSimulator:
    """
    Minimal AIS simulator for development without external keys.

    Emits "ais_position_batch" events every tick with a small set of
    vessels that perform a slow random walk. This matches the frontend
    expectations used in AisLiveMap.tsx.
    """

    def __init__(
        self,
        sio: socketio.AsyncServer,
        *,
        vessel_count: int = 40,
        center: tuple[float, float] = (-3.7038, 40.4168),  # Madrid approx
        spread_deg: float = 8.0,
        tick_seconds: float = 2.5,
        seed: int | None = None,
    ) -> None:
        self.sio = sio
        self.vessel_count = max(5, min(500, vessel_count))
        self.center = center
        self.spread_deg = max(0.5, min(60.0, spread_deg))
        self.tick_seconds = max(0.5, min(30.0, tick_seconds))
        self.task: asyncio.Task[Any] | None = None
        self._rng = random.Random(seed or int(time.time()))
        self._fleet = self._bootstrap_fleet()

    def _bootstrap_fleet(self) -> List[Dict[str, Any]]:
        cx, cy = self.center
        fleet: List[Dict[str, Any]] = []
        for i in range(self.vessel_count):
            # Create pseudo MMSI-like ID and random starting position
            mmsi = f"999{self._rng.randint(100000, 999999)}"
            lon = cx + self._rng.uniform(-self.spread_deg, self.spread_deg)
            lat = cy + self._rng.uniform(-self.spread_deg, self.spread_deg)
            sog = max(0.1, abs(self._rng.gauss(8.0, 3.0)))
            cog = self._rng.uniform(0.0, 360.0)
            name = f"SIM-{i:03d}"
            fleet.append({"mmsi": mmsi, "lon": lon, "lat": lat, "sog": sog, "cog": cog, "name": name})
        return fleet

    def _step(self) -> None:
        # Simple random walk with slight bearing changes and speed noise
        for v in self._fleet:
            # change course slightly
            v["cog"] = (v.get("cog", 0.0) + self._rng.uniform(-8.0, 8.0)) % 360.0
            # jitter speed
            v["sog"] = max(0.1, float(v.get("sog", 5.0)) + self._rng.uniform(-0.5, 0.5))
            # move approx: 1 deg ~ 111km. We scale to be visually plausible at world zooms.
            # Convert SOG knots -> deg per tick (approximation for visualization only)
            # 1 knot ~ 0.0003 deg/sec at equator; we'll simplify.
            speed_deg = (v["sog"] * 0.00030) * self.tick_seconds
            # simple bearing step
            rad = v["cog"] * 3.14159265 / 180.0
            v["lon"] += speed_deg * float(self._rng.uniform(0.9, 1.1)) * float(
                math.cos(rad)
            )
            v["lat"] += speed_deg * float(self._rng.uniform(0.9, 1.1)) * float(
                math.sin(rad)
            )
            # keep within world bounds
            v["lon"] = max(-180.0, min(180.0, v["lon"]))
            v["lat"] = max(-85.0, min(85.0, v["lat"]))

    async def _loop(self) -> None:
        try:
            while True:
                try:
                    # advance positions
                    self._step()
                except Exception:
                    # continue even if step fails
                    pass
                # Prepare batch payload expected by frontend
                payload = {
                    "positions": [
                        {
                            "id": v["mmsi"],
                            "lon": float(v["lon"]),
                            "lat": float(v["lat"]),
                            "cog": float(v.get("cog") or 0.0),
                            "sog": float(v.get("sog") or 0.0),
                            "name": str(v.get("name") or "SIM"),
                        }
                        for v in self._fleet
                    ]
                }
                # Broadcast to all clients
                try:
                    await self.sio.emit("ais_position_batch", payload)
                except Exception:
                    # ignore transient socket errors
                    pass
                await asyncio.sleep(self.tick_seconds)
        except asyncio.CancelledError:  # pragma: no cover
            raise

    async def start(self) -> None:
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self._loop(), name="ais-simulator")

    async def stop(self) -> None:
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
