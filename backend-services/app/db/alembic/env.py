from __future__ import annotations

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add current project to sys.path and import Base metadata
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[3]  # backend/
sys.path.append(str(BASE_DIR))

from pathlib import Path

from app.db.database import Base, _url  # type: ignore  # noqa: E402
from app.db import models  # noqa: F401  # ensure models are imported

# Decide connection URL: prefer explicit ALEMBIC_DATABASE_URL if provided; otherwise use app's engine URL
_alembic_url = os.getenv("ALEMBIC_DATABASE_URL")
if _alembic_url:
    # Escape '%' for ConfigParser interpolation rules
    config.set_main_option("sqlalchemy.url", _alembic_url.replace('%', '%%'))
else:
    config.set_main_option("sqlalchemy.url", str(_url).replace('%', '%%'))

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section), # type: ignore
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
