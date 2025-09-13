from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import our models and database configuration
import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')

from src.impact_bridge.database.models import Base
from src.impact_bridge.database.engine import get_database_url
from src.impact_bridge.config import DatabaseConfig

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_config() -> DatabaseConfig:
    """Get database configuration for migrations."""
    # Use default database config or load from environment
    db_config = DatabaseConfig()
    
    # Allow override from environment variables
    if os.getenv("LEADVILLE_DB_DIR"):
        db_config.dir = os.getenv("LEADVILLE_DB_DIR")
    if os.getenv("LEADVILLE_DB_FILE"):
        db_config.file = os.getenv("LEADVILLE_DB_FILE")
    
    return db_config


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    db_config = get_database_config()
    url = get_database_url(db_config)
    
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

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    db_config = get_database_config()
    
    # Override the sqlalchemy.url in the configuration
    config_section = config.get_section(config.config_ini_section, {})
    config_section['sqlalchemy.url'] = get_database_url(db_config)
    
    connectable = engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
