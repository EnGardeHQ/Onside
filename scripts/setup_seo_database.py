"""
SEO Database Setup Script

This script creates the necessary database tables for the SEO service
following the Semantic Seed coding standards and the implementation plan.
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, Column, Integer, String, DateTime, JSON, ForeignKey, Float, Boolean, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from enum import Enum as PyEnum

# Import the existing Base from your application's models
# This ensures we're using the same Base as the rest of the application
from src.database import Base
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration - using the same URL as the main database
DATABASE_URL = "postgresql+asyncpg://tobymorning@localhost:5432/onside"

# We'll use the Base from src.database to maintain consistency

# Enums
class MetricType(str, PyEnum):
    SEARCH_ANALYTICS = "search_analytics"
    PAGESPEED = "pagespeed"
    CRAWL_STATS = "crawl_stats"
    CORE_WEB_VITALS = "core_web_vitals"

class DeviceType(str, PyEnum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"

class IssueType(str, PyEnum):
    CRAWL_ERROR = "crawl_error"
    MOBILE_USABILITY = "mobile_usability"
    INDEXING = "indexing"
    SECURITY = "security"
    ENHANCEMENT = "enhancement"
    PAGE_EXPERIENCE = "page_experience"

class IssueStatus(str, PyEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    IGNORED = "ignored"

class IssueSeverity(str, PyEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Models
class SEOMetrics(Base):
    """Stores various SEO metrics over time."""
    __tablename__ = "seo_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    metric_date = Column(DateTime, nullable=False)
    metric_type = Column(Enum(MetricType), nullable=False)
    device_type = Column(Enum(DeviceType), nullable=True)
    data = Column(JSONB, nullable=False)  # Flexible storage for different metric types
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        {"postgresql_partition_by": "RANGE (metric_date)"},
    )

class SEOIssues(Base):
    """Tracks SEO issues and their status."""
    __tablename__ = "seo_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    issue_type = Column(Enum(IssueType), nullable=False)
    status = Column(Enum(IssueStatus), default=IssueStatus.ACTIVE, nullable=False)
    severity = Column(Enum(IssueSeverity), nullable=False)
    url = Column(String, nullable=True)
    details = Column(JSONB, nullable=True)  # Flexible storage for issue details
    first_detected = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_detected = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class SEOSearchKeywords(Base):
    """Tracks keyword rankings and performance."""
    __tablename__ = "seo_search_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String, nullable=False)
    current_rank = Column(Integer, nullable=True)
    previous_rank = Column(Integer, nullable=True)
    search_volume = Column(Integer, nullable=True)
    difficulty_score = Column(Float, nullable=True)
    url = Column(String, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        {"postgresql_partition_by": "RANGE (last_updated)"},
    )

async def setup_seo_database():
    """Create SEO database tables and set up initial data."""
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        # Create all tables
        async with engine.begin() as conn:
            # Check if tables already exist
            result = await conn.execute(
                text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'seo_metrics'
                )
                """)
            )
            table_exists = result.scalar()
            
            if table_exists:
                logger.info("SEO tables already exist. Skipping table creation.")
                return
            
            # Create tables
            logger.info("Creating SEO database tables...")
            
            # Create enum types first
            await conn.execute(text("""
            DO $$
            BEGIN
                -- Create ENUM types if they don't exist
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'metrictype') THEN
                    CREATE TYPE metrictype AS ENUM ('search_analytics', 'pagespeed', 'crawl_stats', 'core_web_vitals');
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'devicetype') THEN
                    CREATE TYPE devicetype AS ENUM ('desktop', 'mobile', 'tablet');
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'issuetype') THEN
                    CREATE TYPE issuetype AS ENUM (
                        'crawl_error', 'mobile_usability', 'indexing', 
                        'security', 'enhancement', 'page_experience'
                    );
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'issuestatus') THEN
                    CREATE TYPE issuestatus AS ENUM ('active', 'resolved', 'ignored');
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'issueseverity') THEN
                    CREATE TYPE issueseverity AS ENUM ('critical', 'high', 'medium', 'low');
                END IF;
            END $$;
            """))
            
            # Create tables one by one to handle dependencies
            tables_to_create = [
                """
                CREATE TABLE IF NOT EXISTS seo_metrics (
                    id SERIAL PRIMARY KEY,
                    domain_id INTEGER REFERENCES domains(id) ON DELETE CASCADE,
                    metric_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                    metric_type metrictype NOT NULL,
                    device_type devicetype,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                ) PARTITION BY RANGE (metric_date);
                """,
                """
                CREATE TABLE IF NOT EXISTS seo_issues (
                    id SERIAL PRIMARY KEY,
                    domain_id INTEGER REFERENCES domains(id) ON DELETE CASCADE,
                    issue_type issuetype NOT NULL,
                    status issuestatus DEFAULT 'active',
                    severity issueseverity NOT NULL,
                    url TEXT,
                    details JSONB,
                    first_detected TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    last_detected TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    resolved_at TIMESTAMP WITHOUT TIME ZONE,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS seo_search_keywords (
                    id SERIAL PRIMARY KEY,
                    domain_id INTEGER REFERENCES domains(id) ON DELETE CASCADE,
                    keyword TEXT NOT NULL,
                    current_rank INTEGER,
                    previous_rank INTEGER,
                    search_volume INTEGER,
                    difficulty_score FLOAT,
                    url TEXT,
                    last_updated TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                );
                """
            ]
            
            for create_table_sql in tables_to_create:
                await conn.execute(text(create_table_sql))
            
            # Create partitions for time-series tables
            await conn.execute(text("""
            -- Create partitions for seo_metrics
            CREATE TABLE IF NOT EXISTS seo_metrics_y2024m05 PARTITION OF seo_metrics
                FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');
                
            CREATE TABLE IF NOT EXISTS seo_metrics_y2024m06 PARTITION OF seo_metrics
                FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');
                
            -- Create indexes on partitions
            CREATE INDEX IF NOT EXISTS idx_seo_metrics_y2024m05_domain_date ON seo_metrics_y2024m05(domain_id, metric_date);
            CREATE INDEX IF NOT EXISTS idx_seo_metrics_y2024m06_domain_date ON seo_metrics_y2024m06(domain_id, metric_date);
            
            -- Create indexes on seo_issues
            CREATE INDEX IF NOT EXISTS idx_seo_issues_domain ON seo_issues(domain_id);
            CREATE INDEX IF NOT EXISTS idx_seo_issues_status ON seo_issues(status);
            CREATE INDEX IF NOT EXISTS idx_seo_issues_type ON seo_issues(issue_type);
            
            -- Create indexes on seo_search_keywords
            CREATE INDEX IF NOT EXISTS idx_seo_keywords_domain ON seo_search_keywords(domain_id);
            CREATE INDEX IF NOT EXISTS idx_seo_keywords_rank ON seo_search_keywords(domain_id, current_rank);
            """))
            
            logger.info("Successfully created SEO database tables and indexes")
            
    except Exception as e:
        logger.error(f"Error setting up SEO database: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(setup_seo_database())
