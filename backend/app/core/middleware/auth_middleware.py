from __future__ import annotations

from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.auth.session_manager import extract_token_from_request, decode_token


class AuthContextMiddleware(BaseHTTPMiddleware):
    """Lightweight middleware that, if a token is present, validates it once and
    stores minimal context (payload, sub) on request.state for later use.

    It does not enforce authentication for open endpoints; dependencies at the
    route level should still guard protected resources.
    """

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        try:
            # Try to get token from headers/cookies without raising
            token: Optional[str] = extract_token_from_request(request, creds=None)  # type: ignore[arg-type]
            if token:
                try:
                    payload = decode_token(token)
                    request.state.token_payload = payload  # type: ignore[attr-defined]
                    request.state.sub = payload.get("sub")  # type: ignore[attr-defined]
                except Exception:
                    # Don't block the request here; dependencies will raise 401 when required
                    pass
        except Exception:
            # Never break request flow from middleware
            pass
        return await call_next(request)
