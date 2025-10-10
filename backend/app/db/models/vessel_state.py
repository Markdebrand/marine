from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Float, func, text
from sqlalchemy import Index
from sqlalchemy.orm import relationship

from app.db.database import Base


class VesselState(Base):
    __tablename__ = "vessel_state"

    # Nota: este modelo está pensado para ser mapeado a una hypertable en TimescaleDB mediante migraciones
    id = Column(Integer, primary_key=True, autoincrement=True)
    mmsi = Column(String(16), nullable=False, index=True)
    ts = Column(DateTime(timezone=True), nullable=False, index=True)
    geom = Column(String(255))  # placeholder; usar geometry(Point, 4326) en migración
    sog = Column(Float)
    cog = Column(Float)
    heading = Column(Float)
    nav_status = Column(String(50))
    src = Column(String(64))

    __table_args__ = (
        Index("ix_vessel_state_mmsi_ts", "mmsi", "ts"),
    )

    # relaciones con snapshot (no obligatorias)
    snapshot = relationship("VesselSnapshot", back_populates="latest_state")
