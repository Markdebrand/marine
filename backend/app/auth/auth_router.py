from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from typing import cast
from sqlalchemy.orm import Session
from jose import jwt
from app.db.database import get_db
from app.db import models
from app.auth.auth_schemas import RegisterRequest, RegisterResponse, LoginRequest, TokenResponse, UserInfo, RefreshRequest, ProfileResponse, ProfileUpdate, SessionEntry, UserUpdateAdmin, PaginatedUsersResponse
from app.auth.security_jwt import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    refresh_expiry,
)
from app.auth.security_passwords import (
    hash_password,
    verify_password,
)
from app.config.settings import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    STATIC_AUTH_EMAIL,
    STATIC_AUTH_PASSWORD,
    STATIC_AUTH_ENABLED,
    STATIC_AUTH_ROLE,
    STATIC_AUTH_SUPERADMIN,
    DEBUG,
    AUTH_COOKIES_ENABLED,
    COOKIE_DOMAIN,
    COOKIE_SECURE,
    COOKIE_SAMESITE,
    JWT_AUDIENCE,
    AUTH_RATE_LIMIT_WINDOW_SECONDS,
    AUTH_RATE_LIMIT_MAX_ATTEMPTS,
)
from app.audit.audit_logger import record_login_success, record_login_failure, record_logout
from app.core.auth.session_manager import get_current_user
from app.db.queries.session_queries import revoke_session_token, revoke_other_active_sessions_for_user, revoke_all_active_sessions_for_user
import logging
from app.utils.adapters.cache_adapter import get_cache, set_cache, clear_cache
from app.core.auth.session_manager import invalidate_session_cache
import time
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from app.core.auth.guards import require_admin, require_superadmin

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("app.auth")
diag_logger = logging.getLogger("app.auth.diagnostic")


def _ensure_rate_limit(email: str, request: Request | None = None) -> str:
    """Ensure rate limit window for the given email+ip. Raises HTTPException(429) on limit exceeded.

    Returns the cache key used for this rate limiter so callers can update/clear it.
    """
    ip = request.client.host if request and request.client else "-"
    rl_key = f"auth:rl:{email.lower()}:{ip}"
    data = get_cache(rl_key) or {"c": 0, "t": 0}
    try:
        c = int(data.get("c", 0))
    except Exception:
        c = 0
    try:
        t = int(data.get("t", 0))
    except Exception:
        t = 0
    now = int(time.time())
    wnd = int(AUTH_RATE_LIMIT_WINDOW_SECONDS)
    maxc = int(AUTH_RATE_LIMIT_MAX_ATTEMPTS)
    if now - t > wnd:
        c = 0
        t = now
    if c >= maxc:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")
    # provisionalmente guardar ventana actualizada
    set_cache(rl_key, {"c": c, "t": t or now}, AUTH_RATE_LIMIT_WINDOW_SECONDS)
    return rl_key


def _set_auth_cookies(response: Response, access_token: str | None, refresh_token: str | None):
    if not AUTH_COOKIES_ENABLED:
        return
    if access_token:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,  # type: ignore[arg-type]
            domain=COOKIE_DOMAIN,
            path="/",
        )
    if refresh_token:
        from datetime import datetime, timezone
        max_age = int((refresh_expiry() - datetime.now(timezone.utc)).total_seconds())
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,  # type: ignore[arg-type]
            domain=COOKIE_DOMAIN,
            path="/",
            max_age=max_age,
        )


def _clear_auth_cookies(response: Response):
    if not AUTH_COOKIES_ENABLED:
        return
    response.delete_cookie("access_token", path="/", domain=COOKIE_DOMAIN)
    response.delete_cookie("refresh_token", path="/", domain=COOKIE_DOMAIN)


@router.post("/register", response_model=RegisterResponse)
def register(
    body: RegisterRequest, 
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_superadmin)
):
    from app.core.services.onboarding_service import UserOnboardingService
    try:
        # Extraer campos adicionales del body
        extra_fields = body.model_dump(exclude={"email", "password", "password_confirmation"})
        persona = UserOnboardingService.create_user_with_started_plan(
            db, 
            body.email, 
            body.password,
            **extra_fields
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RegisterResponse(id=persona.id, email=persona.email)  # type: ignore


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    # Rate limit por IP+email (delegado a helper)
    rl_key = None
    try:
        rl_key = _ensure_rate_limit(body.email)
    except HTTPException:
        raise
    except Exception:
        # If rate limiter fails for any reason, allow login to proceed (best-effort)
        rl_key = None
    # Static fallback if configured
    if STATIC_AUTH_ENABLED and STATIC_AUTH_EMAIL and STATIC_AUTH_PASSWORD and body.email.lower() == STATIC_AUTH_EMAIL.lower():
        static_ok = False
        try:
            if STATIC_AUTH_PASSWORD.startswith("$2b$"):
                static_ok = verify_password(body.password, STATIC_AUTH_PASSWORD)
            else:
                static_ok = (body.password == STATIC_AUTH_PASSWORD)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Static auth verify error: {e}")
            static_ok = False
        if static_ok:
            if DEBUG:
                logging.getLogger(__name__).info("Static auth fallback successful for configured user")
            # Include configured role/superadmin flags for local-only static login
            token = create_access_token("0", role=STATIC_AUTH_ROLE, is_superadmin=STATIC_AUTH_SUPERADMIN)
            try:
                ip = request.client.host if request and request.client else "-"
                ua = request.headers.get("user-agent", "-") if request else "-"
                exp_ts = None
                try:
                    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], audience=JWT_AUDIENCE)
                    exp_ts = payload.get("exp")  # type: ignore
                except Exception:
                    exp_ts = None
                record_login_success(user_id="0", email=body.email.lower(), ip=ip, ua=ua, token=token, exp_ts=exp_ts)
            except Exception:
                pass
            _set_auth_cookies(response, token, None)
            return TokenResponse(access_token=token)
        else:
            if DEBUG:
                logging.getLogger(__name__).info("Static auth fallback email matched but password mismatch")

    # DB-backed auth
    persona = db.query(models.User).filter(models.User.email == body.email.lower()).first()
    if not persona or not verify_password(body.password, persona.password_hash):  # type: ignore
        try:
            ip = request.client.host if request and request.client else "-"
            ua = request.headers.get("user-agent", "-") if request else "-"
            record_login_failure(email=body.email.lower(), ip=ip, ua=ua)
        except Exception:
            pass
        # incrementar contador de intentos fallidos
        try:
            if rl_key:
                data = get_cache(rl_key) or {"c": 0, "t": int(time.time())}
                c = int(data.get("c", 0)) + 1
                t = int(data.get("t", int(time.time())))
                set_cache(rl_key, {"c": c, "t": t}, AUTH_RATE_LIMIT_WINDOW_SECONDS)
        except Exception:
            pass
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Enforce activation status before issuing tokens
    try:
        if hasattr(persona, "is_active") and not bool(getattr(persona, "is_active")):
            raise HTTPException(status_code=403, detail={
                "code": "not_activated",
                "message": "Tu cuenta aún no está activada. Revisa tu email para completar la activación.",
            })
    except HTTPException:
        raise
    except Exception:
        pass

    # ENFORCE: single session policy — comportamiento configurable
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        existing = (
            db.query(models.SessionToken)
            .filter(
                models.SessionToken.user_id == persona.id,
                models.SessionToken.revoked_at.is_(None),
                models.SessionToken.expires_at > now,
            )
            .first()
        )
        if existing is not None:
            try:
                diag_logger.info("login: found existing active session", extra={
                    "user_id": persona.id,
                    "session_id": getattr(existing, 'id', None),
                    "token_hash": getattr(existing, 'token_hash', None),
                })
            except Exception:
                pass
            from app.config.settings import SINGLE_SESSION_POLICY
            policy = (SINGLE_SESSION_POLICY or "block").lower()
            if policy == "block":
                # 409 Conflict con detalle específico para frontend
                raise HTTPException(status_code=409, detail={
                    "code": "single_session_active",
                    "message": "Cierra sesión en el otro dispositivo para continuar.",
                })
            elif policy == "force":
                # Revocar todas las sesiones activas antes de continuar (atomicidad no crítica aquí)
                try:
                    revoke_all_active_sessions_for_user(db, user_id=int(persona.id), reason="force_new_login")
                except Exception:
                    # Si no podemos revocar por alguna razón, fallamos safe (bloquear)
                    raise HTTPException(status_code=409, detail={
                        "code": "single_session_active",
                        "message": "No se pudo cerrar la sesión previa. Intenta de nuevo.",
                    })
    except HTTPException:
        raise
    except Exception:
        # Si hay error consultando, no bloquear por defecto; continuamos con login
        pass

    raw_refresh, refresh_h = generate_refresh_token()
    # Include role and is_superadmin claims for faster client gating
    try:
        effective_role = getattr(persona, 'role', 'user') or 'user'
        if getattr(persona, 'is_superadmin', False):
            effective_role = 'admin'
        is_super = bool(getattr(persona, 'is_superadmin', False))
    except Exception:
        effective_role = 'user'
        is_super = False
    # Fetch subscription status for the token
    from app.db.queries.plan_queries import get_active_subscription
    sub_status = None
    try:
        active_sub = get_active_subscription(db, cast(int, persona.id))
        if active_sub:
            sub_status = active_sub.status
    except Exception:
        pass

    token = create_access_token(str(persona.id), sid=refresh_h, role=effective_role, is_superadmin=is_super, subscription_status=sub_status)

    # Política anterior (revoque otros) eliminada porque ahora bloqueamos cuando hay activa
    try:
        ip = request.client.host if request and request.client else "-"
        ua = request.headers.get("user-agent", "-") if request else "-"
    except Exception:
        ip = "-"
        ua = "-"
    try:
        db.add(models.SessionToken(
            user_id=cast(int, persona.id),
            token_hash=refresh_h,
            user_agent=ua,
            ip=ip,
            expires_at=refresh_expiry(),
        ))
        db.commit()
        try:
            diag_logger.info("login: created session token", extra={"user_id": persona.id, "token_hash": refresh_h})
        except Exception:
            pass
        try:
            invalidate_session_cache(refresh_h)
        except Exception:
            pass
    except Exception:
        db.rollback()
        raw_refresh = None  # type: ignore
    try:
        ip = request.client.host if request and request.client else "-"
        ua = request.headers.get("user-agent", "-") if request else "-"
        exp_ts = None
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], audience=JWT_AUDIENCE)
            exp_ts = payload.get("exp")  # type: ignore
        except Exception:
            exp_ts = None
        record_login_success(user_id=str(persona.id), email=body.email.lower(), ip=ip, ua=ua, token=token, exp_ts=exp_ts)
    except Exception:
        pass
    _set_auth_cookies(response, token, raw_refresh)
    # reset contador de rate limit tras login exitoso
    try:
        if rl_key:
            clear_cache(rl_key)
    except Exception:
        pass
    return TokenResponse(access_token=token, refresh_token=raw_refresh)


# Dependency to extract current user
security = HTTPBearer(auto_error=False)



# Extiende /me para incluir plan_code y features
def _build_profile_response(db: Session, user: models.User) -> ProfileResponse:
    """Builds profile response preferring active subscription in a single query.

    Optimization: Use a single left-join to load the latest subscription, preferring
    active status, and its plan to minimize roundtrips.
    """
    from sqlalchemy import desc, case

    # Compose a single query: prefer active subscriptions, else latest by id
    # Order by active flag desc, then subscription id desc
    active_first = case((models.Subscription.status == 'active', 1), else_=0)
    row = (
        db.query(models.Subscription, models.Plan)
        .outerjoin(models.Plan, models.Subscription.plan_id == models.Plan.id)
        .filter(models.Subscription.user_id == user.id)
        .order_by(desc(active_first), models.Subscription.id.desc())
        .first()
    )

    sub = row[0] if row else None
    plan = row[1] if row else None

    # Rol reportado: usa el rol explícito del usuario y considera superadmin como admin efectivo
    role = getattr(user, 'role', 'user') or 'user'
    if getattr(user, 'is_superadmin', False):
        role = 'admin'
    return ProfileResponse(
        id=user.id,  # type: ignore[arg-type]
        email=user.email,  # type: ignore[arg-type]
        role=role,
        is_superadmin=getattr(user, 'is_superadmin', False),
        first_name=getattr(user, 'first_name', None),
        last_name=getattr(user, 'last_name', None),
        phone=getattr(user, 'phone', None),
        company=getattr(user, 'company', None),
        website=getattr(user, 'website', None),
        bio=getattr(user, 'bio', None),
        plan_code=(getattr(plan, 'code', None) if plan else None),
        plan_name=(getattr(plan, 'name', None) if plan else None),
        subscription_id=(getattr(sub, 'id', None) if sub else None),
        subscription_status=(getattr(sub, 'status', None) if sub else None),
    )


@router.get("/me", response_model=ProfileResponse)
def me(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileResponse:
    # Si está activada la autenticación estática, devolvemos un perfil fijo y NO tocamos la base de datos
    from app.config.settings import STATIC_AUTH_ENABLED, STATIC_AUTH_EMAIL, STATIC_AUTH_ROLE, STATIC_AUTH_SUPERADMIN
    if STATIC_AUTH_ENABLED:
        return ProfileResponse(
            id=0,
            email=STATIC_AUTH_EMAIL,
            role=STATIC_AUTH_ROLE or "user",
            is_superadmin=STATIC_AUTH_SUPERADMIN,
            first_name=None,
            last_name=None,
            phone=None,
            company=None,
            website=None,
            bio=None,
            plan_code=None,
            plan_name=None,
            subscription_id=None,
            subscription_status=None,
        )
    # Si no, comportamiento normal (con cache)
    try:
        key = f"profile:{int(getattr(user,'id'))}"
        cached = get_cache(key)
        if cached:
            return cached  # type: ignore[return-value]
        resp = _build_profile_response(db, user)
        set_cache(key, resp, 60)
        return resp
    except Exception:
        return _build_profile_response(db, user)


class SetPasswordRequest(BaseModel):
    password: str


@router.post("/set_password")
def set_password(body: SetPasswordRequest, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        if getattr(user, 'id', None) == 0:
            raise HTTPException(status_code=400, detail="Cannot set password for pseudo/static user")
        user.password_hash = hash_password(body.password)  # type: ignore
        db.add(user)
        db.commit()
        return {"success": True, "message": "Password updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set password: {e}")


class LogoutRequest(BaseModel):
    refresh_token: str | None = None
    # Optional hint from client: total active seconds since login
    active_seconds: int | None = None


@router.post("/logout")
def logout(request: Request, response: Response, body: LogoutRequest | None = None, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        user_id = str(getattr(user, "id", "-")) if user else "-"
        email = getattr(user, "email", "-") if user else "-"
        ip = request.client.host if request and request.client else "-"
        ua = request.headers.get("user-agent", "-") if request else "-"
        auth = request.headers.get("authorization") or request.headers.get("Authorization") if request else None
        raw_token = None
        if auth and auth.lower().startswith("bearer "):
            raw_token = auth.split(" ", 1)[1].strip()
        record_logout(user_id=user_id, email=email, ip=ip, ua=ua, token=raw_token)
    except Exception:
        pass

    # Revocar la sesión actual de forma robusta, incluso si el cliente no envía refresh_token
    try:
        target_st = None

        # 1) Si el cliente envía el refresh_token en el body, úsalo directamente
        if body and body.refresh_token:
            h = hash_refresh_token(body.refresh_token)
            try:
                diag_logger.info("logout: client provided refresh_token", extra={"user_id": getattr(user,'id',None), "refresh_hash": h})
            except Exception:
                pass
            target_st = db.query(models.SessionToken).filter(models.SessionToken.token_hash == h).first()

        # 2) Si no hay body.refresh_token, intenta extraer el sid del access token ya validado
        if target_st is None:
            try:
                payload = getattr(request.state, "token_payload", None)
                sid = payload.get("sid") if isinstance(payload, dict) else None
                if sid:
                    try:
                        diag_logger.info("logout: extracted sid from access token", extra={"user_id": getattr(user,'id',None), "sid": sid})
                    except Exception:
                        pass
                    target_st = (
                        db.query(models.SessionToken)
                        .filter(models.SessionToken.token_hash == sid)
                        .first()
                    )
            except Exception:
                target_st = None

        # 3) Último recurso: revocar la sesión activa más reciente del usuario
        if target_st is None and user is not None:
            target_st = (
                db.query(models.SessionToken)
                .filter(
                    models.SessionToken.user_id == getattr(user, 'id', None),
                    models.SessionToken.revoked_at.is_(None),
                )
                .order_by(models.SessionToken.id.desc())
                .first()
            )

        if target_st is not None and getattr(target_st, 'revoked_at', None) is None:
            # Si el cliente pasó active_seconds, respétalo
            try:
                if body and isinstance(getattr(body, 'active_seconds', None), int) and int(getattr(body, 'active_seconds')) > 0:
                    target_st.active_seconds = int(getattr(body, 'active_seconds'))  # type: ignore[assignment]
                    db.add(target_st)
                    db.commit()
            except Exception:
                db.rollback()

            # Revocar con helper (calcula active_seconds y limpia caché)
            try:
                revoke_session_token(db, target_st, reason="logout")
                try:
                    invalidate_session_cache(getattr(target_st, 'token_hash', '') or '')
                except Exception:
                    pass
                try:
                    diag_logger.info("logout: revoked session", extra={"user_id": getattr(user,'id',None), "session_id": getattr(target_st,'id',None), "token_hash": getattr(target_st,'token_hash',None)})
                except Exception:
                    pass
            except Exception:
                # Fallback best-effort
                from datetime import datetime, timezone
                target_st.revoked_at = datetime.now(timezone.utc)  # type: ignore[assignment]
                target_st.revoke_reason = "logout"  # type: ignore[assignment]
                db.add(target_st)
                db.commit()
                try:
                    diag_logger.info("logout: fallback revoked session", extra={"user_id": getattr(user,'id',None), "session_id": getattr(target_st,'id',None), "token_hash": getattr(target_st,'token_hash',None)})
                except Exception:
                    pass
    except Exception:
        db.rollback()

    _clear_auth_cookies(response)
    return {"success": True}


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: RefreshRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    if not body.refresh_token:
        raise HTTPException(status_code=400, detail="Falta refresh_token")
    hashed = hash_refresh_token(body.refresh_token)
    st = db.query(models.SessionToken).filter(models.SessionToken.token_hash == hashed, models.SessionToken.revoked_at.is_(None)).first()
    if not st:
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    raw_refresh, refresh_h = generate_refresh_token()
    # Embed role/is_superadmin claims on refreshed token
    try:
        user = db.query(models.User).filter(models.User.id == st.user_id).first()
        effective_role = getattr(user, 'role', 'user') or 'user' if user else 'user'
        if user and getattr(user, 'is_superadmin', False):
            effective_role = 'admin'
        is_super = bool(getattr(user, 'is_superadmin', False)) if user else False
    except Exception:
        effective_role = 'user'
        is_super = False
    try:
        from app.db.queries.plan_queries import get_active_subscription
        sub_status = None
        if user:
            active_sub = get_active_subscription(db, cast(int, user.id))
            if active_sub:
                sub_status = active_sub.status
    except Exception:
        sub_status = None

    token = create_access_token(str(st.user_id), sid=refresh_h, role=effective_role, is_superadmin=is_super, subscription_status=sub_status)
    try:
        # Revoca el usado para refrescar sin hacer commit (permitir atomicidad al crear el nuevo)
        revoke_session_token(db, st, commit=False)

        # Crea el nuevo SessionToken (en la misma transacción)
        new_st = models.SessionToken(
            user_id=int(st.user_id), # type: ignore
            token_hash=refresh_h,
            user_agent=(request.headers.get("user-agent") if request else None),
            ip=(request.client.host if request and request.client else None),
            expires_at=refresh_expiry(),
        )
        db.add(new_st)
        # Commit una sola vez para hacer la rotación atómica
        db.commit()
        db.refresh(new_st)
        try:
            invalidate_session_cache(hashed)
            invalidate_session_cache(refresh_h)
        except Exception:
            pass

        # Revoca cualquier otro activo del mismo usuario (excepto el recién creado)
        try:
            revoke_other_active_sessions_for_user(db, user_id=int(st.user_id), keep_token_hash=refresh_h, reason="single_session_enforced") # type: ignore
        except Exception:
            pass

    except Exception:
        db.rollback()
        raise

    _set_auth_cookies(response, token, raw_refresh)
    return TokenResponse(access_token=token)


# Lightweight heartbeat to update last_seen_at of the active session
class PingRequest(BaseModel):
    refresh_token: str | None = None


@router.post("/ping")
def ping(request: Request, body: PingRequest | None = None, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    from datetime import datetime, timezone
    target = None
    try:
        if body and body.refresh_token:
            h = hash_refresh_token(body.refresh_token)
            target = db.query(models.SessionToken).filter(models.SessionToken.token_hash == h, models.SessionToken.revoked_at.is_(None)).first()
        if target is None:
            # fallback: latest non-revoked session for this user
            target = (
                db.query(models.SessionToken)
                .filter(models.SessionToken.user_id == user.id, models.SessionToken.revoked_at.is_(None))
                .order_by(models.SessionToken.id.desc())
                .first()
            )
        if target is not None:
            target.last_seen_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            # Optionally refresh UA/IP context
            try:
                ua = request.headers.get("user-agent") if request else None
                ip = request.client.host if request and request.client else None
                if ua and not getattr(target, 'user_agent', None):
                    target.user_agent = ua  # type: ignore[assignment]
                if ip and not getattr(target, 'ip', None):
                    target.ip = ip  # type: ignore[assignment]
            except Exception:
                pass
            db.add(target)
            db.commit()
            return {"success": True, "session_id": getattr(target, 'id', None), "ts": getattr(target, 'last_seen_at', None)}
    except Exception:
        db.rollback()
    return {"success": False}


# ---- Admin guard ----
@router.patch("/profile", response_model=ProfileResponse)
def update_profile(body: ProfileUpdate, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileResponse:
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Enforce once-per-30-days for non-admins
    try:
        effective_role = getattr(user, 'role', 'user') or 'user'
        is_admin = effective_role == 'admin' or getattr(user, 'is_superadmin', False)
    except Exception:
        is_admin = False

    if not is_admin:
        from datetime import datetime, timezone, timedelta
        last = getattr(user, 'last_profile_update_at', None)
        if last is not None:
            # If timezone-naive, treat as UTC
            try:
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)  # type: ignore[assignment]
            except Exception:
                pass
            now = datetime.now(timezone.utc)
            if now - last < timedelta(days=30):
                rem = timedelta(days=30) - (now - last)
                # Return clear message including remaining days (rounded up)
                days_left = max(1, int(rem.total_seconds() // 86400))
                raise HTTPException(status_code=429, detail=f"Profile can only be updated once every 30 days. Try again in ~{days_left} day(s).")
    # Update allowed fields only
    allowed = ["first_name", "last_name", "phone", "company", "website", "bio"]
    changed = False
    for field in allowed:
        val = getattr(body, field, None)
        if val is not None:
            setattr(user, field, val)
            changed = True
    if changed:
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to update profile")
        # Update last_profile_update_at if non-admin, or always update to reflect latest change
        from datetime import datetime, timezone
        try:
            user.last_profile_update_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            # Do not fail the request if timestamp update fails
    # Invalidate cached profile
    try:
        from app.utils.adapters.cache_adapter import clear_cache
        clear_cache(f"profile:{int(getattr(user,'id'))}")
    except Exception:
        pass
    return _build_profile_response(db, user)


def _build_session_list(db: Session, user_id: int, limit: int | None = None) -> list[SessionEntry]:
    """Return list[SessionEntry] for given user_id (admin-facing or self), encapsulating active_seconds logic."""
    rows_q = (
        db.query(models.SessionToken)
        .filter(models.SessionToken.user_id == user_id)
        .order_by(models.SessionToken.id.desc())
    )
    if isinstance(limit, int) and limit > 0:
        rows = rows_q.limit(limit).all()
    else:
        rows = rows_q.all()

    from datetime import timezone, datetime
    now = datetime.now(timezone.utc)
    out: list[SessionEntry] = []
    for r in rows:
        stored = getattr(r, 'active_seconds', None)
        try:
            stored_int = int(stored) if stored is not None else 0
        except Exception:
            stored_int = 0
        active_int = stored_int
        try:
            if getattr(r, 'revoked_at', None) is None:
                start = getattr(r, 'created_at', None)
                last = getattr(r, 'last_seen_at', None) or now
                if start is not None and last is not None:
                    delta = (last - start).total_seconds()  # type: ignore[operator]
                    active_int = int(max(0, delta))
            else:
                if not (stored_int and stored_int > 0):
                    start = getattr(r, 'created_at', None)
                    last = getattr(r, 'last_seen_at', None) or getattr(r, 'revoked_at', None) or now
                    if start is not None and last is not None:
                        delta = (last - start).total_seconds()  # type: ignore[operator]
                        active_int = int(max(1, delta))
        except Exception:
            pass
        out.append(SessionEntry(
            id=getattr(r, 'id', None),
            created_at=(getattr(r, 'created_at').isoformat() if getattr(r, 'created_at', None) is not None else ''),
            last_seen_at=(getattr(r, 'last_seen_at').isoformat() if getattr(r, 'last_seen_at', None) is not None else None),
            revoked_at=(getattr(r, 'revoked_at').isoformat() if getattr(r, 'revoked_at', None) is not None else None),
            active_seconds=active_int,
            ip=getattr(r, 'ip', None),
            user_agent=getattr(r, 'user_agent', None),
        ))
    return out


# Sessions list for current user


@router.get("/sessions", response_model=list[SessionEntry])
def sessions(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[SessionEntry]:
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return _build_session_list(db, user.id)


@router.get("/sessions/{user_id}", response_model=list[SessionEntry])
def sessions_for_user(user_id: int, admin: models.User = Depends(require_admin), db: Session = Depends(get_db), limit: int | None = None) -> list[SessionEntry]:
    # Admin-only: list sessions for a specific user
    return _build_session_list(db, user_id, limit)


@router.get("/users/search", response_model=list[UserInfo])
def search_users(q: str, admin: models.User = Depends(require_admin), db: Session = Depends(get_db), limit: int | None = 20) -> list[UserInfo]:
    query = db.query(models.User)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(models.User.email.ilike(like))
    query = query.order_by(models.User.email.asc())
    if isinstance(limit, int) and limit > 0:
        query = query.limit(limit)
    rows = query.all()
    out: list[UserInfo] = []
    for u in rows:
        out.append(UserInfo(id=int(getattr(u, 'id')), email=str(getattr(u, 'email')), is_superadmin=bool(getattr(u, 'is_superadmin', False))))
    return out


@router.put("/users/{user_id}", response_model=ProfileResponse)
def update_user_admin(
    user_id: int,
    body: UserUpdateAdmin,
    admin: models.User = Depends(require_superadmin),
    db: Session = Depends(get_db)
) -> ProfileResponse:
    """Administrative endpoint to update user data and manage subscriptions."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Update user fields
    update_data = body.model_dump(exclude={"cancel_subscription"}, exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    # Handle subscription cancellation/reactivation
    if "cancel_subscription" in body.model_fields_set:
        from datetime import datetime, timezone
        from app.db.models.enums import SubscriptionStatus
        now = datetime.now(timezone.utc)
        
        if body.cancel_subscription:
            # Cancel active subscription
            active_sub = (
                db.query(models.Subscription)
                .filter(
                    models.Subscription.user_id == user_id,
                    models.Subscription.status == SubscriptionStatus.active.value
                )
                .first()
            )
            if active_sub:
                active_sub.status = SubscriptionStatus.canceled.value
                active_sub.canceled_at = now
                db.add(active_sub)
        else:
            # Reactivate canceled subscription if cancel_at is future
            canceled_sub = (
                db.query(models.Subscription)
                .filter(
                    models.Subscription.user_id == user_id,
                    models.Subscription.status == SubscriptionStatus.canceled.value
                )
                .order_by(models.Subscription.id.desc())
                .first()
            )
            if canceled_sub and canceled_sub.cancel_at and canceled_sub.cancel_at > now:
                canceled_sub.status = SubscriptionStatus.active.value
                canceled_sub.canceled_at = None
                db.add(canceled_sub)

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Invalidate cache
        try:
            from app.utils.adapters.cache_adapter import clear_cache
            clear_cache(f"profile:{user_id}")
        except Exception:
            pass
            
        return _build_profile_response(db, user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar usuario: {str(e)}")


@router.get("/users", response_model=PaginatedUsersResponse)
def list_users_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: models.User = Depends(require_superadmin),
    db: Session = Depends(get_db)
) -> PaginatedUsersResponse:
    """Administrative endpoint to list all users with pagination."""
    query = db.query(models.User)
    total = query.count()
    
    rows = (
        query.order_by(models.User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    users = [_build_profile_response(db, u) for u in rows]
    
    return PaginatedUsersResponse(
        users=users,
        total=total,
        page=page,
        page_size=page_size
    )
