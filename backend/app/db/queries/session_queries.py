from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.db import models as m
from app.core.auth.session_manager import invalidate_session_cache


def create_session_token(
    db: Session,
    *,
    user_id: int,
    token_hash: str,
    user_agent: Optional[str],
    ip: Optional[str],
    expires_at: datetime,
) -> m.SessionToken:
    st = m.SessionToken(
        user_id=user_id,
        token_hash=token_hash,
        user_agent=user_agent,
        ip=ip,
        expires_at=expires_at,
    )
    db.add(st)
    db.commit()
    db.refresh(st)
    return st


def get_session_by_hash(db: Session, token_hash: str) -> Optional[m.SessionToken]:
    return db.query(m.SessionToken).filter(m.SessionToken.token_hash == token_hash).first()


def revoke_session_token(db: Session, st: m.SessionToken, *, reason: Optional[str] = None) -> m.SessionToken:
    import logging
    logger = logging.getLogger("session_token")
    logger.info(f"Revocando sesión: id={getattr(st, 'id', None)}, user_id={getattr(st, 'user_id', None)}, token_hash={getattr(st, 'token_hash', None)}")
    logger.info(f"Antes: revoked_at={getattr(st, 'revoked_at', None)}, active_seconds={getattr(st, 'active_seconds', None)}, last_seen_at={getattr(st, 'last_seen_at', None)}")
    now = datetime.now(timezone.utc)
    st.revoked_at = now  # type: ignore[assignment]
    # Si el cliente ya envió active_seconds en logout, respétalo y no recalcules
    already_set = getattr(st, 'active_seconds', None)
    if reason == "logout" and isinstance(already_set, int) and already_set > 0:
        pass
    else:
        # Calcular active_seconds robusto en backend
        try:
            start = getattr(st, 'created_at', None)
            last = getattr(st, 'last_seen_at', None)
            # Si no hubo actividad (last_seen_at vacío o prácticamente igual a created_at), usa revoked_at/now
            if last is None:
                last = getattr(st, 'revoked_at', None) or now
            elif start is not None:
                try:
                    near_zero = (last - start).total_seconds()  # type: ignore[operator]
                    if near_zero <= 1:
                        last = getattr(st, 'revoked_at', None) or now
                except Exception:
                    last = getattr(st, 'revoked_at', None) or now
            if start is not None and last is not None:
                delta = (last - start).total_seconds()  # type: ignore[operator]
                prev = getattr(st, 'active_seconds', None) or 0
                active_seconds = int(max(0, prev if prev else 0) + max(0.0, delta))
                if active_seconds < 1:
                    active_seconds = 1
                setattr(st, 'active_seconds', active_seconds)
            else:
                setattr(st, 'active_seconds', 1)  # fallback mínimo 1
        except Exception:
            setattr(st, 'active_seconds', 1)
    if reason:
        st.revoke_reason = reason  # type: ignore[assignment]
    db.add(st)
    db.commit()
    db.refresh(st)
    try:
        sid = getattr(st, 'token_hash', None)
        if isinstance(sid, str) and sid:
            invalidate_session_cache(sid)
    except Exception:
        pass
    logger.info(f"Después: revoked_at={getattr(st, 'revoked_at', None)}, active_seconds={getattr(st, 'active_seconds', None)}, last_seen_at={getattr(st, 'last_seen_at', None)}")
    return st


def revoke_all_active_sessions_for_user(db: Session, user_id: int, reason: str = "new_login") -> int:
    """Revoca TODOS los refresh tokens activos del usuario."""
    now = datetime.now(timezone.utc)
    q = (
        db.query(m.SessionToken)
        .filter(
            m.SessionToken.user_id == user_id,
            m.SessionToken.revoked_at.is_(None),
        )
    )
    rows = q.all()
    count = 0
    for st in rows:
        st.revoked_at = now  # type: ignore[assignment]
        st.revoke_reason = reason  # type: ignore[assignment]
        try:
            start = getattr(st, "created_at", None) or now
            end = getattr(st, "last_seen_at", None) or now
            if not end or end < start:
                end = now
            active = int((end - start).total_seconds())
            st.active_seconds = max(1, active)  # type: ignore[assignment]
        except Exception:
            st.active_seconds = 1  # type: ignore[assignment]
        db.add(st)
        count += 1
    if count:
        db.commit()
        try:
            for st in rows:
                sid = getattr(st, 'token_hash', None)
                if isinstance(sid, str) and sid:
                    invalidate_session_cache(sid)
        except Exception:
            pass
    return count


def revoke_other_active_sessions_for_user(db: Session, user_id: int, keep_token_hash: str, reason: str = "concurrency_kill") -> int:
    """Revoca todos los refresh tokens activos del usuario, excepto el indicado."""
    now = datetime.now(timezone.utc)
    q = (
        db.query(m.SessionToken)
        .filter(
            m.SessionToken.user_id == user_id,
            m.SessionToken.revoked_at.is_(None),
            m.SessionToken.token_hash != keep_token_hash,
        )
    )
    rows = q.all()
    count = 0
    for st in rows:
        st.revoked_at = now  # type: ignore[assignment]
        st.revoke_reason = reason  # type: ignore[assignment]
        try:
            start = getattr(st, "created_at", None) or now
            end = getattr(st, "last_seen_at", None) or now
            if not end or end < start:
                end = now
            active = int((end - start).total_seconds())
            st.active_seconds = max(1, active)  # type: ignore[assignment]
        except Exception:
            st.active_seconds = 1  # type: ignore[assignment]
        db.add(st)
        count += 1
    if count:
        db.commit()
        try:
            for st in rows:
                sid = getattr(st, 'token_hash', None)
                if isinstance(sid, str) and sid:
                    invalidate_session_cache(sid)
        except Exception:
            pass
    return count
