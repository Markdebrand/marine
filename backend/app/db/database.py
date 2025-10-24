import logging

from sqlalchemy import create_engine, event, text, MetaData
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config.settings import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
    POSTGRES_POOL_SIZE, POSTGRES_MAX_OVERFLOW
)

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_N_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

# Normaliza password por si viene entre comillas en .env
_PASSWORD = (POSTGRES_PASSWORD or "").strip().strip('\'\"')

# Usamos psycopg (psycopg[binary]) como driver para Postgres
_url = URL.create(
    drivername="postgresql+psycopg",
    username=POSTGRES_USER,
    password=_PASSWORD,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    database=POSTGRES_DB,
)

engine = create_engine(
    _url,
    pool_size=POSTGRES_POOL_SIZE,
    max_overflow=POSTGRES_MAX_OVERFLOW,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Simple init helper
def init_db():
    from app.db import models  # noqa: F401 ensure models imported
    # Ajustes al conectar: asegurar zona horaria UTC si la sesión lo permite
    @event.listens_for(engine, "connect")
    def _set_time_zone(dbapi_connection, connection_record):  # noqa: ANN001
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("SET TIME ZONE 'UTC'")
            cursor.close()
        except Exception:
            # No bloquear si falla el SET (p.ej., permisos limitados)
            pass

    # Intenta habilitar PostGIS para soportar columnas geometry
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            conn.commit()
    except Exception as exc:  # pragma: no cover - depende de privilegios/extensión
        logging.getLogger(__name__).warning("Postgres PostGIS extension not available: %s", exc)

    # Crea tablas si no existen
    Base.metadata.create_all(bind=engine)

    # Prueba de conectividad simple
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:  # pragma: no cover
        logging.getLogger(__name__).error(f"Postgres connectivity check failed: {e}")

    # Opcional: semilla de planes/permiso si decides mantenerla en arranque
    try:
        from app.db.seed_db import ensure_seed_plans, ensure_seed_permissions, ensure_seed_roles  # type: ignore
        with SessionLocal() as s:
            ensure_seed_plans(s)
            ensure_seed_permissions(s)
            ensure_seed_roles(s)
    except Exception:
        pass
