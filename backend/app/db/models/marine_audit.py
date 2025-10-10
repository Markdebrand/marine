from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class MarineAudit(Base):
    __tablename__ = "marine_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_id = Column(Integer, ForeignKey("res_user.id", ondelete="SET NULL"))
    action = Column(String(100), nullable=False)
    details = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    actor = relationship("ResUser")
