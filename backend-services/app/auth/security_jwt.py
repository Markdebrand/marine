from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import uuid
from jose import jwt
import secrets
import hashlib
import hmac
from app.config.settings import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_AUDIENCE,
    REFRESH_TOKEN_EXPIRE_DAYS,
    REFRESH_TOKEN_EXPIRE_MINUTES,
)

def create_access_token(subject: str, sid: Optional[str] = None, expires_minutes: Optional[int] = None, role: Optional[str] = None, is_superadmin: Optional[bool] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode: dict = {
        "sub": subject,
        "exp": expire,
        "jti": uuid.uuid4().hex,
        "aud": JWT_AUDIENCE,
    }
    if sid:
        to_encode["sid"] = sid
    # Optional claims for quicker client-side gating (non-authoritative; server still enforces via deps)
    if role:
        to_encode["role"] = role
    if is_superadmin is not None:
        to_encode["is_superadmin"] = bool(is_superadmin)
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decodifica y valida el access token, validando audience.

    Lanza jose.JWTError si no es válido.
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], audience=JWT_AUDIENCE)


def _hmac_sha256(data: str, key: str) -> str:
    return hmac.new(key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()

def generate_refresh_token() -> Tuple[str, str]:
    """Genera un refresh token aleatorio seguro y su hash HMAC-SHA256.

    Returns: (raw_token, hashed_token)
    """
    raw = secrets.token_urlsafe(48)
    return raw, _hmac_sha256(raw, JWT_SECRET_KEY)


def hash_refresh_token(raw: str) -> str:
    """Calcula el HMAC-SHA256 del refresh token para guardarlo/consultarlo en BD."""
    return _hmac_sha256(raw, JWT_SECRET_KEY)


def refresh_expiry(days: Optional[int] = None) -> datetime:
    """Devuelve la fecha de expiración para un refresh token."""
    # Si days es 0 o None y REFRESH_TOKEN_EXPIRE_DAYS es 0, usar minutos
    if (days is None or days == 0) and REFRESH_TOKEN_EXPIRE_DAYS == 0:
        return datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    return datetime.now(timezone.utc) + timedelta(days=days or REFRESH_TOKEN_EXPIRE_DAYS)
