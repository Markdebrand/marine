from __future__ import annotations

from sqlalchemy import Column, Integer, String, Index

from app.db.database import Base


class MarineCountry(Base):
    __tablename__ = "marine_country"

    mid = Column(Integer, primary_key=True, autoincrement=False)
    pais = Column(String(128), nullable=False)
    country = Column(String(128), nullable=False)

    __table_args__ = (
        Index("ix_marine_country_mid", "mid"),
    )
