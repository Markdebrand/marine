from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class PasswordResetToken(Base):
    """
    Model for password reset tokens.
    Tokens are hashed before storage for security.
    """
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(64), nullable=True)
    
    # Relationship to user
    user = relationship("User", backref="password_reset_tokens")
