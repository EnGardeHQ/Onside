"""
Add JLL company record to the database.

This script ensures that a JLL (Jones Lang LaSalle) company record
exists in the database for testing the JLL analysis workflow.
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

async def add_jll_company():
    """Add JLL company record to the database if it doesn't exist."""
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
        
        # Check if JLL company already exists
        logger.info("Checking if JLL company already exists...")
        async with async_session() as session:
            result = await session.execute(
                text("SELECT id, name FROM companies WHERE name ILIKE '%JLL%' OR name ILIKE '%Jones Lang LaSalle%' LIMIT 1")
            )
            jll_company = result.fetchone()
            
            if jll_company:
                logger.info(f"JLL company already exists: {jll_company.name} (ID: {jll_company.id})")
                return jll_company.id
            
            # Add JLL company record
            logger.info("Adding JLL company record...")
            
            # Get an existing user ID to reference (required for the foreign key)
            user_result = await session.execute(text("SELECT id FROM users LIMIT 1"))
            user_id = user_result.scalar()
            
            if not user_id:
                logger.error("No users found in the database. Cannot create company without user_id")
                return None
            
            jll_data = {
                "name": "Jones Lang LaSalle (JLL)",
                "domain": "jll.com",
                "description": "Global commercial real estate services company specializing in property services, facility management, and investment management.",
                "industry": "Real Estate Services",
                "size": 98000,
                "is_active": True,
                "user_id": user_id
            }
            
            # Insert company
            insert_result = await session.execute(
                text("""
                    INSERT INTO companies 
                    (name, domain, description, industry, size, is_active, user_id) 
                    VALUES 
                    (:name, :domain, :description, :industry, :size, :is_active, :user_id)
                    RETURNING id
                """),
                jll_data
            )
            
            jll_id = insert_result.scalar()
            await session.commit()
            
            logger.info(f"✅ Added JLL company with ID: {jll_id}")
            return jll_id
            
    except Exception as e:
        logger.error(f"❌ Error adding JLL company: {str(e)}")
        return None

async def main():
    """Run the add JLL company script."""
    logger.info("=== Starting Add JLL Company Script ===")
    jll_id = await add_jll_company()
    
    if jll_id:
        logger.info(f"=== JLL Company Script: SUCCESS (ID: {jll_id}) ===")
        logger.info("The database now has a JLL company record for testing")
        return 0
    else:
        logger.error("=== JLL Company Script: FAILED ===")
        logger.error("Failed to add JLL company record")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
