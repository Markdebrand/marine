from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class MarineAlert(Base):
    __tablename__ = "marine_alert"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("res_user.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(64), nullable=False)  # geofence | port | other
    params_json = Column(JSON, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    last_triggered = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("ResUser", back_populates="alerts")
