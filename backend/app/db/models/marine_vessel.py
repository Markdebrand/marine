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
        """Automatically set the flag MID whenever mmsi is set, handling special formats."""
        if not value or not isinstance(value, str):
            return value

        mid = None
        # Robust parsing based on ITU MMSI structure
        if value.startswith("111"):  # SAR Aircraft
            if len(value) >= 6:
                mid = value[3:6]
        elif value.startswith("00"):  # Coast Stations
            if len(value) >= 5:
                mid = value[2:5]
        elif value.startswith("0"):  # Group MMSI
            if len(value) >= 4:
                mid = value[1:4]
        elif value.startswith("99") or value.startswith("98"):  # AtoN or craft associated with parent
            if len(value) >= 5:
                mid = value[2:5]
        elif len(value) >= 3:  # Standard Vessel
            mid = value[:3]

        if mid:
            try:
                self.flag = int(mid)
            except (ValueError, TypeError):
                pass
        return value

