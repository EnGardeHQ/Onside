"""
Setup Domains Table

This script creates the domains table that is required by the SEO service.
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from enum import Enum as PyEnum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql+asyncpg://tobymorning@localhost:5432/onside"

# Base class for SQLAlchemy models
Base = declarative_base()

# Enums
class DomainStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

class Domain(Base):
    """Represents a domain in the system."""
    __tablename__ = "domains"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    display_name = Column(String, nullable=True)
    status = Column(Enum(DomainStatus), default=DomainStatus.ACTIVE, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=True)

async def setup_domains_table():
    """Create the domains table if it doesn't exist."""
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        # Check if domains table exists
        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'domains'
                )
                """)
            )
            table_exists = result.scalar()
            
            if table_exists:
                logger.info("domains table already exists. Skipping creation.")
                return
            
            # Create the table
            logger.info("Creating domains table...")
            await conn.run_sync(Base.metadata.create_all)
            
            # Create indexes
            await conn.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_domains_company_id ON domains(company_id);
                CREATE INDEX IF NOT EXISTS idx_domains_status ON domains(status);
                """)
            )
            
            logger.info("Successfully created domains table and indexes")
            
    except Exception as e:
        logger.error(f"Error setting up domains table: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(setup_domains_table())
