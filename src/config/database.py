"""Database configuration module.

This module handles database connection configuration following our verified
PostgreSQL schema and Semantic Seed coding standards.

Features:
- Async SQLAlchemy configuration
- Proper event loop handling
- Comprehensive error handling
- Detailed logging
"""
import logging
import os
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

# Import database settings
from .settings import DATABASE

# SQLAlchemy async engine
engine: Optional[AsyncEngine] = None
async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None

def get_database_url() -> str:
    """Get the database URL from environment.
    
    Following our verified schema configuration, this function:
    1. Uses the DATABASE settings
    2. Ensures proper asyncpg driver usage for PostgreSQL
    3. Follows OnSide's verified database schema (onside, tobymorning, localhost)
    """
    # Extract database settings
    user = DATABASE.get("USER", "tobymorning")
    password = DATABASE.get("PASSWORD", "")
    host = DATABASE.get("HOST", "localhost")
    port = DATABASE.get("PORT", "5432")
    name = DATABASE.get("NAME", "onside")
    
    # Check for database URL in settings
    if database_url := DATABASE.get("URL"):
        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return database_url
    
    # Construct URL from components
    if password:
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
    return f"postgresql+asyncpg://{user}@{host}:{port}/{name}"

async def init_db() -> None:
    """Initialize the database connection.
    
    Following Sprint 4 requirements and Semantic Seed standards:
    1. Proper async event loop handling
    2. Connection pooling configuration
    3. Comprehensive error handling
    4. Detailed logging
    """
    global engine, async_session_factory
    
    try:
        import asyncio
        
        # Ensure we're running in the correct event loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Create async engine with proper connection arguments
        engine = create_async_engine(
            get_database_url(),
            pool_size=DATABASE.get("POOL_SIZE", 20),            # Use settings
            max_overflow=DATABASE.get("MAX_OVERFLOW", 10),      # Use settings
            pool_timeout=DATABASE.get("POOL_TIMEOUT", 30),      # Use settings
            echo=DATABASE.get("ECHO", True),                    # Use settings
            # Following our verified schema configuration
            connect_args={
                "server_settings": {
                    "application_name": "onside_app",
                    "client_encoding": "utf8",
                    "timezone": "UTC"
                },
                "command_timeout": 60  # 60 second timeout
            }
        )
        
        # Create async session factory
        async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        
        # Test the connection
        from sqlalchemy.sql import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        logger.info("✅ Database connection initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        if engine:
            await engine.dispose()
        raise

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session.
    
    Yields:
        AsyncSession: Database session
    """
    if async_session_factory is None:
        await init_db()
        
    if async_session_factory is None:
        raise RuntimeError("Database session factory not initialized")
        
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"❌ Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()

async def close_db() -> None:
    """Close database connections."""
    global engine
    
    if engine:
        try:
            await engine.dispose()
            logger.info("✅ Database connections closed")
        except Exception as e:
            logger.error(f"❌ Error closing database connections: {str(e)}")
            raise
