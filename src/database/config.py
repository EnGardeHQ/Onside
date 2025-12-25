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

# Import shared database resources
from src.database import Base, engine, SessionLocal

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
    from src.models.user import User
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
