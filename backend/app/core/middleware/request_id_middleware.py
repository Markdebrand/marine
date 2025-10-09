from __future__ import annotations

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        # Get or create correlation id
        cid = request.headers.get(self.header_name)
        if not cid:
            cid = uuid.uuid4().hex
        try:
            request.state.correlation_id = cid  # type: ignore[attr-defined]
        except Exception:
            pass
        response = await call_next(request)
        response.headers.setdefault(self.header_name, cid)
        return response
