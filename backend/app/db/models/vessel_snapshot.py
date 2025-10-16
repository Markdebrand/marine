from __future__ import annotations

from sqlalchemy import Column, String, DateTime, Float, Integer, func, ForeignKey
from geoalchemy2 import Geometry
from sqlalchemy.orm import relationship

from app.db.database import Base


class VesselSnapshot(Base):
    __tablename__ = "vessel_snapshot"

    mmsi = Column(String(16), primary_key=True)
    last_ts = Column(DateTime(timezone=True), nullable=False)
    last_geom = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    sog = Column(Float)
    cog = Column(Float)
    heading = Column(Float)
    nav_status = Column(String(50))

    latest_state_id = Column(Integer, ForeignKey("vessel_state.id", ondelete="SET NULL"), nullable=True)
    latest_state = relationship("VesselState", back_populates="snapshot")
