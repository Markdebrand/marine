"""Servicio de auditoría privada (solo backend).

Registra eventos de autenticación, tiempos de request y sesiones en memoria.
"""
from __future__ import annotations
import logging
import time
import hashlib
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger("app.audit")


def _token_id(token: str) -> str:
    # Identificador opaco derivado del token sin exponerlo en claro
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class SessionStore:
    def __init__(self) -> None:
        # token_id -> data
        self._store: Dict[str, Dict[str, Any]] = {}

    def start(self, token: str, user_id: str, email: str, ip: str, ua: str, exp_ts: Optional[float]) -> str:
        tid = _token_id(token)
        self._store[tid] = {
            "user_id": user_id,
            "email": email,
            "ip": ip,
            "ua": ua,
            "start_ts": time.time(),
            "exp_ts": exp_ts,
        }
        return tid

    def end(self, token: str) -> Tuple[Optional[float], Optional[Dict[str, Any]]]:
        tid = _token_id(token)
        data = self._store.pop(tid, None)
        if not data:
            return None, None
        duration = max(0.0, time.time() - float(data.get("start_ts", time.time())))
        return duration, data


session_store = SessionStore()


def record_login_success(user_id: str, email: str, ip: str, ua: str, token: str, exp_ts: Optional[float]) -> None:
    tid = session_store.start(token=token, user_id=user_id, email=email, ip=ip, ua=ua, exp_ts=exp_ts)
    logger.info(
        "login success user_id=%s email=%s ip=%s ua=%s token_id=%s exp_ts=%s",
        user_id,
        email,
        ip,
        ua,
        tid,
        int(exp_ts) if exp_ts else "-",
    )


def record_login_failure(email: str, ip: str, ua: str) -> None:
    logger.warning("login failed email=%s ip=%s ua=%s", email, ip, ua)


def record_logout(user_id: str, email: str, ip: str, ua: str, token: Optional[str]) -> None:
    duration, data = (None, None)
    if token:
        duration, data = session_store.end(token)
    logger.info(
        "logout user_id=%s email=%s ip=%s ua=%s session_ms=%s",
        user_id,
        email,
        ip,
        ua,
        f"{(duration or 0.0)*1000.0:.2f}",
    )


def record_request_timing(method: str, path: str, status: int, duration_ms: float, user_id: Optional[str], ip: str, ua: str) -> None:
    logger.info(
        "request method=%s path=%s status=%s duration_ms=%.2f user_id=%s ip=%s ua=%s",
        method,
        path,
        status,
        duration_ms,
        user_id if user_id is not None else "-",
        ip,
        ua,
    )
