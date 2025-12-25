"""
Check if the users table exists in the database.
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

async def check_users_table():
    """Check if the users table exists."""
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
        
        # Check if users table exists
        logger.info("Checking if users table exists...")
        async with async_session() as session:
            result = await session.execute(
                text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')")
            )
            users_exists = result.scalar()
            logger.info(f"Users table exists: {users_exists}")
            
            if users_exists:
                # Check if there are any records in the users table
                users_result = await session.execute(text("SELECT COUNT(*) FROM users"))
                user_count = users_result.scalar()
                logger.info(f"Number of user records: {user_count}")
            
            return users_exists
            
    except Exception as e:
        logger.error(f"❌ Error checking users table: {str(e)}")
        return False

async def main():
    """Run the users table check."""
    logger.info("=== Checking Users Table ===")
    exists = await check_users_table()
    
    if exists:
        logger.info("=== Users Table Check: SUCCESS ===")
    else:
        logger.error("=== Users Table Check: FAILED ===")
        logger.error("The users table does not exist")

if __name__ == "__main__":
    asyncio.run(main())
