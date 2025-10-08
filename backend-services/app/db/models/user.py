from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint, event, func
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.auth.security_passwords import verify_password as _verify_password


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(16), nullable=False, default="user", index=True)
    is_superadmin = Column(Boolean, nullable=False, default=False)
    # Activation / status control
    is_active = Column(Boolean, nullable=False, default=True)
    # Optional Odoo linkage for idempotency/audit
    odoo_lead_id = Column(String(64))
    odoo_partner_id = Column(String(64))
    # Optional profile fields
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))
    company = Column(String(255))
    website = Column(String(255))
    bio = Column(String(1024))
    # Rate limit for profile edits
    last_profile_update_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
    )

    def verify_password(self, raw: str) -> bool:
        return _verify_password(raw, self.password_hash)  # type: ignore[arg-type]


# Allowed coarse roles in the current app
_ALLOWED_ROLES = {"admin", "user", "cliente"}


def _coerce_role(target: User) -> None:
    try:
        r = getattr(target, "role", None)
    except Exception:
        r = None
    if r not in _ALLOWED_ROLES:
        target.role = "user"  # type: ignore[assignment]


@event.listens_for(User, "before_insert")
def _user_before_insert(mapper, connection, target: User):  # type: ignore[no-redef]
    _coerce_role(target)


@event.listens_for(User, "before_update")
def _user_before_update(mapper, connection, target: User):  # type: ignore[no-redef]
    _coerce_role(target)


class SessionToken(Base):
    __tablename__ = "session_tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    user_agent = Column(String(255))
    ip = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))
    revoke_reason = Column(String(255))
    # Total de segundos "activos" de la sesión (login -> último seen/revoke)
    active_seconds = Column(Integer)
