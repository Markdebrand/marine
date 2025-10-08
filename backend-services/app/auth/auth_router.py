from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from typing import cast
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.db.database import get_db
from app.db import models
from app.auth.auth_schemas import RegisterRequest, RegisterResponse, LoginRequest, TokenResponse, UserInfo, RefreshRequest, ProfileResponse, ProfileUpdate
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
from app.db.queries.session_queries import revoke_session_token, revoke_all_active_sessions_for_user, revoke_other_active_sessions_for_user
import logging
from app.utils.adapters.cache_adapter import get_cache, set_cache, clear_cache
from app.core.auth.session_manager import invalidate_session_cache

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("app.auth")


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
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    from app.core.services.onboarding_service import UserOnboardingService
    try:
        persona = UserOnboardingService.create_user_with_started_plan(db, body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RegisterResponse(id=persona.id, email=persona.email)  # type: ignore


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    # Rate limit por IP+email
    rl_key = None
    try:
        ip = request.client.host if request and request.client else "-"
        rl_key = f"auth:rl:{body.email.lower()}:{ip}"
        data = get_cache(rl_key) or {"c": 0, "t": 0}
        c = int(data.get("c", 0))
        t = int(data.get("t", 0))
        import time as _tm
        now = int(_tm.time())
        wnd = int(AUTH_RATE_LIMIT_WINDOW_SECONDS)
        maxc = int(AUTH_RATE_LIMIT_MAX_ATTEMPTS)
        if now - t > wnd:
            c = 0; t = now
        if c >= maxc:
            raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")
        # provisionalmente guardar ventana actualizada
        set_cache(rl_key, {"c": c, "t": t or now}, AUTH_RATE_LIMIT_WINDOW_SECONDS)
    except HTTPException:
        raise
    except Exception:
        pass
    # Static fallback if configured
    if STATIC_AUTH_EMAIL and STATIC_AUTH_PASSWORD and body.email.lower() == STATIC_AUTH_EMAIL.lower():
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
            # pseudo-user has no role; omit claim
            token = create_access_token("0", role=None, is_superadmin=False)
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
                data = get_cache(rl_key) or {"c": 0, "t": int(__import__('time').time())}
                c = int(data.get("c", 0)) + 1
                t = int(data.get("t", int(__import__('time').time())))
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

    # ENFORCE: single session policy – si ya existe una sesión activa, bloquear este login y pedir cerrar la otra
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
            # 409 Conflict con detalle específico para frontend
            raise HTTPException(status_code=409, detail={
                "code": "single_session_active",
                "message": "Cierra sesión en el otro dispositivo para continuar.",
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
        effective_role = 'user'; is_super = False
    token = create_access_token(str(persona.id), sid=refresh_h, role=effective_role, is_superadmin=is_super)

    # Política anterior (revoque otros) eliminada porque ahora bloqueamos cuando hay activa
    try:
        ip = request.client.host if request and request.client else "-"
        ua = request.headers.get("user-agent", "-") if request else "-"
    except Exception:
        ip = "-"; ua = "-"
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
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer(auto_error=False)



# Extiende /me para incluir plan_code y features
def _build_profile_response(db: Session, user: models.User) -> ProfileResponse:
    """Builds profile response preferring active subscription in a single query.

    Optimization: Use a single left-join to load the latest subscription, preferring
    active status, and its plan to minimize roundtrips.
    """
    from sqlalchemy import desc, case
    from sqlalchemy.orm import aliased

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
    # Cachear perfil 60s
    try:
        key = f"profile:{int(getattr(user,'id'))}"
        cached = get_cache(key)
        if cached:
            return cached  # type: ignore[return-value]
        resp = _build_profile_response(db, user)
        # Guardar como dict para robustez de serialización
        set_cache(key, resp, 60)
        return resp
    except Exception:
        return _build_profile_response(db, user)


from pydantic import BaseModel


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

    # Revoke refresh token if provided
    try:
        if body and body.refresh_token:
            h = hash_refresh_token(body.refresh_token)
            st = db.query(models.SessionToken).filter(models.SessionToken.token_hash == h).first()
            if st and getattr(st, 'revoked_at', None) is None:
                # If client provided active_seconds, set it now so revoke helper respects it
                try:
                    if isinstance(getattr(body, 'active_seconds', None), int) and int(getattr(body, 'active_seconds')) > 0:
                        st.active_seconds = int(getattr(body, 'active_seconds'))  # type: ignore[assignment]
                        db.add(st)
                        db.commit()
                except Exception:
                    db.rollback()
                # use revoke helper to compute active_seconds and persist
                try:
                    revoke_session_token(db, st, reason="logout")
                    try:
                        invalidate_session_cache(getattr(st, 'token_hash', '') or '')
                    except Exception:
                        pass
                except Exception:
                    # best-effort fallback
                    from datetime import datetime, timezone
                    st.revoked_at = datetime.now(timezone.utc)  # type: ignore[assignment]
                    st.revoke_reason = "logout"  # type: ignore[assignment]
                    db.add(st)
                    db.commit()
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
        effective_role = 'user'; is_super = False
    token = create_access_token(str(st.user_id), sid=refresh_h, role=effective_role, is_superadmin=is_super)
    try:
        # Revoca el usado para refrescar
        revoke_session_token(db, st)

        # Crea el nuevo SessionToken
        new_st = models.SessionToken(
            user_id=int(st.user_id), # type: ignore
            token_hash=refresh_h,
            user_agent=(request.headers.get("user-agent") if request else None),
            ip=(request.client.host if request and request.client else None),
            expires_at=refresh_expiry(),
        )
        db.add(new_st)
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
from app.core.auth.guards import require_admin


@router.get("/profile", response_model=ProfileResponse)
def profile(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileResponse:
    return _build_profile_response(db, user)


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


# Sessions list for current user
from app.auth.auth_schemas import SessionEntry, UserInfo


@router.get("/sessions", response_model=list[SessionEntry])
def sessions(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[SessionEntry]:
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Query session tokens for user
    rows = (
        db.query(models.SessionToken)
        .filter(models.SessionToken.user_id == user.id)
        .order_by(models.SessionToken.id.desc())
        .all()
    )
    out: list[SessionEntry] = []
    from datetime import timezone, datetime
    now = datetime.now(timezone.utc)
    for r in rows:
        # Stored value (may be None or stale)
        stored = getattr(r, 'active_seconds', None)
        try:
            stored_int = int(stored) if stored is not None else 0
        except Exception:
            stored_int = 0

        # Compute active seconds dynamically for active (not revoked) sessions
        active_int = stored_int
        try:
            if getattr(r, 'revoked_at', None) is None:
                # Active session: use last_seen_at or now to compute up-to-date active seconds
                start = getattr(r, 'created_at', None)
                last = getattr(r, 'last_seen_at', None) or now
                if start is not None and last is not None:
                    delta = (last - start).total_seconds()  # type: ignore[operator]
                    active_int = int(max(0, delta))
                else:
                    active_int = stored_int or 0
            else:
                # Revoked session: prefer stored value, but compute fallback if missing
                if stored_int and stored_int > 0:
                    active_int = stored_int
                else:
                    start = getattr(r, 'created_at', None)
                    last = getattr(r, 'last_seen_at', None) or getattr(r, 'revoked_at', None) or now
                    if start is not None and last is not None:
                        delta = (last - start).total_seconds()  # type: ignore[operator]
                        active_int = int(max(1, delta))
                    else:
                        active_int = 1
        except Exception:
            active_int = stored_int or 0

        entry = SessionEntry(
            id=getattr(r, 'id', None),
            created_at=(getattr(r, 'created_at').isoformat() if getattr(r, 'created_at', None) is not None else ''),
            last_seen_at=(getattr(r, 'last_seen_at').isoformat() if getattr(r, 'last_seen_at', None) is not None else None),
            revoked_at=(getattr(r, 'revoked_at').isoformat() if getattr(r, 'revoked_at', None) is not None else None),
            active_seconds=active_int,
            ip=getattr(r, 'ip', None),
            user_agent=getattr(r, 'user_agent', None),
        )
        out.append(entry)
    return out


@router.get("/sessions/{user_id}", response_model=list[SessionEntry])
def sessions_for_user(user_id: int, admin: models.User = Depends(require_admin), db: Session = Depends(get_db), limit: int | None = None) -> list[SessionEntry]:
    # Admin-only: list sessions for a specific user
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
