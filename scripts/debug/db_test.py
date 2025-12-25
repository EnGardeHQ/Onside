"""Test database connection."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:onside-password@localhost:5432/onside")

# Convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

print(f"Using database URL: {ASYNC_DATABASE_URL}")

# Create async engine
engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def test_connection():
    """Test database connection."""
    try:
        async with AsyncSessionLocal() as session:
            # Test a simple query
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            print(f"Database connection successful: {result.scalar()}")
    except Exception as e:
        print(f"Database connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
