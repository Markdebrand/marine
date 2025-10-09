from __future__ import annotations

from typing import Callable, Any

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models as m
from app.core.auth.session_manager import get_current_user
from app.core.services.usage_service import get_active_subscription, get_feature_limit_from_plan
from app.utils.adapters.cache_adapter import get_cache, set_cache, clear_cache
from app.config.settings import SESSION_CACHE_TTL


def require_admin(user: m.User = Depends(get_current_user)) -> m.User:
    """Allow admin role or superadmin flag."""
    if getattr(user, "is_superadmin", False) or getattr(user, "role", "user") == "admin":
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires admin role")


def require_due_create(
    user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Authorize creation of Due Diligence based on subscription/plan.

    Rules:
    - Superadmin/Admin: always allowed.
    - Others: must have an active subscription with feature 'due_diligence'
      and a defined limit (None means unlimited, any int >= 0 allowed).
    """
    if getattr(user, "is_superadmin", False) or getattr(user, "role", None) == "admin":
        return user
    try:
        sub = get_active_subscription(db, user.id)  # type: ignore[arg-type]
        _ = get_feature_limit_from_plan(db, sub, "due_diligence", "max_monthly")
    except Exception as exc:  # bubble up 402/403
        raise exc
    return user


# Placeholders for future fine-grained RBAC backed by tables or JWT claims
def require_role(role_slug: str) -> Callable[[Any], Any]:
    def _dep(user: m.User = Depends(get_current_user), db: Session = Depends(get_db)) -> m.User:
        if getattr(user, "is_superadmin", False):
            return user
        try:
            uid = int(getattr(user, 'id'))
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inválido")
        key = f"rbac:roles:{uid}"
        roles = get_cache(key)
        if not isinstance(roles, (set, list, tuple)):
            from app.db.models import Role, UserRole
            rows = (
                db.query(Role.slug)
                .join(UserRole, UserRole.role_id == Role.id)
                .filter(UserRole.user_id == uid)
                .all()
            )
            roles = set(slug for (slug,) in rows)
            # incluir coarse role si existe en user.role
            coarse = (getattr(user, 'role', None) or '').strip()
            if coarse:
                roles.add(coarse)
            set_cache(key, roles, max(30, SESSION_CACHE_TTL))
        if role_slug in set(roles):
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Requiere rol: {role_slug}")
    return _dep


def require_permission(perm_slug: str) -> Callable[[Any], Any]:
    def _dep(user: m.User = Depends(get_current_user), db: Session = Depends(get_db)) -> m.User:
        if getattr(user, "is_superadmin", False):
            return user
        try:
            uid = int(getattr(user, 'id'))
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inválido")
        key = f"rbac:perms:{uid}"
        perms = get_cache(key)
        if not isinstance(perms, (set, list, tuple)):
            from app.db.models import Permission, RolePermission, UserRole
            rows = (
                db.query(Permission.slug)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .join(UserRole, UserRole.role_id == RolePermission.role_id)
                .filter(UserRole.user_id == uid)
                .all()
            )
            perms = set(slug for (slug,) in rows)
            set_cache(key, perms, max(30, SESSION_CACHE_TTL))
        if perm_slug in set(perms):
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Falta permiso: {perm_slug}")
    return _dep


# --- Role gating helpers ---
def disallow_roles(*role_slugs: str) -> Callable[[Any], Any]:
    """Dependency that blocks users whose coarse role is in role_slugs (unless superadmin).

    Example: Depends(disallow_roles("cliente")) blocks clients from the route.
    """
    blocked = set(r.strip().lower() for r in role_slugs)

    def _dep(user: m.User = Depends(get_current_user)) -> m.User:
        if getattr(user, "is_superadmin", False):
            return user
        role = (getattr(user, "role", None) or "").lower()
        if role in blocked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rol no autorizado para este recurso")
        return user

    return _dep


def require_cliente(user: m.User = Depends(get_current_user)) -> m.User:
    if getattr(user, "is_superadmin", False):
        return user
    if (getattr(user, "role", None) or "").lower() == "cliente":
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requiere rol: cliente")
