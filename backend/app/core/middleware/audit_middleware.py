import time
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from jose import jwt, JWTError
from app.config.settings import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_AUDIENCE
from app.audit.audit_logger import record_request_timing


def _get_client_ip(request: Request) -> str:
    # Respeta ProxyHeadersMiddleware: usa X-Forwarded-For si existe
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # tomar el primero
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "-"


def _get_user_id_from_auth(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], audience=JWT_AUDIENCE)
        sub = payload.get("sub")
        return str(sub) if sub is not None else None
    except JWTError:
        return None


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware de auditoría privado: mide requests y delega a servicio de auditoría."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        user_id = _get_user_id_from_auth(request)
        ip = _get_client_ip(request)
        ua = request.headers.get("user-agent", "-")
        path = request.url.path
        if request.url.query:
            path = f"{path}?{request.url.query}"
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            status = getattr(request.state, "_forced_status", None) or getattr(
                locals().get("response", None), "status_code", 0
            )
            record_request_timing(
                method=request.method,
                path=path,
                status=status,
                duration_ms=duration_ms,
                user_id=user_id,
                ip=ip,
                ua=ua,
            )
