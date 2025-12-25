"""
SEO Database Setup Script (Fixed)

This script creates the necessary database tables for the SEO service
following the Semantic Seed coding standards and the implementation plan.
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from enum import Enum as PyEnum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql+asyncpg://tobymorning@localhost:5432/onside"

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

async def setup_seo_database():
    """Create SEO database tables and set up initial data."""
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=True)
        
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
            # 1. seo_metrics table (partitioned)
            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS seo_metrics (
                id SERIAL,
                domain_id INTEGER NOT NULL,
                metric_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                metric_type metrictype NOT NULL,
                device_type devicetype,
                data JSONB NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                PRIMARY KEY (id, metric_date),
                CONSTRAINT fk_domain
                    FOREIGN KEY(domain_id) 
                    REFERENCES domains(id)
                    ON DELETE CASCADE
            ) PARTITION BY RANGE (metric_date);
            """))
            
            # 2. seo_issues table
            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS seo_issues (
                id SERIAL PRIMARY KEY,
                domain_id INTEGER NOT NULL,
                issue_type issuetype NOT NULL,
                status issuestatus DEFAULT 'active',
                severity issueseverity NOT NULL,
                url TEXT,
                details JSONB,
                first_detected TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                last_detected TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                resolved_at TIMESTAMP WITHOUT TIME ZONE,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                CONSTRAINT fk_issue_domain
                    FOREIGN KEY(domain_id) 
                    REFERENCES domains(id)
                    ON DELETE CASCADE
            );
            
            -- Create indexes on seo_issues
            CREATE INDEX IF NOT EXISTS idx_seo_issues_domain 
                ON seo_issues(domain_id);
                
            CREATE INDEX IF NOT EXISTS idx_seo_issues_status 
                ON seo_issues(status);
                
            CREATE INDEX IF NOT EXISTS idx_seo_issues_type 
                ON seo_issues(issue_type);
            """))
            
            # 3. seo_search_keywords table
            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS seo_search_keywords (
                id SERIAL PRIMARY KEY,
                domain_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                current_rank INTEGER,
                previous_rank INTEGER,
                search_volume INTEGER,
                difficulty_score FLOAT,
                url TEXT,
                last_updated TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                CONSTRAINT fk_keyword_domain
                    FOREIGN KEY(domain_id) 
                    REFERENCES domains(id)
                    ON DELETE CASCADE
            );
            
            -- Create indexes on seo_search_keywords
            CREATE INDEX IF NOT EXISTS idx_seo_keywords_domain 
                ON seo_search_keywords(domain_id);
                
            CREATE INDEX IF NOT EXISTS idx_seo_keywords_rank 
                ON seo_search_keywords(domain_id, current_rank);
            """))
            
            # Create partitions for time-series tables
            # May 2024 partition
            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS seo_metrics_y2024m05 
                PARTITION OF seo_metrics 
                FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');
                
            -- June 2024 partition
            CREATE TABLE IF NOT EXISTS seo_metrics_y2024m06 
                PARTITION OF seo_metrics 
                FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');
                
            -- Create indexes on partitions
            CREATE INDEX IF NOT EXISTS idx_seo_metrics_y2024m05_domain_date 
                ON seo_metrics_y2024m05(domain_id, metric_date);
                
            CREATE INDEX IF NOT EXISTS idx_seo_metrics_y2024m06_domain_date 
                ON seo_metrics_y2024m06(domain_id, metric_date);
            """))
            
            # Add table comments
            await conn.execute(text("""
            COMMENT ON TABLE seo_metrics IS 'Stores various SEO metrics over time, partitioned by date for performance';
            COMMENT ON TABLE seo_issues IS 'Tracks SEO issues and their status';
            COMMENT ON TABLE seo_search_keywords IS 'Stores keyword rankings and search performance data';
            """))
            CREATE TABLE IF NOT EXISTS seo_metrics (
                id SERIAL,
                domain_id INTEGER NOT NULL,
                metric_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                metric_type metrictype NOT NULL,
                device_type devicetype,
                data JSONB NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                PRIMARY KEY (id, metric_date),
                CONSTRAINT fk_domain
                    FOREIGN KEY(domain_id) 
                    REFERENCES domains(id)
                    ON DELETE CASCADE
            ) PARTITION BY RANGE (metric_date);
            
            -- 2. seo_issues table
            CREATE TABLE IF NOT EXISTS seo_issues (
                id SERIAL PRIMARY KEY,
                domain_id INTEGER NOT NULL,
                issue_type issuetype NOT NULL,
                status issuestatus DEFAULT 'active',
                severity issueseverity NOT NULL,
                url TEXT,
                details JSONB,
                first_detected TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                last_detected TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                resolved_at TIMESTAMP WITHOUT TIME ZONE,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                CONSTRAINT fk_issue_domain
                    FOREIGN KEY(domain_id) 
                    REFERENCES domains(id)
                    ON DELETE CASCADE
            );
            
            -- 3. seo_search_keywords table
            CREATE TABLE IF NOT EXISTS seo_search_keywords (
                id SERIAL PRIMARY KEY,
                domain_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                current_rank INTEGER,
                previous_rank INTEGER,
                search_volume INTEGER,
                difficulty_score FLOAT,
                url TEXT,
                last_updated TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                CONSTRAINT fk_keyword_domain
                    FOREIGN KEY(domain_id) 
                    REFERENCES domains(id)
                    ON DELETE CASCADE
            );
            
            -- Create partitions for time-series tables
            -- May 2024 partition
            CREATE TABLE IF NOT EXISTS seo_metrics_y2024m05 
                PARTITION OF seo_metrics 
                FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');
                
            -- June 2024 partition
            CREATE TABLE IF NOT EXISTS seo_metrics_y2024m06 
                PARTITION OF seo_metrics 
                FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');
                
            -- Create indexes on partitions
            CREATE INDEX IF NOT EXISTS idx_seo_metrics_y2024m05_domain_date 
                ON seo_metrics_y2024m05(domain_id, metric_date);
                
            CREATE INDEX IF NOT EXISTS idx_seo_metrics_y2024m06_domain_date 
                ON seo_metrics_y2024m06(domain_id, metric_date);
            
            -- Create indexes on seo_issues
            CREATE INDEX IF NOT EXISTS idx_seo_issues_domain 
                ON seo_issues(domain_id);
                
            CREATE INDEX IF NOT EXISTS idx_seo_issues_status 
                ON seo_issues(status);
                
            CREATE INDEX IF NOT EXISTS idx_seo_issues_type 
                ON seo_issues(issue_type);
            
            -- Create indexes on seo_search_keywords
            CREATE INDEX IF NOT EXISTS idx_seo_keywords_domain 
                ON seo_search_keywords(domain_id);
                
            CREATE INDEX IF NOT EXISTS idx_seo_keywords_rank 
                ON seo_search_keywords(domain_id, current_rank);
            
            -- Add comment for table documentation
            COMMENT ON TABLE seo_metrics IS 'Stores various SEO metrics over time, partitioned by date for performance';
            COMMENT ON TABLE seo_issues IS 'Tracks SEO issues and their status';
            COMMENT ON TABLE seo_search_keywords IS 'Stores keyword rankings and search performance data';
            
            logger.info("Successfully created SEO database tables and indexes");
            
    except Exception as e:
        logger.error(f"Error setting up SEO database: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(setup_seo_database())
