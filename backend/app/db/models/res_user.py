from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class ResUser(Base):
    __tablename__ = "res_user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(128), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    watchlist = relationship("MarineWatchlist", back_populates="user")
    alerts = relationship("MarineAlert", back_populates="user")
