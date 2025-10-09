from __future__ import annotations

from sqlalchemy.orm import Session
from typing import Optional, Iterable

from app.db import models as m


def get_user_by_email(db: Session, email: str) -> Optional[m.User]:
    return db.query(m.User).filter(m.User.email == email.lower()).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[m.User]:
    return db.get(m.User, user_id)


def get_superadmin(db: Session) -> Optional[m.User]:
    return db.query(m.User).filter(m.User.is_superadmin.is_(True)).first()


def list_users_by_ids(db: Session, ids: Iterable[int]) -> list[m.User]:
    return db.query(m.User).filter(m.User.id.in_(list(ids))).all()
