from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
from jose import jwt, JWTError
from app.config.settings import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_AUDIENCE

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger("app.analytics")


class PageDwellEvent(BaseModel):
    path: str = Field(..., description="Ruta de la página en el frontend, p.ej. /dashboard")
    duration_ms: float = Field(..., ge=0, description="Tiempo total en la página en milisegundos")
    referrer: Optional[str] = Field(None, description="Referrer del frontend, si aplica")
    ts: Optional[float] = Field(None, description="Unix timestamp (cliente) opcional")
    meta: Optional[Dict[str, Any]] = Field(None, description="Campos adicionales opcionales")


def _get_user_id(request: Request) -> str:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return "-"
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], audience=JWT_AUDIENCE)
        sub = payload.get("sub")
        return str(sub) if sub is not None else "-"
    except JWTError:
        return "-"


@router.post("/page_dwell")
async def page_dwell(event: PageDwellEvent, request: Request):
    """Registra un evento de permanencia en una página del frontend.

    No persiste en DB; solo escribe en logs para análisis en tu stack de logs.
    """
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
        request.client.host if request.client else "-"
    )
    ua = request.headers.get("user-agent", "-")
    user_id = _get_user_id(request)
    logger.info(
        "page_dwell path=%s duration_ms=%.2f user_id=%s ip=%s ua=%s referrer=%s meta=%s ts=%s",
        event.path,
        event.duration_ms,
        user_id,
        ip,
        ua,
        event.referrer or "-",
        event.meta or {},
        event.ts if event.ts is not None else "-",
    )
    return {"success": True}
