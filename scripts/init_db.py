"""Initialize the database with the required schema.

This script creates all the necessary tables in the PostgreSQL database
based on the SQLAlchemy models.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.database import Base, engine, init_db
from src.models import *  # Import all models to ensure they're registered with SQLAlchemy

async def create_tables():
    """Create all tables in the database."""
    print("Initializing database...")
    
    # Create all tables
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database initialization complete!")

if __name__ == "__main__":
    asyncio.run(create_tables())
