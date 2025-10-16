from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, func, Index
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geometry
from sqlalchemy.orm import relationship

from app.db.database import Base


class MarinePort(Base):
    __tablename__ = "marine_port"

    id = Column(Integer, primary_key=True, autoincrement=True)
    unlocode = Column(String(16), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    country = Column(String(128))
    ext_refs = Column(postgresql.JSONB, nullable=True)
    coords = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_marine_port_unlocode_name", "unlocode", "name"),
    )

    # relaciones opcionales
    # events = relationship("PortEvent", back_populates="port")
