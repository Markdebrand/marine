from __future__ import annotations
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.db.database import Base

class UserPreference(Base):
    __tablename__ = 'user_preferences'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    key = Column(String(100), nullable=False)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'key', name='uq_user_pref_user_key'),
    )

    user = relationship('User', backref='preferences')
