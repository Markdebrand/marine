from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func, Index
from sqlalchemy.orm import relationship

from app.db.database import Base


class Release(Base):
    """Cabecera de un Release / Changelog.

    Contiene metadatos generales y una colección de secciones.
    """

    __tablename__ = "releases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(50), nullable=False)
    version = Column(String(32), nullable=False, index=True)
    type = Column(String(32), nullable=False)  # p.ej: feature, fix, patch, beta, etc.
    short_description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sections = relationship(
        "ReleaseSection",
        back_populates="release",
        cascade="all, delete-orphan",
        order_by="ReleaseSection.position.asc()",
    )

    __table_args__ = (
        Index("ix_release_version_type", "version", "type", unique=True),
    )


class ReleaseSection(Base):
    __tablename__ = "release_sections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    release_id = Column(Integer, ForeignKey("releases.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)  # Sin límite de caracteres
    position = Column(Integer, nullable=False, default=0)

    release = relationship("Release", back_populates="sections")
