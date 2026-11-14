"""
Alembic env.py — reads DATABASE_URL from .env so you never hard-code
credentials here.
"""
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# ---------------------------------------------------------------------------
# 1. Load application models so Alembic sees all tables in Base.metadata
# ---------------------------------------------------------------------------
from app.database import Base  # noqa: F401 — registers Base
import app.models  # noqa: F401 — side-effect: registers all ORM classes

# ---------------------------------------------------------------------------
# 2. Pull DATABASE_URL from environment (loaded via app config)
# ---------------------------------------------------------------------------
from app.core.config import settings

config = context.config
# Escape '%' for configparser interpolation safety
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
