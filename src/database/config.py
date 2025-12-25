"""Database configuration module.

This module contains the database configuration for the application.
It follows Semantic Seed Venture Studio Coding Standards V2.0.
"""
import os
from typing import Generator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create base class for SQLAlchemy models
Base = declarative_base()

# Use verified PostgreSQL configuration from project memory
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://tobymorning@localhost:5432/onside")

# Create async engine with verified PostgreSQL configuration
# Following OnSide project requirements:
# - Database: onside
# - Owner: tobymorning
# - Connection: localhost:5432
# - Authentication: User-based (tobymorning)
engine = create_async_engine(
    DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'),
    echo=True,  # Enable SQL query logging
    future=True,
    pool_size=5,  # Reduced pool size for development
    max_overflow=10,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=1800  # Recycle connections every 30 minutes
)

# Create async session factory
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency to get async database session
async def get_db() -> AsyncSession:
    """Dependency for getting async database session"""
    async with SessionLocal() as session:
        yield session

# Initialize database
async def init_db():
    """Initialize the database with all tables"""
    # Import all models here to ensure they're registered with Base
    # These imports are done here to avoid circular imports
    from src.models.content import Content, ContentEngagementHistory, TrendAnalysis
    from src.auth.models import User
    from src.models.market import (
        MarketTag,
        MarketSegment,
        Competitor,
        CompetitorContent,
        CompetitorMetrics,
        competitor_tags,
    )
    from src.models.ai import AIInsight
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Cleanup database
async def cleanup_db():
    """Clean up database resources"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

# Database initialization will be handled by FastAPI startup event
