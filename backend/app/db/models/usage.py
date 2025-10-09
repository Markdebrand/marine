from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.types import JSON

from app.db.database import Base


class UsageCounter(Base):
    __tablename__ = "usage_counters"
    id = Column(Integer, primary_key=True, autoincrement=True)

    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), index=True, nullable=False)
    feature_key = Column(String(64), nullable=False, index=True)

    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    used = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("subscription_id", "feature_key", "period_start", name="uq_usage_period"),
    )
