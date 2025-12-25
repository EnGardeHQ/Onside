"""Database module initialization.

This module initializes database connection following Semantic Seed coding standards
and our verified PostgreSQL schema requirements.

Features:
- Proper connection to verified PostgreSQL schema
- Support for actual (not mocked) database operations
- Following BDD/TDD methodology
"""
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import declarative_base, Session, sessionmaker

# Create SQLAlchemy base class with explicit schema for isolation
from sqlalchemy import MetaData, text
Base = declarative_base(metadata=MetaData(schema="onside"))

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:onside-dev-password@localhost:5432/onside")

# Create separate URLs for sync and async engines
# Sync engine (psycopg2) - supports options parameter
SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://") if DATABASE_URL.startswith("postgresql+asyncpg://") else DATABASE_URL

# Add search_path for sync engine (psycopg2 supports this)
if SYNC_DATABASE_URL and "options=" not in SYNC_DATABASE_URL:
    separator = "&" if "?" in SYNC_DATABASE_URL else "?"
    SYNC_DATABASE_URL = f"{SYNC_DATABASE_URL}{separator}options=-c%20search_path=onside,public"

# Create sync engine for synchronous operations
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True
)

# Create sync session factory
SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

# Async engine (asyncpg) - does NOT support options parameter
# Convert postgresql:// to postgresql+asyncpg:// for async driver
ASYNC_DATABASE_URL = DATABASE_URL
if ASYNC_DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# For asyncpg, we use connect_args with server_settings instead of URL options
# This sets the search_path at the connection level
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    future=True,
    connect_args={
        "server_settings": {
            "search_path": "onside,public"
        }
    }
)

# Create async session factory following BDD/TDD methodology with real database connections
SessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

def get_db_sync() -> Generator[Session, None, None]:
    """Dependency for getting synchronous database sessions.

    Use this for synchronous endpoints and operations.
    """
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Alias for backwards compatibility - defaults to sync version
get_db = get_db_sync

async def get_db_async():
    """Dependency for getting database sessions asynchronously.

    Following proper BDD/TDD methodology with real database connections.
    Use this for async endpoints that need async database operations.
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def init_db():
    """Initialize the database asynchronously.

    Following our verified schema configuration:
    - Database name: onside
    - Owner: tobymorning
    - Connection: localhost:5432
    - Authentication: User-based (tobymorning)
    """
    # Use bind.run_sync for async engine
    async with engine.begin() as conn:
        # Ensure schema exists before creating tables
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS onside"))
        await conn.run_sync(Base.metadata.create_all)

__all__ = ['Base', 'SessionLocal', 'SyncSessionLocal', 'engine', 'sync_engine', 'get_db', 'get_db_sync', 'get_db_async', 'init_db']
