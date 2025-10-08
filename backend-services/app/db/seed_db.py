from __future__ import annotations

from typing import Any, Dict, Iterable
from sqlalchemy.orm import Session
from app.db import models as m
from app.auth.security_passwords import hash_password

PLANS: Dict[str, Dict[str, Any]] = {
    "started": {
        "name": "Started",
        "support": "BASIC",
        "features": {
            "dashboards": {"max": 3},
            "due_diligence": {"max_monthly": 3},
            "plaid": {"monthly_included": 0, "allow_optional": True},
            "multiregional": False,
        },
    },
    "pro": {
        "name": "Pro",
        "support": "STANDARD",
        "features": {
            "dashboards": {"max": 5},
            "due_diligence": {"max_monthly": 5},
            "plaid": {"monthly_included": 5, "allow_optional": True},
            "multiregional": True,
        },
    },
    "enterprise": {
        "name": "Enterprise",
        "support": "PRIORITY",
        "features": {
            "dashboards": {"max": 8},
            "due_diligence": {"max_monthly": 8},
            "plaid": {"monthly_included": 15, "allow_optional": True},
            "multiregional": True,
        },
    },
    "premium_enterprise": {
        "name": "Premium Enterprise",
        "support": "DEDICATED",
        "features": {
            "dashboards": {"max": 10},
            "due_diligence": {"max_monthly": 10},
            "plaid": {"monthly_included": 30, "allow_optional": True},
            "multiregional": True,
        },
    },
}


def ensure_seed_plans(db: Session) -> None:
    """Upsert del catálogo de planes."""
    existing = {str(p.code): p for p in db.query(m.Plan).all()}
    for code, cfg in PLANS.items():
        row = existing.get(code)
        if row is not None:
            row.name = cfg.get("name", row.name)
            row.support = cfg.get("support", row.support)
            row.features = cfg.get("features", row.features)
        else:
            db.add(m.Plan(code=code, name=cfg.get("name", code.title()), support=cfg.get("support", "BASIC"), features=cfg.get("features", {})))
    db.commit()


def ensure_admin_user(db: Session) -> None:
    """Crea un usuario administrador si no existe.

    Credenciales por defecto: admin@example.com / Admin123! (cambiar en producción)
    """
    admin_email = "admin@example.com"
    user = db.query(m.User).filter(m.User.email == admin_email).first()
    if not user:
        user = m.User(email=admin_email, password_hash=hash_password("Admin123!"), is_superadmin=True, role="admin")
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Asegurar que esté marcado como superadmin aunque ya exista
        changed = False
        if getattr(user, "is_superadmin", False) is not True:
            user.is_superadmin = True  # type: ignore[attr-defined]
            changed = True
        if getattr(user, "role", None) != "admin":
            user.role = "admin"  # type: ignore[attr-defined]
            changed = True
        if changed:
            db.add(user)
            db.commit()
    # No crear suscripción para el superadmin; usuarios normales partirán con "started" en el flujo de auth


def ensure_seed_permissions(db: Session) -> None:
    """Crea permisos básicos (idempotente)."""
    wanted = [
        {"slug": "due.create", "name": "Crear Due Diligence"},
        {"slug": "due.view", "name": "Ver Due Diligence"},
    ]
    existing = {str(p.slug): p for p in db.query(m.Permission).all()}
    for w in wanted:
        slug = str(w["slug"])  # normalize
        row = existing.get(slug)
        if row is not None:
            if str(getattr(row, "name", "")) != str(w["name"]):
                row.name = w["name"]  # type: ignore[assignment]
                db.add(row)
        else:
            db.add(m.Permission(slug=slug, name=w["name"]))
    db.commit()


def ensure_seed_roles(db: Session) -> None:
    """Crea roles básicos (admin, user)."""
    wanted = [
        {"slug": "admin", "name": "Administrador"},
        {"slug": "user", "name": "Usuario"},
        {"slug": "cliente", "name": "Cliente"},
    ]
    existing = {str(r.slug): r for r in db.query(m.Role).all()}
    for w in wanted:
        slug = str(w["slug"])  # normalize
        row = existing.get(slug)
        if row is not None:
            if str(getattr(row, "name", "")) != str(w["name"]):
                row.name = w["name"]  # type: ignore[assignment]
                db.add(row)
        else:
            db.add(m.Role(slug=slug, name=w["name"]))
    db.commit()

    # Asignar rol admin al superadmin si existe
    admin_role = db.query(m.Role).filter(m.Role.slug == "admin").first()
    superadmin = db.query(m.User).filter(m.User.is_superadmin.is_(True)).first()
    if admin_role and superadmin:
        has = (
            db.query(m.UserRole)
            .filter(m.UserRole.user_id == superadmin.id, m.UserRole.role_id == admin_role.id)
            .first()
        )
        if not has:
            db.add(m.UserRole(user_id=superadmin.id, role_id=admin_role.id))
            db.commit()


def _ensure_role_permissions(db: Session, role: m.Role, perm_slugs: Iterable[str]) -> None:
    perms = db.query(m.Permission).filter(m.Permission.slug.in_(list(perm_slugs))).all()
    existing = db.query(m.RolePermission).filter(m.RolePermission.role_id == role.id).all()
    existing_perm_ids = {rp.permission_id for rp in existing}
    for p in perms:
        if p.id not in existing_perm_ids:
            db.add(m.RolePermission(role_id=role.id, permission_id=p.id))
    db.commit()


def ensure_seed_rbac(db: Session) -> None:
    """Crea roles y permisos básicos y asignaciones.

    - admin: todos los permisos
    - user: due.* (create, view)
    - Si existe User.is_superadmin=True, se asegura rol admin.
    """
    ensure_seed_permissions(db)
    ensure_seed_roles(db)

    admin_role = db.query(m.Role).filter(m.Role.slug == "admin").first()
    user_role = db.query(m.Role).filter(m.Role.slug == "user").first()
    if not admin_role or not user_role:
        return

    # admin -> todos los permisos
    all_perms = [str(p.slug) for p in db.query(m.Permission).all()]
    _ensure_role_permissions(db, admin_role, all_perms)

    # user -> due.create, due.view
    _ensure_role_permissions(db, user_role, ["due.create", "due.view"])
