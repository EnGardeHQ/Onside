"""
Database connection test for the OnSide project.

This script verifies:
1. Connection to the actual PostgreSQL database
2. Schema and table existence
3. Basic query functionality

Following Semantic Seed BDD/TDD standards, this ensures our implementation
works with the real database rather than mocks.
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

# Database tables to check
REQUIRED_TABLES = [
    'companies',
    'competitors',
    'domains',
    'links',
    'link_snapshots',
    'reports',
    'ai_insights',
    'competitor_content',
    'competitor_metrics'
]

async def test_database_connection():
    """Test connection to the actual PostgreSQL database."""
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
            echo=True,  # SQL query logging
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800
        )
        
        # Create session factory
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        
        # Test connection
        logger.info("Testing database connection...")
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: None)
            logger.info('✅ Successfully connected to database')
        
        # Verify tables exist
        logger.info("Checking database schema...")
        missing_tables = []
        async with async_session() as session:
            for table in REQUIRED_TABLES:
                result = await session.execute(
                    text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
                )
                exists = result.scalar()
                if exists:
                    logger.info(f"✅ Table '{table}' exists")
                else:
                    logger.error(f"❌ Table '{table}' does not exist")
                    missing_tables.append(table)
        
        # Check for JLL company record
        logger.info("Checking for JLL company record...")
        async with async_session() as session:
            result = await session.execute(
                text("SELECT id, name FROM companies WHERE name ILIKE '%JLL%' OR name ILIKE '%Jones Lang LaSalle%' LIMIT 1")
            )
            jll_company = result.fetchone()
            if jll_company:
                logger.info(f"✅ Found JLL company: {jll_company.name} (ID: {jll_company.id})")
            else:
                logger.warning("⚠️ No JLL company record found in the database")
        
        # Summary
        if missing_tables:
            logger.error(f"❌ Database schema verification failed. Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            logger.info("✅ All required tables exist in the database")
            return True
            
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        return False

async def main():
    """Run the database connection test."""
    logger.info("=== Starting Database Connection Test ===")
    success = await test_database_connection()
    
    if success:
        logger.info("=== Database Connection Test: PASSED ===")
        logger.info("The database is correctly configured for the JLL analysis workflow")
        return 0
    else:
        logger.error("=== Database Connection Test: FAILED ===")
        logger.error("Please fix the database configuration before proceeding with JLL analysis")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
