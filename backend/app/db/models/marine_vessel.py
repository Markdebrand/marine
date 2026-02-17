from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship, validates

from app.db.database import Base


class MarineVessel(Base):
    __tablename__ = "marine_vessel"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mmsi = Column(String(16), nullable=False, unique=True, index=True)
    imo = Column(String(16), nullable=True, unique=True, index=True)
    name = Column(String(255), nullable=True)
    type = Column(String(64), nullable=True)
    flag = Column(Integer, ForeignKey("marine_country.mid"), nullable=True)
    length = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    ext_refs = Column(postgresql.JSONB, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    country = relationship("MarineCountry", foreign_keys=[flag])
    watchlist_items = relationship("MarineWatchlist", back_populates="vessel")

    @validates("mmsi")
    def validate_mmsi_and_set_flag(self, key, value):
        """Automatically set the flag MID whenever mmsi is set."""
        if value and len(value) >= 3:
            try:
                self.flag = int(value[:3])
            except (ValueError, TypeError):
                pass
        return value

