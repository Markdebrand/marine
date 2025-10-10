from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base


class MarineWatchlist(Base):
    __tablename__ = "marine_watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("res_user.id", ondelete="CASCADE"), nullable=False, index=True)
    vessel_id = Column(Integer, ForeignKey("marine_vessel.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("ResUser", back_populates="watchlist")
    vessel = relationship("MarineVessel", back_populates="watchlist_items")

    __table_args__ = (
        UniqueConstraint("user_id", "vessel_id", name="uq_watchlist_user_vessel"),
    )
