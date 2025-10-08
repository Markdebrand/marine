from sqlalchemy import create_engine, event, text, MetaData
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config.settings import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_DB, MYSQL_USER, MYSQL_PASSWORD,
    MYSQL_POOL_SIZE, MYSQL_MAX_OVERFLOW
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
_PASSWORD = (MYSQL_PASSWORD or "").strip().strip("'\"")

_url = URL.create(
    drivername="mysql+pymysql",
    username=MYSQL_USER,
    password=_PASSWORD,  # URL.create se encarga de escapar caracteres especiales (#, !, @, etc.)
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    database=MYSQL_DB,
    query={"charset": "utf8mb4"},
)

engine = create_engine(
    _url,
    pool_size=MYSQL_POOL_SIZE,
    max_overflow=MYSQL_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=1800,  # evita MySQL server has gone away en conexiones ociosas
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
    # Ajustes de sesión MySQL al conectar (zona horaria UTC)
    @event.listens_for(engine, "connect")
    def _set_sql_mode_time_zone(dbapi_connection, connection_record):  # noqa: ANN001
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("SET time_zone = '+00:00'")
            cursor.close()
        except Exception:
            # No bloquear si falla el SET (p.ej., permisos limitados)
            pass

    # Crea tablas si no existen
    Base.metadata.create_all(bind=engine)

    # Prueba de conectividad simple
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:  # pragma: no cover
        import logging
        logging.getLogger(__name__).error(f"MySQL connectivity check failed: {e}")

    # Opcional: semilla de planes/permiso si decides mantenerla en arranque
    try:
        from app.db.seed_db import ensure_seed_plans, ensure_seed_permissions, ensure_seed_roles  # type: ignore
        with SessionLocal() as s:
            ensure_seed_plans(s)
            ensure_seed_permissions(s)
            ensure_seed_roles(s)
    except Exception:
        pass
