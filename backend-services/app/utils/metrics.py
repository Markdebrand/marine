"""
Métricas ligeras en memoria (counters/durations) con logging opcional.

Evita dependencias externas. Para producción, puede reemplazarse por Prometheus/StatsD.
"""
from __future__ import annotations

from typing import Dict, Tuple, Optional
import threading
import time
import logging

_lock = threading.Lock()
_counters: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], int] = {}
_timings: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], float] = {}
logger = logging.getLogger("app.metrics")


def _normalize_tags(tags: Optional[dict] = None) -> Tuple[Tuple[str, str], ...]:
    if not tags:
        return tuple()
    return tuple(sorted((str(k), str(v)) for k, v in tags.items()))


def increment(name: str, value: int = 1, *, tags: Optional[dict] = None) -> None:
    key = (name, _normalize_tags(tags))
    with _lock:
        _counters[key] = _counters.get(key, 0) + int(value)
    # Log a nivel debug para no inundar
    logger.debug("metric.increment", extra={"metric": name, "value": value, "tags": dict(tags or {})})


def record_duration(name: str, seconds: float, *, tags: Optional[dict] = None) -> None:
    key = (name, _normalize_tags(tags))
    with _lock:
        _timings[key] = _timings.get(key, 0.0) + float(seconds)
    logger.debug("metric.duration", extra={"metric": name, "seconds": seconds, "tags": dict(tags or {})})


class Timer:
    def __init__(self, name: str, *, tags: Optional[dict] = None):
        self.name = name
        self.tags = tags or {}
        self._t0 = time.perf_counter()

    def stop(self) -> float:
        dt = time.perf_counter() - self._t0
        record_duration(self.name, dt, tags=self.tags)
        return dt

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False


def snapshot() -> dict:
    """Devuelve una copia simple de counters y timings para depuración."""
    with _lock:
        return {
            "counters": {str(k): v for k, v in _counters.items()},
            "timings": {str(k): v for k, v in _timings.items()},
        }

def export_raw():
    """Devuelve copias inmutables (shallow) para exportadores de métricas."""
    with _lock:
        return dict(_counters), dict(_timings)
