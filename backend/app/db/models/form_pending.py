from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Index, func, JSON

from app.db.database import Base


class FormPending(Base):
    __tablename__ = "form_pending"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Form fields
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(32))
    email = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    job_title = Column(String(150), nullable=False)
    employees = Column(String(50), nullable=False)
    industry = Column(String(150), nullable=False)
    subscription = Column(JSON, nullable=False, default=list)
    geographic = Column(String(150), nullable=False)

    # Status & timestamps
    status = Column(String(32), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_form_pending_email_created", "email", "created_at"),
    )
