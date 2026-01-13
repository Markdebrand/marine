"""
Guards for validating subscription status in protected endpoints.
"""
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.core.auth.session_manager import get_current_user
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def require_active_subscription(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Dependency that validates if the user has an active subscription.
    
    Allows access to:
    - Admin/Superadmin users
    - Users with active and non-expired subscription
    
    Blocks access to:
    - Users without subscription
    - Users with expired subscription
    
    Raises:
        HTTPException 403: If subscription is expired or missing
    
    Returns:
        models.User: The current user if allowed
    """
    # Admins always have access
    try:
        effective_role = getattr(user, 'role', 'user') or 'user'
        is_admin = effective_role == 'admin' or getattr(user, 'is_superadmin', False)
        
        if is_admin:
            return user
    except Exception:
        pass
    
    # Validate for regular users
    try:
        now = datetime.now(timezone.utc)
        
        # Search active subscription
        # We assume 'active' status is authoritative for access, but we double check dates
        subscription = (
            db.query(models.Subscription)
            .filter(
                models.Subscription.user_id == user.id,
                models.Subscription.status == 'active'
            )
            .order_by(models.Subscription.id.desc())
            .first()
        )
        
        # If no active subscription
        if subscription is None:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "subscription_required",
                    "message": "This feature requires an active subscription. Please renew your subscription to continue.",
                }
            )
        
        # Check if expired
        period_end = getattr(subscription, 'current_period_end', None)
        if period_end is not None:
            # Ensure timezone awareness
            if period_end.tzinfo is None:
                period_end = period_end.replace(tzinfo=timezone.utc)
            
            if period_end <= now:
                # Auto-expire
                try:
                    subscription.status = 'expired'  # type: ignore
                    db.commit()
                    logger.info(f"Subscription {subscription.id} for user {user.id} marked as expired")
                except Exception as e:
                    logger.error(f"Failed to update subscription status: {e}")
                    db.rollback()
                
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "subscription_expired",
                        "message": "Your subscription has expired. Please renew to access this feature.",
                    }
                )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating subscription for user {user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error validating subscription"
        )
