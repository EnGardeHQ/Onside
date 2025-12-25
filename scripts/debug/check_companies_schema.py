"""
Check the schema of the companies table in the database.

This script inspects the actual structure of the companies table
to understand the available columns for adding a JLL company record.
"""
import asyncio
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def check_companies_schema():
    """Check the schema of the companies table."""
    # Get database credentials from environment variables (with defaults)
    user = os.getenv('DB_USER', 'tobymorning')
    password = os.getenv('DB_PASSWORD', '')
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    database = os.getenv('DB_NAME', 'onside')
    
    # Construct database URL
    database_url = f'postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}'
    
    try:
        # Create engine with asyncpg driver
        logger.info(f"Connecting to database: {database} at {host}:{port}")
        engine = create_async_engine(
            database_url,
            echo=False  # Disable SQL query logging for cleaner output
        )
        
        # Create session factory
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        
        # Get column information for companies table
        logger.info("Inspecting companies table schema...")
        async with async_session() as session:
            result = await session.execute(
                text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'companies'
                    ORDER BY ordinal_position
                """)
            )
            columns = result.fetchall()
            
            logger.info("Companies table schema:")
            logger.info("%-25s %-20s %-10s" % ("Column Name", "Data Type", "Nullable"))
            logger.info("-" * 60)
            for col in columns:
                logger.info("%-25s %-20s %-10s" % (col.column_name, col.data_type, col.is_nullable))
            
            return columns
            
    except Exception as e:
        logger.error(f"❌ Error inspecting companies table: {str(e)}")
        return None

async def main():
    """Run the schema check script."""
    logger.info("=== Starting Companies Table Schema Check ===")
    columns = await check_companies_schema()
    
    if columns:
        logger.info("=== Companies Table Schema Check: SUCCESS ===")
        return 0
    else:
        logger.error("=== Companies Table Schema Check: FAILED ===")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
