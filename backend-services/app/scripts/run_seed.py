"""
Script para ejecutar el seeding de planes y RBAC mínimo (admin/user).
Puedes ejecutarlo con:
    python -m app.scripts.run_seed
"""
from app.db.database import SessionLocal
from app.db.seed_db import ensure_seed_plans, ensure_seed_rbac

def main():
    db = SessionLocal()
    ensure_seed_plans(db)   # started/pro/enterprise/premium_enterprise con 3/5/8/10
    ensure_seed_rbac(db)    # roles (admin,user), permisos (due.create, due.view), asignaciones
    db.close()

if __name__ == "__main__":
    main()
