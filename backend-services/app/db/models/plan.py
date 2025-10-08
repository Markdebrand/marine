from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, JSON, func
from sqlalchemy.orm import relationship

from app.db.database import Base
from .enums import SubscriptionStatus, SupportLevel


class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    support = Column(String(20), nullable=False, default=SupportLevel.BASIC.value)
    features = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    status = Column(String(30), nullable=False, default=SubscriptionStatus.active.value)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    current_period_start = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    current_period_end = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    cancel_at = Column(DateTime(timezone=True))
    canceled_at = Column(DateTime(timezone=True))
    trial_end = Column(DateTime(timezone=True))
    add_ons = Column(JSON, nullable=True)

    user = relationship("User")
    plan = relationship("Plan")

    __table_args__ = (
        Index("ix_subscriptions_user_status", "user_id", "status"),
    )
