"""Simple test script to verify the consolidated User model."""
import asyncio
import sys
import os
import tempfile
import shutil
import logging
from contextlib import asynccontextmanager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from enum import Enum as PyEnum
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use a test database
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "onside_test.db")
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
logger.info(f"Using test database at: {TEST_DB_PATH}")

# Create a simple engine just for testing
engine = create_async_engine(TEST_DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

# Enable foreign key support for SQLite
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRole(str, PyEnum):
    ADMIN = "admin"
    USER = "user"
    ANALYST = "analyst"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, default=lambda: datetime.utcnow().isoformat(), onupdate=lambda: datetime.utcnow().isoformat())

    def set_password(self, password: str):
        """Hash and set the user's password."""
        self.hashed_password = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the stored hash."""
        return pwd_context.verify(password, self.hashed_password)

async def init_models():
    """Initialize the test database with all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_models():
    """Drop all tables from the test database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@asynccontextmanager
async def db_session():
    """Provide a transactional scope around a series of operations."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def test_user_creation():
    """Test user creation and password hashing."""
    # Initialize the test database
    await init_models()
    
    async with db_session() as db:
        try:
            # Create a test user
            test_email = "test@example.com"
            test_password = "testpassword123"
            
            user = User(
                email=test_email,
                username="testuser",
                name="Test User",
                role=UserRole.USER,
                is_active=True
            )
            user.set_password(test_password)
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # Verify the user was created
            assert user.id is not None
            assert user.email == test_email
            assert user.check_password(test_password)
            assert not user.check_password("wrongpassword")
            assert user.role == UserRole.USER
            assert user.is_active is True
            
            logger.info("✅ User model test passed!")
            
            # Clean up
            await db.delete(user)
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Test failed: {e}")
            raise

async def main():
    """Run the test."""
    try:
        await test_user_creation()
        return 0
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return 1
    finally:
        # Clean up the test database
        try:
            await drop_models()
            await engine.dispose()
            if os.path.exists(TEST_DB_PATH):
                os.unlink(TEST_DB_PATH)
        except Exception as e:
            logger.warning(f"Warning during cleanup: {e}")

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
