from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config.settings import AUTH_COOKIES_ENABLED, JWT_AUDIENCE, JWT_ALGORITHM, JWT_SECRET_KEY, SESSION_CACHE_TTL
from app.utils.adapters.cache_adapter import get_cache, set_cache, clear_cache, is_redis_enabled
import logging
diag_logger = logging.getLogger("app.auth.session_diag")
from app.db.database import get_db
from app.db import models as m


# Shared bearer extractor (for Authorization: Bearer <token>)
_bearer = HTTPBearer(auto_error=False)


def extract_token_from_request(request: Request, creds: HTTPAuthorizationCredentials | None) -> Optional[str]:
    """Get JWT from Authorization header (Bearer) or cookie fallback if enabled.

    Nota: Algunos middlewares no construyen la dependencia HTTPBearer; por ello,
    además de `creds`, inspeccionamos manualmente el header Authorization.
    """
    # 1) Vía dependencia HTTPBearer
    if creds and (creds.scheme or "").lower() == "bearer":
        return creds.credentials
    # 2) Header Authorization manual (para middlewares)
    try:
        auth = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            return auth.split(" ", 1)[1].strip()
    except Exception:
        pass
    # 3) Cookie HttpOnly (si está habilitado)
    if AUTH_COOKIES_ENABLED:
        token = request.cookies.get("access_token")
        if token:
            return token
    return None


def decode_token(token: str) -> dict:
    """Decode and validate JWT; raises HTTP 401 on error."""
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], audience=JWT_AUDIENCE)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


def get_token_payload(request: Request, creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    """Return validated JWT payload, preferring the one cached by middleware."""
    payload = getattr(request.state, "token_payload", None)
    if isinstance(payload, dict) and payload.get("sub") is not None:
        return payload
    token = extract_token_from_request(request, creds)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Falta token")
    payload = decode_token(token)
    try:
        request.state.token_payload = payload  # type: ignore[attr-defined]
        request.state.sub = payload.get("sub")  # type: ignore[attr-defined]
    except Exception:
        pass
    return payload


def get_current_user(request: Request, payload: dict = Depends(get_token_payload), db: Session = Depends(get_db)) -> m.User:
    """Load and return current user using the JWT subject (sub) and validate sid if present."""
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sin sub")
    if str(sub) == "0":
        # minimal pseudo user for static auth
        return m.User(id=0, email="static@example.com", password_hash="")  # type: ignore[arg-type]
    try:
        uid = int(sub)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sub inválido")
    # If JWT carries sid, validate session is still active (cached) and gently update last_seen_at
    sid = payload.get("sid")
    if sid:
        cache_key = f"session:active:{sid}"
        try:
            diag_logger.debug("session_manager: checking session cache", extra={"cache_key": cache_key})
        except Exception:
            pass
        cached = get_cache(cache_key)
        if cached is False:
            try:
                diag_logger.info("session_manager: cache indicates session revoked", extra={"cache_key": cache_key})
            except Exception:
                pass
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="session_revoked")
        # If cache says True, but Redis is NOT enabled (in-memory per-worker cache),
        # the value may be stale in other workers. In that case verify DB to avoid
        # false positives. When Redis is enabled the shared cache is authoritative.
        if cached is True and not is_redis_enabled():
            try:
                st_check = (
                    db.query(m.SessionToken)
                    .filter(
                        m.SessionToken.token_hash == sid,
                        m.SessionToken.revoked_at.is_(None),
                    )
                    .first()
                )
                if not st_check:
                    # mark cache as revoked and fail
                    try:
                        set_cache(cache_key, False, SESSION_CACHE_TTL)
                    except Exception:
                        pass
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="session_revoked")
            except HTTPException:
                raise
            except Exception:
                # On DB errors, be permissive and continue (existing behavior)
                pass
        if cached is not True:
            st = (
                db.query(m.SessionToken)
                .filter(
                    m.SessionToken.token_hash == sid,
                    m.SessionToken.revoked_at.is_(None),
                )
                .first()
            )
            if not st:
                try:
                    set_cache(cache_key, False, SESSION_CACHE_TTL)
                    try:
                        diag_logger.info("session_manager: DB shows session revoked; set cache False", extra={"cache_key": cache_key})
                    except Exception:
                        pass
                except Exception:
                    pass
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="session_revoked")
            try:
                set_cache(cache_key, True, SESSION_CACHE_TTL)
                try:
                    diag_logger.debug("session_manager: set session cache True", extra={"cache_key": cache_key})
                except Exception:
                    pass
            except Exception:
                pass
            # Throttled last_seen_at update
            try:
                from datetime import datetime, timezone, timedelta
                now = datetime.now(timezone.utc)
                last = getattr(st, 'last_seen_at', None)
                should_update = False
                if last is None:
                    should_update = True
                else:
                    try:
                        if last.tzinfo is None:
                            last = last.replace(tzinfo=timezone.utc)  # type: ignore[assignment]
                    except Exception:
                        pass
                    if (now - last) >= timedelta(seconds=60):
                        should_update = True
                if should_update:
                    st.last_seen_at = now  # type: ignore[assignment]
                    db.add(st)
                    db.commit()
            except Exception:
                db.rollback()

    user = db.get(m.User, uid)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    try:
        request.state.user = user  # type: ignore[attr-defined]
    except Exception:
        pass
    return user


def invalidate_session_cache(sid: str) -> None:
    try:
        clear_cache(f"session:active:{sid}")
    except Exception:
        pass


def get_current_sub(request: Request, creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    """Return only the JWT subject without touching the database."""
    payload = getattr(request.state, "token_payload", None)
    if not isinstance(payload, dict):
        token = extract_token_from_request(request, creds)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Falta token")
        payload = decode_token(token)
    sub = payload.get("sub") if isinstance(payload, dict) else None
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sin sub")
    return str(sub)
