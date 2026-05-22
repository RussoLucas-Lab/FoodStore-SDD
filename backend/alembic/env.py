"""Alembic environment configuration.

Reads DATABASE_URL from the application Settings and imports all SQLModel
models so that autogenerate can detect the full schema.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel
from alembic import context

# ---------------------------------------------------------------------------
# Make the app package importable from here (backend/ is the working dir)
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all models so their metadata is registered with SQLModel
# Order matters: referenced tables must be imported before tables with FK to them
from app.modules.roles.model import Rol, UsuarioRol  # noqa: F401
from app.modules.usuarios.model import Usuario  # noqa: F401
from app.modules.auth.model import RefreshToken  # noqa: F401
from app.modules.categorias.model import Categoria  # noqa: F401
from app.modules.ingredientes.model import Ingrediente  # noqa: F401
from app.modules.productos.model import Producto, ProductoCategoria, ProductoIngrediente  # noqa: F401
from app.modules.direcciones.model import Direccion  # noqa: F401
from app.modules.pedidos.model import (  # noqa: F401
    EstadoPedido,
    Pedido,
    DetallePedido,
    HistorialEstadoPedido,
)
from app.modules.pagos.model import FormaPago, Pago  # noqa: F401

# ---------------------------------------------------------------------------
# Alembic Config object
# ---------------------------------------------------------------------------
config = context.config

# Override sqlalchemy.url with the value from Settings
try:
    from app.core.config import settings
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
except Exception:
    # Fall back to env var directly if settings are not available
    db_url = os.getenv("DATABASE_URL", "")
    if db_url:
        config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the SQLModel metadata (all registered tables)
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    Calls to context.execute() here emit the given string to the script output.
    """
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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection
    with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
