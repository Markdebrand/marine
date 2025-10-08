from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session

from app.db import models as m


def get_active_subscription(db: Session, user_id: int) -> Optional[m.Subscription]:
    """Latest active subscription for a user (status == 'active')."""
    return (
        db.query(m.Subscription)
        .filter(m.Subscription.user_id == user_id, m.Subscription.status == "active")
        .order_by(m.Subscription.id.desc())
        .first()
    )


def get_latest_subscription(db: Session, user_id: int) -> Optional[m.Subscription]:
    """Latest subscription for a user regardless of status."""
    return (
        db.query(m.Subscription)
        .filter(m.Subscription.user_id == user_id)
        .order_by(m.Subscription.id.desc())
        .first()
    )


def get_plan_by_id(db: Session, plan_id: int) -> Optional[m.Plan]:
    return db.get(m.Plan, plan_id)


def get_feature_limit_from_plan(
    db: Session, plan_id: int, feature_key: str, limit_key: str = "max_monthly"
) -> Optional[int]:
    """Fetch integer limit from Plan.features JSON for a given feature_key.

    Example Plan.features structure:
      { "due_diligence": { "max_monthly": 10 } }
    """
    plan = db.get(m.Plan, plan_id)
    if not plan or not isinstance(getattr(plan, "features", None), dict):
        return None
    feat = plan.features.get(feature_key) or {}
    val = feat.get(limit_key)
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None
