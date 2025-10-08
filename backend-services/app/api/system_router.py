from fastapi import APIRouter, Depends, HTTPException
from app.config.settings import APP_NAME, DEBUG
from fastapi.responses import RedirectResponse, Response
from app.config.settings import ROOT_PATH
from app.core.auth.session_manager import get_current_user
from app.core.auth.guards import require_admin
from app.db import models
from app.utils.adapters.cache_adapter import is_redis_enabled
from app.utils.metrics import snapshot as metrics_snapshot
from app.observability.prometheus_exporter import render_prometheus_text

router = APIRouter()

@router.get("/healthz")
def healthz():
    return {"status": "ok"}

@router.get("/")
def root():
    return {"name": APP_NAME, "status": "ok"}

@router.get("/google_login/google/authorized", name="google_authorized")
async def google_authorized(code: str | None = None, state: str | None = None):
    if not code:
        return {"detail": "missing code"}
    # Include ROOT_PATH (e.g. '/api') so dev proxy (vite) and production reverse proxies route correctly
    redirect_url = f"{ROOT_PATH}/auth/google/callback?code={code}"
    if state:
        redirect_url += f"&state={state}"
    return RedirectResponse(url=redirect_url)


@router.get("/whoami")
def whoami(user: models.User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email}


@router.get("/admin/ping")
def admin_ping(_: models.User = Depends(require_admin)):
    return {"ok": True}


@router.get("/debug/cache")
def debug_cache_status():
    if not DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "redis_enabled": is_redis_enabled(),
    }


@router.get("/debug/metrics")
def debug_metrics():
    if not DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    return metrics_snapshot()

@router.get("/metrics")
def metrics_exposition():
    # Exponer siempre; si se requiere proteger, se puede añadir dependencias/guardas
    body = render_prometheus_text()
    return Response(content=body, media_type="text/plain; version=0.0.4; charset=utf-8")
