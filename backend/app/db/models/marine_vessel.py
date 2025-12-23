from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship

from app.db.database import Base


class MarineVessel(Base):
    __tablename__ = "marine_vessel"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mmsi = Column(String(16), nullable=False, unique=True, index=True)
    imo = Column(String(16), nullable=True, unique=True, index=True)
    name = Column(String(255), nullable=True)
    type = Column(String(64), nullable=True)
    flag = Column(String(64), nullable=True)
    length = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    ext_refs = Column(postgresql.JSONB, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    watchlist_items = relationship("MarineWatchlist", back_populates="vessel")
