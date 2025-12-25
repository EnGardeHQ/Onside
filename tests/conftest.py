"""Test configuration and fixtures.

This module provides pytest fixtures for testing the application, including
database session management and authentication.
"""
import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)

from src.models.user import User, UserRole
from src.database import Base
from src.main import create_app
from src.auth.security import create_access_token

# Using real PostgreSQL database for tests following Semantic Seed standards
# This ensures tests run against the actual schema
import os

# Get database connection info from environment or use default test values
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "onside_test")
DB_USER = os.environ.get("DB_USER", "tobymorning")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

# Real PostgreSQL connection URL
TEST_DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine using real PostgreSQL.
    
    Following Semantic Seed standards, we connect to the actual database
    to ensure tests run against the real schema structure.
    """
    # Create engine without connect_args specific to SQLite
    engine = create_async_engine(
        TEST_DB_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30
    )
    
    # Create test schema and initialize
    async with engine.begin() as conn:
        # Create a schema specifically for this test run to avoid interfering with dev data
        test_schema = f"test_schema_{os.getpid()}"
        await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {test_schema}")
        await conn.execute(f"SET search_path TO {test_schema}")
        
        # Create all tables in the test schema
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up after tests
    async with engine.begin() as conn:
        await conn.execute(f"DROP SCHEMA IF EXISTS {test_schema} CASCADE")
    
    await engine.dispose()

@pytest_asyncio.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with proper transaction isolation.
    
    Following Semantic Seed BDD/TDD standards, each test runs in its own
    transaction that is rolled back after the test completes.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()
    
    # Set the test schema for this connection
    test_schema = f"test_schema_{os.getpid()}"
    await connection.execute(f"SET search_path TO {test_schema}")
    
    # Create session bound to this connection
    async_session = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        # Begin a nested transaction
        await session.begin_nested()
        
        # Yield the session for test use
        yield session
        
        # Rollback the nested transaction after test
        await session.rollback()
    
    # Rollback the outer transaction
    await transaction.rollback()
    await connection.close()

@pytest_asyncio.fixture
async def test_app(test_db) -> FastAPI:
    """Create a test FastAPI application."""
    app = create_app()
    app.state.db = test_db
    return app

@pytest_asyncio.fixture
async def test_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client for making HTTP requests."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user."""
    from src.auth.password_utils import generate_password_hash
    
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=generate_password_hash("testpassword"),
        name="Test User",
        role=UserRole.USER,
        is_active=True,
        is_admin=False
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_token(test_user: User) -> str:
    """Create a test JWT token."""
    return create_access_token(test_user.id)
