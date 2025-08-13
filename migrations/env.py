from logging.config import fileConfig
import os
from dotenv import load_dotenv

from sqlalchemy import pool
from sqlalchemy.engine import Connection, create_engine

from alembic import context

# Load environment variables
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from database.models import Base
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def get_url():
    """Get database URL from environment variables"""
    # For Supabase, we'll use the connection string format
    # You can also use individual components if needed
    
    # Option 1: Direct connection string (if you have it)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Option 2: Build from Supabase components
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        # Extract host from Supabase URL and build PostgreSQL connection
        # Supabase URL format: https://project-id.supabase.co
        host = supabase_url.replace("https://", "").replace("http://", "").replace(".supabase.co", "")
        
        # For Supabase, the database is typically 'postgres'
        # You might need to adjust these based on your specific setup
        user = "postgres"  # or your specific user
        password = supabase_key  # or your specific password
        database = "postgres"  # or your specific database name
        
        return f"postgresql://{user}:{password}@{host}.supabase.co:5432/{database}"
    
    # Fallback to local development
    return "postgresql://postgres:password@localhost:5432/tegus_dev"

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = create_engine(
        configuration["sqlalchemy.url"],
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


# Run migrations based on context
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
