from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as _Req
from starlette.responses import JSONResponse as _JSON, Response as _Resp
import httpx as _hx
import time as _tm
from typing import Optional as _Opt, Tuple as _Tup
from app.config.settings import (
    ROOT_PATH as _rp,
    REMOTE_STATUS_URL as _ru,
    REMOTE_STATUS_CACHE_TTL as _rt,
    REMOTE_STATUS_FAIL_OPEN as _fo,
)


class AppSwitchMiddleware(BaseHTTPMiddleware):
    """Middleware que consulta un endpoint remoto (si está configurado) para permitir/bloquear temporalmente
    las rutas protegidas sin reiniciar el backend. Whitelistea rutas públicas/estáticas.
    """

    def __init__(self, app):  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._k: _Tup[float, bool] | None = None  # (exp, flag)
        self._to = _hx.Timeout(3.0, connect=2.0)
        self._w = [
            "/healthz",
            "/docs",
            "/openapi",
            "/redoc",
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
            "/google_login/google/authorized",
            "/auth/google/",
        ]

    def _p(self, x: str) -> bool:
        if x == "/":
            return True
        for y in self._w:
            if x == y or x.startswith(y.rstrip("/") + "/"):
                return True
        return False

    def _g(self) -> _Opt[bool]:
        if not self._k:
            return None
        e, v = self._k
        if _tm.time() < e:
            return v
        return None

    def _s(self, v: bool) -> None:
        self._k = (_tm.time() + max(1, _rt), v)

    async def _f(self) -> bool:
        if not _ru:
            return True
        try:
            async with _hx.AsyncClient(timeout=self._to, follow_redirects=True) as c:
                r = await c.get(_ru)
                if r.status_code == 200:
                    d = r.json()
                    return bool(d.get("enabled", False))
                return True if _fo else False
        except Exception:
            return True if _fo else False

    async def dispatch(self, request: _Req, call_next) -> _Resp:  # type: ignore[override]
        if not _ru:
            return await call_next(request)

        full = request.url.path
        try:
            rp = _rp or ""
            if rp and full.startswith(rp):
                p = full[len(rp):] or "/"
            else:
                p = full
        except Exception:
            p = full

        if self._p(p):
            return await call_next(request)

        c = self._g()
        if c is None:
            en = await self._f()
            self._s(en)
        else:
            en = c

        if not en:
            return _JSON(status_code=503, content={"error": "service_unavailable", "message": "Application temporarily disabled"})

        return await call_next(request)
