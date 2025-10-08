from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class ActivationToken(Base):
    __tablename__ = "activation_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))
    revoked = Column(Boolean, nullable=False, default=False)

    user = relationship("User", backref="activation_tokens")
