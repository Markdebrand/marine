from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models as m
from app.core.auth.session_manager import get_current_user
from app.core.services.usage_service import get_active_subscription, get_feature_limit_from_plan
from app.utils.adapters.cache_adapter import get_cache, set_cache
from app.config.settings import SESSION_CACHE_TTL

def require_superadmin(user: m.User = Depends(get_current_user)):
    if not getattr(user, "is_superadmin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo superadmin")
    return user

def require_role(role_slug: str):
    def _dep(user: m.User = Depends(get_current_user), db: Session = Depends(get_db)):
        if getattr(user, "is_superadmin", False):
            return user
        uid = int(getattr(user, 'id'))
        key = f"rbac:roles:{uid}"
        roles = get_cache(key)
        if not isinstance(roles, (set, list, tuple)):
            rows = (
                db.query(m.Role.slug)
                .join(m.UserRole, m.UserRole.role_id == m.Role.id)
                .filter(m.UserRole.user_id == uid)
                .all()
            )
            roles = set(slug for (slug,) in rows)
            coarse = (getattr(user, 'role', None) or '').strip()
            if coarse:
                roles.add(coarse)
            set_cache(key, roles, max(30, SESSION_CACHE_TTL))
        if role_slug in set(roles):
            return user
        raise HTTPException(status_code=403, detail=f"Requiere rol: {role_slug}")
    return _dep

def require_permission(perm_slug: str):
    def _dep(user: m.User = Depends(get_current_user), db: Session = Depends(get_db)):
        if getattr(user, "is_superadmin", False):
            return user
        uid = int(getattr(user, 'id'))
        key = f"rbac:perms:{uid}"
        perms = get_cache(key)
        if not isinstance(perms, (set, list, tuple)):
            rows = (
                db.query(m.Permission.slug)
                .join(m.RolePermission, m.RolePermission.permission_id == m.Permission.id)
                .join(m.UserRole, m.UserRole.role_id == m.RolePermission.role_id)
                .filter(m.UserRole.user_id == uid)
                .all()
            )
            perms = set(slug for (slug,) in rows)
            set_cache(key, perms, max(30, SESSION_CACHE_TTL))
        if perm_slug in set(perms):
            return user
        raise HTTPException(status_code=403, detail=f"Falta permiso: {perm_slug}")
    return _dep


# --- Due Diligence specific guard ---
def require_due_create(user: m.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Authorize Due Diligence creation via subscription plan limits (not roles)."""
    if getattr(user, "is_superadmin", False) or getattr(user, "role", None) == "admin":
        return user
    try:
        sub = get_active_subscription(db, user.id)  # type: ignore
        _ = get_feature_limit_from_plan(db, sub, "due_diligence", "max_monthly")
    except Exception as exc:
        raise exc
    return user
