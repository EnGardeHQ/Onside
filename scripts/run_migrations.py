"""Run database migrations.

This script applies all pending database migrations.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from alembic import command
from alembic.config import Config
from src.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations() -> None:
    """Run database migrations.
    
    This function applies all pending database migrations.
    """
    try:
        # Get the directory containing this script
        script_dir = Path(__file__).resolve().parent
        
        # Set the path to the alembic.ini file
        alembic_cfg = Config(str(script_dir.parent / "alembic.ini"))
        
        # Set the path to the migrations directory
        alembic_cfg.set_main_option(
            "script_location", 
            str(script_dir.parent / "migrations")
        )
        
        # Set the database URL
        alembic_cfg.set_main_option("sqlalchemy.url", str(settings.database_url))
        
        logger.info("Running database migrations...")
        
        # Run the migrations
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Database migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
