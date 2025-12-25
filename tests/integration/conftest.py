print("\n[CONftest VERY EARLY DEBUG] conftest.py is being read by pytest -- TOP OF FILE\n")
import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker

# Use the existing database for testing
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://tobymorning@localhost:5432/onside")

# Import all models to ensure they're registered with Base
# Ensure all your models are imported here
from src.database import Base # Assuming Base is in base_model.py
from src.models.domain import Domain
# Add other model imports as needed, e.g.:
# from src.models.company import Company
# from src.models.competitor import Competitor 
# ... and so on for all models that define tables

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()

@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create and configure the database engine for testing."""
    engine_instance = create_async_engine(
        TEST_DATABASE_URL,
        echo=True,  # Set to False to reduce test output
        future=True,
        poolclass=NullPool,
        pool_pre_ping=True
    )
    
    # Create all tables
    async with engine_instance.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine_instance
    
    # Clean up
    await engine_instance.dispose()

@pytest_asyncio.fixture(scope="function") # Changed to function scope for better test isolation
async def db_session(engine):
    print("\n[CONftest DEBUG] DB Session fixture (function scope): START")
    
    # Each test gets a new connection and transaction
    async with engine.connect() as connection:
        async with connection.begin() as transaction:
            SessionLocal = async_sessionmaker(
                bind=connection,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            async with SessionLocal() as session:
                print("[CONftest DEBUG] DB Session fixture: YIELDING session")
                yield session
                print("[CONftest DEBUG] DB Session fixture: Rolling back transaction (implicit via context manager exit)")
        # Transaction is rolled back here
    print("[CONftest DEBUG] DB Session fixture (function scope): END")