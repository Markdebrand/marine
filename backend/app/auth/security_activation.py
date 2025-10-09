import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

ACTIVATION_TOKEN_BYTES = 32  # ~ 43 chars urlsafe
ACTIVATION_TTL_HOURS = 48


def gen_raw_token() -> str:
    return secrets.token_urlsafe(ACTIVATION_TOKEN_BYTES)


def hash_token(raw: str) -> str:
    # Hash rápido para lookup (no reversible)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def exp_at(hours: int = ACTIVATION_TTL_HOURS) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def verify_hmac_signature(secret: str, body_bytes: bytes, signature: str) -> bool:
    mac = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
    try:
        return hmac.compare_digest(mac, signature)
    except Exception:
        return False
