"""Script to initialize the test database with required schema.

This script creates all necessary tables in the test database.
"""
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set the test database URL before importing database modules
os.environ["DATABASE_NAME"] = "onside_test"
os.environ["DB_NAME"] = "onside_test"

from src.database import init_db, engine, Base
from src.config import DATABASE

async def main():
    """Initialize the test database."""
    print("Initializing test database...")
    
    # Import all models to ensure they're registered with Base
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
    from src.models.domain import Domain
    
    # Print database URL for debugging
    print(f"Using database URL: {os.environ.get('DATABASE_URL')}")
    print(f"Using database name: {os.environ.get('DB_NAME')}")
    
    # Create all tables
    async with engine.begin() as conn:
        print("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    # Verify tables were created
    from sqlalchemy import text
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = result.fetchall()
        print("\nTables in database:")
        for table in tables:
            print(f"- {table[0]}")
    
    print("\nTest database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(main())
