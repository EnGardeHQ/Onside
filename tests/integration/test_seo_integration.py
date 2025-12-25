"""Integration tests for the SEO service.

These tests verify the functionality of the SEOService class by connecting to actual services.
Following project standards, these tests run against the test database.
"""
import logging
import os
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy import text, MetaData, Table, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.schema import CreateSchema

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import models to ensure they're registered with SQLAlchemy
from src.database import Base
from src.models.domain import Domain
from src.models.content import Content
from src.models.user import User
from src.models.market import MarketTag, MarketSegment, Competitor, CompetitorContent, CompetitorMetrics
from src.models.ai import AIInsight

# Import services
from src.services.seo.seo_service import SEOService

# Set up logging with more detailed configuration
log_file = '/tmp/onside_test.log'

# Clear previous log file if it exists
if os.path.exists(log_file):
    os.remove(log_file)

# Create a custom formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Set up file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Set up console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Get logger for this module
logger = logging.getLogger(__name__)
logger.info(f"Logging to file: {log_file}")

# Enable debug logging for SQLAlchemy
sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
sqlalchemy_logger.setLevel(logging.INFO)
sqlalchemy_logger.addHandler(file_handler)

# Enable debug logging for our application
src_logger = logging.getLogger('src')
src_logger.setLevel(logging.DEBUG)
src_logger.addHandler(file_handler)

# Database configuration for tests - using the existing database
TEST_DB_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://tobymorning@localhost:5432/onside")

# Test domain for all tests
TEST_DOMAIN = "example.com"

@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncEngine:
    """Create and configure a new database engine for testing."""
    logger.info(f"Connecting to test database at: {TEST_DB_URL}")
    
    # Create engine with explicit schema
    engine = create_async_engine(
        TEST_DB_URL,
        echo=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        future=True
    )
    
    # Create all tables
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        # Create schema if it doesn't exist
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    logger.info("Dropping database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine):
    """Create a database session for testing."""
    connection = await test_engine.connect()
    transaction = await connection.begin()
    
    # Create a new session with the connection
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection,
        class_=AsyncSession
    )
    
    session = TestingSessionLocal()
    
    try:
        yield session
        await session.rollback()
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()

@pytest_asyncio.fixture(autouse=True)
async def setup_test_data(db_session: AsyncSession):
    """Set up test data in the database before each test."""
    try:
        # Add a test domain to the database
        test_domain = Domain(
            domain=TEST_DOMAIN,
            is_active=True,
            last_crawled=None
        )
        db_session.add(test_domain)
        await db_session.commit()
        logger.info(f"Test domain {TEST_DOMAIN} added to database")
        
        yield
        
    except Exception as e:
        logger.error(f"Error setting up test data: {str(e)}")
        raise
    finally:
        # Clean up after test
        try:
            await db_session.execute(text("TRUNCATE TABLE domains CASCADE"))
            await db_session.commit()
        except Exception as e:
            logger.error(f"Error cleaning up test data: {str(e)}")
            await db_session.rollback()
            raise



@pytest_asyncio.fixture
async def seo_service(db_session: AsyncSession) -> SEOService:
    """Create an SEOService instance with real database connection.
    
    This fixture provides a properly configured SEOService instance
    connected to the test database.
    """
    return SEOService(db=db_session)

def print_logs():
    """Print the contents of the log file."""
    try:
        with open('/tmp/onside_test.log', 'r') as f:
            print("\n=== LOG FILE CONTENTS ===")
            print(f.read())
            print("=========================\n")
    except Exception as e:
        print(f"Error reading log file: {e}")

@pytest.mark.asyncio
async def test_get_competing_domains_integration(seo_service, db_session):
    """Test getting competing domains with actual service integration."""
    # Register the print_logs function to run after the test
    import atexit
    atexit.register(print_logs)
    
    # Log environment variables (without sensitive values)
    logger.info("Environment variables:")
    for var in ["GOOGLE_API_KEY", "GOOGLE_CSE_ID"]:
        logger.info(f"  {var} = {'[REDACTED]' if os.getenv(var) else 'NOT SET'}")
    
    # Skip if no API keys are available for required services
    required_env_vars = ["GOOGLE_API_KEY", "GOOGLE_CSE_ID"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        pytest.skip(f"Skipping test: Missing required environment variables: {', '.join(missing_vars)}")
    
    try:
        logger.info("1. Starting test_get_competing_domains")
        
        # Log environment variables (without sensitive values)
        logger.info(f"2. Environment variables: {', '.join([f'{k}=[REDACTED]' if 'key' in k.lower() or 'secret' in k.lower() or 'token' in k.lower() or 'password' in k.lower() else f'{k}={os.getenv(k)}' for k in required_env_vars])}")
        
        # Verify database connection
        try:
            logger.info("3. Testing database connection...")
            result = await db_session.execute(text("SELECT 1"))
            logger.info(f"4. Database connection test result: {result.scalar()}")
        except Exception as db_error:
            logger.error(f"Database connection error: {str(db_error)}", exc_info=True)
            raise
        
        # Verify the test domain exists in the database or create it
        logger.info(f"5. Checking if test domain exists: {TEST_DOMAIN}")
        try:
            domain_result = await db_session.execute(
                text("SELECT * FROM domains WHERE domain = :domain"),
                {"domain": TEST_DOMAIN}
            )
            domain = domain_result.first()
            
            if domain is None:
                logger.info("6. Test domain not found, creating...")
                # Create test domain if it doesn't exist
                await db_session.execute(
                    text("INSERT INTO domains (domain, is_active) VALUES (:domain, true)"),
                    {"domain": TEST_DOMAIN}
                )
                await db_session.commit()
                logger.info(f"7. Created test domain in database: {TEST_DOMAIN}")
            else:
                logger.info(f"6. Found test domain in database: {domain}")
                
            # Verify the domain is in the database
            domain_check = await db_session.execute(
                text("SELECT * FROM domains WHERE domain = :domain"),
                {"domain": TEST_DOMAIN}
            )
            domain_check = domain_check.first()
            logger.info(f"8. Domain verification - found in DB: {domain_check is not None}")
            
            # Check service status and available methods
            logger.info(f"8. SEO Service status: {getattr(seo_service, 'service_status', 'Not available')}")
            logger.info(f"9. SEO Service methods: {[m for m in dir(seo_service) if not m.startswith('_')]}")
            
            # Call the actual service with a test domain
            logger.info(f"10. Calling get_competing_domains for domain: {TEST_DOMAIN}")
            try:
                # Add debug info about the service
                logger.info(f"10.1 SEO Service type: {type(seo_service).__name__}")
                logger.info(f"10.2 SEO Service has get_competing_domains: {hasattr(seo_service, 'get_competing_domains')}")
                
                # Try to get competitors
                logger.info("10.3 Calling get_competing_domains...")
                try:
                    competitors = await seo_service.get_competing_domains(TEST_DOMAIN)
                    logger.info(f"11. Successfully got competitors: {competitors is not None}")
                    
                    # If we got None, log a warning
                    if competitors is None:
                        logger.warning("11.1 WARNING: get_competing_domains returned None")
                except Exception as e:
                    logger.error(f"Error calling get_competing_domains: {str(e)}", exc_info=True)
                    raise
                
                # Debug output
                logger.info(f"12. Number of competitors: {len(competitors) if isinstance(competitors, list) else 'N/A'}")
                logger.debug(f"13. Competitors details: {competitors}")
                
                # Basic assertions about the response structure
                assert isinstance(competitors, list), f"Expected competitors to be a list, got {type(competitors)}"
                
                # If we have competitors, verify their structure
                if competitors:
                    logger.info(f"14. Verifying {len(competitors)} competitors")
                    for i, competitor in enumerate(competitors, 1):
                        assert isinstance(competitor, dict), f"Competitor {i} should be a dictionary, got {type(competitor)}"
                        assert "domain" in competitor, f"Competitor {i} is missing 'domain' key"
                        assert isinstance(competitor["domain"], str), f"Competitor {i} domain should be a string, got {type(competitor['domain'])}"
                
                logger.info("15. test_get_competing_domains_integration completed successfully")
                return
                
            except Exception as e:
                logger.error(f"Error in get_competing_domains call: {str(e)}", exc_info=True)
                # Log the full traceback
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                
                # Log additional debug info
                logger.error("Debug Info:")
                logger.error(f"- TEST_DOMAIN: {TEST_DOMAIN}")
                logger.error(f"- seo_service type: {type(seo_service).__name__}")
                logger.error(f"- seo_service has get_competing_domains: {hasattr(seo_service, 'get_competing_domains')}")
                
                # If it's an attribute error, log available methods
                if isinstance(e, AttributeError):
                    logger.error("Available methods in seo_service:")
                    for method in dir(seo_service):
                        if not method.startswith('_'):
                            logger.error(f"  - {method}")
                
                raise
            
        except Exception as e:
            logger.error(f"Error in database operations: {str(e)}", exc_info=True)
            raise
                
        except Exception as e:
            logger.error(f"Error in database operations: {str(e)}", exc_info=True)
            raise
            
    except Exception as e:
        logger.error(f"Error in test_get_competing_domains_integration: {str(e)}", exc_info=True)
        # Log database connection details for debugging
        try:
            db_url = os.getenv("DATABASE_URL")
            logger.info(f"Database URL: {db_url}")
            logger.info(f"Database tables: {Base.metadata.tables.keys() if hasattr(Base, 'metadata') else 'No Base.metadata'}")
            
            # Try to list all tables in the database
            try:
                if db_session:
                    tables = await db_session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
                    logger.info(f"Database tables: {[t[0] for t in tables]}")
            except Exception as tables_err:
                logger.error(f"Error listing database tables: {str(tables_err)}")
                
        except Exception as db_err:
            logger.error(f"Error getting database info: {str(db_err)}", exc_info=True)
        
        # Re-raise the original exception
        raise

@pytest.mark.asyncio
async def test_get_domain_metrics_integration(seo_service, db_session):
    """Test getting domain metrics with actual service integration."""
    # Skip if no API keys are available for required services
    required_env_vars = ["GOOGLE_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        pytest.skip(f"Skipping test: Missing required environment variables: {', '.join(missing_vars)}")
    
    try:
        logger.info("Starting test_get_domain_metrics_integration")
        
        # Verify the test domain exists in the database or create it
        domain = await db_session.execute(
            text("SELECT * FROM domains WHERE domain = :domain"),
            {"domain": TEST_DOMAIN}
        )
        domain = domain.first()
        
        if domain is None:
            # Create test domain if it doesn't exist
            await db_session.execute(
                text("INSERT INTO domains (domain, is_active) VALUES (:domain, true)"),
                {"domain": TEST_DOMAIN}
            )
            await db_session.commit()
            logger.info(f"Created test domain in database: {TEST_DOMAIN}")
        else:
            logger.info(f"Found test domain in database: {domain}")
        
        # Call the actual service with a test domain
        logger.info(f"Calling get_domain_metrics for domain: {TEST_DOMAIN}")
        metrics = await seo_service.get_domain_metrics(TEST_DOMAIN)
        
        # Debug output
        logger.info(f"Received metrics: {metrics}")
        
        # Basic assertions about the response structure
        assert isinstance(metrics, dict), f"Expected metrics to be a dictionary, got {type(metrics)}"
        
        # Check for required top-level keys
        required_keys = ["overview", "traffic", "backlinks", "performance", "mobile_usability"]
        for key in required_keys:
            assert key in metrics, f"Expected key '{key}' in metrics"
        
        # Check that we have some basic metrics
        assert "health_score" in metrics, "Expected health_score in metrics"
        assert 0 <= metrics["health_score"] <= 100, "health_score should be between 0 and 100"
        
        logger.info("test_get_domain_metrics_integration completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test_get_domain_metrics_integration: {str(e)}")
        raise
