from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, JSON, func

from app.db.database import Base


class MarineProviderContract(Base):
    __tablename__ = "marine_provider_contract"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(128), nullable=False)
    plan = Column(String(128))
    rate_limits_json = Column(JSON, nullable=True)
    retention_days = Column(Integer, nullable=True)
    valid_from = Column(DateTime(timezone=True))
    valid_to = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
