from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db import models as m


def _period_month_bounds(dt: datetime) -> Tuple[datetime, datetime]:
    """Return UTC month start (inclusive) and next month start (exclusive).

    Example for 2025-09-15 -> (2025-09-01 00:00Z, 2025-10-01 00:00Z)
    """
    dt = dt.astimezone(timezone.utc)
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # compute first day of next month at 00:00
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def get_active_subscription(db: Session, user_id: int) -> m.Subscription:
    """Return the latest active subscription for a user or raise 402 if missing."""
    sub = (
        db.query(m.Subscription)
        .filter(m.Subscription.user_id == user_id, m.Subscription.status == "active")
        .order_by(m.Subscription.id.desc())
        .first()
    )
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Sin suscripción activa"
        )
    return sub


def get_feature_limit_from_plan(
    db: Session, sub: m.Subscription, feature_key: str, limit_key: str = "max_monthly"
) -> Optional[int]:
    """Get integer limit for a feature from the subscription's plan JSON features."""
    plan = db.query(m.Plan).filter(m.Plan.id == sub.plan_id).first()
    if not plan or not isinstance(plan.features, dict):
        return None
    feat = plan.features.get(feature_key) or {}
    limit = feat.get(limit_key)
    try:
        return int(limit) if limit is not None else None
    except (ValueError, TypeError):
        return None


def _get_or_create_usage_counter(db: Session, subscription_id: int, feature_key: str, now: datetime) -> m.UsageCounter:
    start, end = _period_month_bounds(now)
    row = (
        db.query(m.UsageCounter)
        .filter(
            m.UsageCounter.subscription_id == subscription_id,
            m.UsageCounter.feature_key == feature_key,
            m.UsageCounter.period_start == start,
        )
        .with_for_update(of=m.UsageCounter)  # best-effort lock to avoid races
        .first()
    )
    if row:
        return row
    row = m.UsageCounter(
        subscription_id=subscription_id,
        feature_key=feature_key,
        period_start=start,
        period_end=end,
        used=0,
    )
    db.add(row)
    db.flush()
    return row


def check_and_consume(db: Session, subscription_id: int, feature_key: str, consume_units: int = 1):
    """Validate monthly quota for a feature and consume units if available.

    Returns a dict with limit and remaining. If the plan has no limit, returns both as None.
    Raises HTTP 402 if quota would be exceeded.
    """
    sub = db.query(m.Subscription).filter(m.Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suscripción no encontrada")
    limit = get_feature_limit_from_plan(db, sub, feature_key, "max_monthly")
    if limit is None:
        return {"limit": None, "remaining": None}

    now = datetime.now(timezone.utc)
    counter = _get_or_create_usage_counter(db, int(sub.id), feature_key, now)  # type: ignore[arg-type]

    current_used = int(getattr(counter, "used", 0) or 0)
    lim = int(limit)
    new_used = current_used + int(consume_units)
    if new_used > lim:
        remaining = max(0, lim - current_used)
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Límite mensual alcanzado para {feature_key}. Remaining={remaining}, Limit={limit}",
        )

    counter.used = new_used  # type: ignore[assignment]
    db.add(counter)
    db.commit()
    db.refresh(counter)

    remaining = lim - new_used
    return {"limit": lim, "remaining": remaining}


def check_quota(db: Session, subscription_id: int, feature_key: str, units: int = 1):
    """Check if there is enough quota available without consuming.

    - Returns {limit, remaining} where remaining is current remaining BEFORE consumption.
    - If the plan has no limit, both values are None.
    - Raises HTTP 402 if not enough quota for the requested 'units'.
    """
    sub = db.query(m.Subscription).filter(m.Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suscripción no encontrada")
    limit = get_feature_limit_from_plan(db, sub, feature_key, "max_monthly")
    if limit is None:
        return {"limit": None, "remaining": None}

    now = datetime.now(timezone.utc)
    start, end = _period_month_bounds(now)
    counter = (
        db.query(m.UsageCounter)
        .filter(
            m.UsageCounter.subscription_id == subscription_id,
            m.UsageCounter.feature_key == feature_key,
            m.UsageCounter.period_start == start,
        )
        .first()
    )
    used = int(getattr(counter, "used", 0) or 0)
    lim = int(limit)
    remaining = max(0, lim - used)
    if units > remaining:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Límite mensual alcanzado para {feature_key}. Remaining={remaining}, Limit={lim}",
        )
    return {"limit": lim, "remaining": remaining}


def consume(db: Session, subscription_id: int, feature_key: str, units: int = 1):
    """Consume 'units' from quota if available (with locking), and return {limit, remaining}.

    This is intended to be called AFTER a successful operation, following a prior check_quota.
    It still re-validates under lock and may raise HTTP 402 in rare race conditions.
    """
    sub = db.query(m.Subscription).filter(m.Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suscripción no encontrada")
    limit = get_feature_limit_from_plan(db, sub, feature_key, "max_monthly")
    if limit is None:
        return {"limit": None, "remaining": None}

    now = datetime.now(timezone.utc)
    counter = _get_or_create_usage_counter(db, int(sub.id), feature_key, now)  # type: ignore[arg-type]
    current_used = int(getattr(counter, "used", 0) or 0)
    lim = int(limit)
    new_used = current_used + int(units)
    if new_used > lim:
        remaining = max(0, lim - current_used)
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Límite mensual alcanzado para {feature_key}. Remaining={remaining}, Limit={limit}",
        )
    counter.used = new_used  # type: ignore[assignment]
    db.add(counter)
    db.commit()
    db.refresh(counter)
    return {"limit": lim, "remaining": lim - new_used}


def refund(db: Session, subscription_id: int, feature_key: str, units: int = 1):
    """Refund previously consumed units in the current month period.

    - Does NOT create a counter if it doesn't exist (no-op in that case).
    - Never lets the counter go below 0.
    - Returns {limit, remaining}. If plan has no limit, both are None.
    """
    sub = db.query(m.Subscription).filter(m.Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suscripción no encontrada")
    limit = get_feature_limit_from_plan(db, sub, feature_key, "max_monthly")
    if limit is None:
        return {"limit": None, "remaining": None}

    now = datetime.now(timezone.utc)
    start, _ = _period_month_bounds(now)
    counter = (
        db.query(m.UsageCounter)
        .filter(
            m.UsageCounter.subscription_id == subscription_id,
            m.UsageCounter.feature_key == feature_key,
            m.UsageCounter.period_start == start,
        )
        .with_for_update(of=m.UsageCounter)
        .first()
    )
    lim = int(limit)
    if not counter:
        return {"limit": lim, "remaining": lim}
    current_used = int(getattr(counter, "used", 0) or 0)
    new_used = max(0, current_used - int(units))
    if new_used != current_used:
        counter.used = new_used  # type: ignore[assignment]
        db.add(counter)
        db.commit()
        db.refresh(counter)
    remaining = max(0, lim - new_used)
    return {"limit": lim, "remaining": remaining}


def get_usage_status(db: Session, subscription_id: int, feature_key: str):
    """Return used, limit, remaining for current month (UTC)."""
    sub = db.query(m.Subscription).filter(m.Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suscripción no encontrada")
    limit = get_feature_limit_from_plan(db, sub, feature_key, "max_monthly")
    if limit is None:
        return {"used": None, "limit": None, "remaining": None}

    now = datetime.now(timezone.utc)
    start, _ = _period_month_bounds(now)
    counter = (
        db.query(m.UsageCounter)
        .filter(
            m.UsageCounter.subscription_id == subscription_id,
            m.UsageCounter.feature_key == feature_key,
            m.UsageCounter.period_start == start,
        )
        .first()
    )
    used = int(getattr(counter, "used", 0) or 0)
    lim = int(limit)
    remaining = max(0, lim - used)
    return {"used": used, "limit": lim, "remaining": remaining}
