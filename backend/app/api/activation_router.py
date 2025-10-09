from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db.database import get_db
from app.db import models
from app.db.models.activation import ActivationToken
from app.auth.security_activation import hash_token
from app.auth.security_passwords import hash_password
from app.auth.security_jwt import create_access_token
from app.config.settings import AUTH_COOKIES_ENABLED, COOKIE_SECURE, COOKIE_SAMESITE, COOKIE_DOMAIN

router = APIRouter(prefix="/auth/activation", tags=["auth"])


class ActivationInfoResponse(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None


def _load_valid_token(db: Session, raw_token: str) -> tuple[ActivationToken, models.User]:
    th = hash_token(raw_token)
    token = (
        db.query(ActivationToken)
        .filter(
            ActivationToken.token_hash == th,
            ActivationToken.revoked == False,  # noqa: E712
            ActivationToken.used_at.is_(None),
        )
        .first()
    )
    if not token:
        raise HTTPException(status_code=404, detail="Token inválido")
    now = datetime.now(timezone.utc)
    expires_at = getattr(token, "expires_at", None)
    try:
        # If naive, consider UTC
        if expires_at is not None and getattr(expires_at, "tzinfo", None) is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)  # type: ignore[assignment]
    except Exception:
        pass
    if not expires_at or expires_at < now:  # type: ignore[operator]
        raise HTTPException(status_code=410, detail="Token expirado")
    user = db.query(models.User).filter(models.User.id == token.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return token, user


@router.get("")
def details(t: str, db: Session = Depends(get_db)) -> ActivationInfoResponse:
    token, user = _load_valid_token(db, t)
    # Devuelve data no sensible para prellenar la vista
    return ActivationInfoResponse(
        email=user.email,  # type: ignore[arg-type]
        first_name=getattr(user, "first_name", None),
        last_name=getattr(user, "last_name", None),
        company=getattr(user, "company", None),
    )


class ActivationCompleteRequest(BaseModel):
    password: str


@router.post("")
def complete(t: str, body: ActivationCompleteRequest, response: Response, db: Session = Depends(get_db)):
    token, user = _load_valid_token(db, t)

    # Guardar contraseña (hash)
    user.password_hash = hash_password(body.password)  # type: ignore[assignment]
    # Marcar usuario como activo si el campo existe
    try:
        if hasattr(user, "is_active"):
            user.is_active = True  # type: ignore[assignment]
    except Exception:
        pass

    # Marcar token usado
    token.used_at = datetime.now(timezone.utc)  # type: ignore[assignment]
    db.commit()

    # Emitir sesión como en /auth/login
    try:
        effective_role = getattr(user, 'role', 'user') or 'user'
        if getattr(user, 'is_superadmin', False):
            effective_role = 'admin'
        is_super = bool(getattr(user, 'is_superadmin', False))
    except Exception:
        effective_role = 'user'; is_super = False
    access_token = create_access_token(str(user.id), role=effective_role, is_superadmin=is_super)

    # Si login usa cookies HttpOnly, setear aquí igual que en /auth/login
    if AUTH_COOKIES_ENABLED:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,  # type: ignore[arg-type]
            domain=COOKIE_DOMAIN,
            path="/",
        )

    return {"ok": True, "access_token": access_token}
