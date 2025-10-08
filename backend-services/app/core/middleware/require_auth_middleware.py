from __future__ import annotations

from typing import Iterable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.core.auth.session_manager import extract_token_from_request, decode_token
from app.config.settings import ROOT_PATH


class RequireAuthMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces a valid access token for selected path prefixes.

    Public endpoints (health, docs, auth login/register/refresh, OAuth callbacks) stay open.
    Authorization (permissions/roles) remains at the route level via dependencies.
    """

    def __init__(self, app, protected_prefixes: Iterable[str] | None = None):  # type: ignore[no-untyped-def]
        super().__init__(app)
        # Defaults: guard typical authenticated modules
        self.protected = list(protected_prefixes or [
            "/due",
            "/plaid",
            "/rpc",
            "/auth/me",
            "/auth/profile",
        ])
        # Public paths always allowed (prefix match)
        self.public_prefixes = [
            "/",
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

    def _is_public(self, path: str) -> bool:
        for p in self.public_prefixes:
            if path == p or path.startswith(p.rstrip("/") + "/"):
                return True
        return False

    def _is_protected(self, path: str) -> bool:
        for p in self.protected:
            if path == p or path.startswith(p.rstrip("/") + "/"):
                return True
        return False

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        path = request.url.path
        # Support apps mounted with root_path by also checking without it
        try:
            rp = ROOT_PATH or ""
            if rp and path.startswith(rp):
                short = path[len(rp) :] or "/"
            else:
                short = path
        except Exception:
            short = path

        if self._is_public(short):
            return await call_next(request)

        if not self._is_protected(short):
            return await call_next(request)

        # Enforce: must have valid token (no DB consults here)
        token = extract_token_from_request(request, None)
        if not token:
            return JSONResponse({"detail": "Falta token"}, status_code=401)
        try:
            payload = decode_token(token)
            # cache for downstream
            request.state.token_payload = payload  # type: ignore[attr-defined]
            request.state.sub = payload.get("sub")  # type: ignore[attr-defined]
        except Exception:
            return JSONResponse({"detail": "Token inválido"}, status_code=401)

        return await call_next(request)
