import typer
from app.db.database import SessionLocal, init_db
from app.db import models as m
from app.auth.security_passwords import hash_password

cli = typer.Typer(help="Operaciones administrativas")


@cli.command("create-superuser")
def create_superuser(
    email: str = typer.Option(..., "--email", help="Email del superadmin"),
    password: str = typer.Option(
        ..., "--password", help="Password del superadmin", prompt=True, hide_input=True
    ),
):
    """Crea un superadmin global (is_superadmin=True)."""
    init_db()
    with SessionLocal() as db:
        if db.query(m.User).filter(m.User.email == email.lower()).first():
            typer.echo("Ya existe un usuario con ese email")
            raise typer.Exit(1)
        u = m.User(
            email=email.lower(),
            password_hash=hash_password(password),
            is_superadmin=True,
        )
        db.add(u)
        db.commit()
        typer.echo(f"Superadmin creado: {u.email}")


@cli.command("seed-plans")
def seed_plans():
    """Semilla/actualiza catálogo de planes (idempotente)."""
    init_db()
    from app.db.seed_db import ensure_seed_plans  # noqa: WPS433
    with SessionLocal() as db:
        ensure_seed_plans(db)
    typer.echo("Planes asegurados")


@cli.command("seed-permissions")
def seed_permissions():
    """Semilla/actualiza permisos base (idempotente)."""
    init_db()
    from app.db.seed_db import ensure_seed_permissions  # noqa: WPS433
    with SessionLocal() as db:
        ensure_seed_permissions(db)
    typer.echo("Permisos asegurados")


@cli.command("seed-all")
def seed_all():
    """Asegura planes, permisos y RBAC base."""
    init_db()
    from app.db.seed_db import ensure_seed_plans, ensure_seed_permissions, ensure_seed_rbac  # noqa: WPS433
    with SessionLocal() as db:
        ensure_seed_plans(db)
        ensure_seed_permissions(db)
        ensure_seed_rbac(db)
    typer.echo("Planes, permisos y RBAC asegurados")


@cli.command("seed-rbac")
def seed_rbac():
    """Asegura RBAC (roles, permisos y asignaciones)."""
    init_db()
    from app.db.seed_db import ensure_seed_rbac  # noqa: WPS433
    with SessionLocal() as db:
        ensure_seed_rbac(db)
    typer.echo("RBAC asegurado")


if __name__ == "__main__":
    cli()
