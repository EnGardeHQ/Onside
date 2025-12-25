#!/usr/bin/env python3
"""
Database reset and migration script for OnSide application.

This script resets the database and applies all migrations.
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to Python path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.engine import Engine

from src.config.config import Config
from src.database import Base, engine as async_db_engine, SessionLocal

# Create a synchronous engine for migrations
sync_engine = create_engine(
    "postgresql://tobymorning@localhost:5432/onside",
    pool_pre_ping=True,
    pool_recycle=3600,
)

settings = Config()

async def drop_all_tables():
    """Drop all tables in the database."""
    print("Dropping all tables...")
    
    # Use synchronous connection for dropping tables
    with sync_engine.connect() as conn:
        # Disable foreign key constraints
        conn.execute(text("SET session_replication_role = 'replica';"))
        
        # Get all table names
        result = conn.execute(
            text(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                """
            )
        )
        tables = [row[0] for row in result]
        
        # Drop all tables
        for table in tables:
            if table != 'alembic_version':
                print(f"Dropping table: {table}")
                conn.execute(text(f'DROP TABLE IF EXISTS \"{table}\" CASCADE'))
        
        # Re-enable foreign key constraints
        conn.execute(text("SET session_replication_role = 'origin';"))
        conn.commit()
    
    print("All tables dropped successfully.")

def reset_alembic():
    """Reset the alembic version table."""
    print("Resetting alembic version table...")
    
    # Remove the alembic_version table if it exists
    with sync_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.commit()
    
    print("Alembic version table reset.")

async def run_migrations():
    """Run database migrations."""
    print("Running migrations...")
    
    # Run migrations using alembic
    from alembic.config import Config
    from alembic import command
    
    # Get the path to the alembic.ini file
    alembic_cfg = Config("alembic.ini")
    
    # Set the SQLAlchemy URL for migrations
    alembic_cfg.set_main_option('sqlalchemy.url', str(sync_engine.url))
    
    # Run migrations
    command.upgrade(alembic_cfg, "head")
    
    print("Migrations completed successfully.")

async def main():
    """Main function to reset the database and run migrations."""
    try:
        # Drop all tables
        await drop_all_tables()
        
        # Reset alembic version table
        reset_alembic()
        
        # Run migrations
        await run_migrations()
        
        print("\nDatabase reset and migrations completed successfully!")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
