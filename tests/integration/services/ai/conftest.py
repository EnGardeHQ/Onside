"""Test fixtures for LLM integration tests.

This module provides test fixtures for the OnSide LLM services integration tests.
"""
import sys
import os
import pytest
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

# Import the database Base after setting up the path
from src.config.database import Base

# Test database fixture
@pytest.fixture
async def db():
    """Create a test database session."""
    # For testing, we're using SQLite in-memory database
    engine = create_async_engine('sqlite+aiosqlite:///:memory:', echo=True)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session factory
    async_session_factory = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    
    # Provide session for test
    async with async_session_factory() as session:
        yield session
    
    # Clean up after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

# Set up environment variables for testing
@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Set up environment variables for testing."""
    # Ensure we have environment variables set for APIs
    os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', 'sk-dummy')
    os.environ['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY', 'sk-ant-dummy')
    
    # Return for use in tests
    return {
        "openai_key": os.environ.get('OPENAI_API_KEY'),
        "anthropic_key": os.environ.get('ANTHROPIC_API_KEY')
    }
