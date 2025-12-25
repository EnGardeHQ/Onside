"""
Test SEO Database Connection

This script tests the connection to the PostgreSQL database and verifies
that all SEO-related tables exist and are accessible.
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, inspect
from typing import List, Dict, Any
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql+asyncpg://tobymorning@localhost:5432/onside"

# Expected tables and their columns
EXPECTED_TABLES = {
    "seo_metrics": [
        "id", "domain_id", "metric_date", "metric_type", "device_type", 
        "data", "created_at", "updated_at"
    ],
    "seo_issues": [
        "id", "domain_id", "issue_type", "status", "severity", "url", 
        "details", "first_detected", "last_detected", "resolved_at", 
        "created_at", "updated_at"
    ],
    "seo_search_keywords": [
        "id", "domain_id", "keyword", "current_rank", "previous_rank", 
        "search_volume", "difficulty_score", "url", "last_updated", "created_at"
    ]
}

async def check_database_connection() -> bool:
    """Test the database connection."""
    try:
        engine = create_async_engine(DATABASE_URL)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                return True
        return False
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

async def get_existing_tables() -> List[str]:
    """Get a list of all tables in the database."""
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(
            text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            """)
        )
        return [row[0] for row in result]

async def get_table_columns(table_name: str) -> List[str]:
    """Get the column names for a specific table."""
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(
            text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = :table_name
            ORDER BY ordinal_position
            """),
            {"table_name": table_name}
        )
        return [row[0] for row in result]

async def check_tables_exist() -> Dict[str, bool]:
    """Check if all expected tables exist."""
    existing_tables = await get_existing_tables()
    return {
        table: table in existing_tables
        for table in EXPECTED_TABLES.keys()
    }

async def check_table_columns() -> Dict[str, Dict[str, List[str]]]:
    """Check if tables have the expected columns."""
    results = {"missing_columns": {}, "extra_columns": {}}
    
    for table, expected_columns in EXPECTED_TABLES.items():
        existing_columns = await get_table_columns(table)
        
        # Check for missing columns
        missing = [col for col in expected_columns if col not in existing_columns]
        if missing:
            results["missing_columns"][table] = missing
            
        # Check for extra columns
        extra = [col for col in existing_columns if col not in expected_columns]
        if extra:
            results["extra_columns"][table] = extra
    
    return results

async def test_insert_data() -> Dict[str, bool]:
    """Test inserting data into the SEO tables."""
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    results = {}
    
    try:
        # Test insert into seo_metrics
        async with async_session() as session:
            await session.execute(
                text("""
                INSERT INTO seo_metrics 
                (domain_id, metric_date, metric_type, device_type, data)
                VALUES 
                (1, NOW(), 'search_analytics', 'desktop', '{"clicks": 100, "impressions": 1000}'::jsonb)
                RETURNING id
                """)
            )
            await session.commit()
            results["seo_metrics"] = True
            logger.info("✅ Successfully inserted test data into seo_metrics")
    except Exception as e:
        results["seo_metrics"] = False
        logger.error(f"❌ Failed to insert into seo_metrics: {e}")
    
    try:
        # Test insert into seo_issues
        async with async_session() as session:
            await session.execute(
                text("""
                INSERT INTO seo_issues 
                (domain_id, issue_type, status, severity, url, details)
                VALUES 
                (1, 'mobile_usability', 'active', 'high', 'https://example.com', '{"issue": "Text too small to read"}'::jsonb)
                RETURNING id
                """)
            )
            await session.commit()
            results["seo_issues"] = True
            logger.info("✅ Successfully inserted test data into seo_issues")
    except Exception as e:
        results["seo_issues"] = False
        logger.error(f"❌ Failed to insert into seo_issues: {e}")
    
    try:
        # Test insert into seo_search_keywords
        async with async_session() as session:
            await session.execute(
                text("""
                INSERT INTO seo_search_keywords 
                (domain_id, keyword, current_rank, search_volume, difficulty_score, url)
                VALUES 
                (1, 'test keyword', 5, 1000, 45.5, 'https://example.com/test')
                RETURNING id
                """)
            )
            await session.commit()
            results["seo_search_keywords"] = True
            logger.info("✅ Successfully inserted test data into seo_search_keywords")
    except Exception as e:
        results["seo_search_keywords"] = False
        logger.error(f"❌ Failed to insert into seo_search_keywords: {e}")
    
    return results

async def main():
    """Run all database tests."""
    print("🔍 Starting SEO Database Tests")
    print("=" * 50)
    
    # Test database connection
    print("\n🔌 Testing database connection...")
    connected = await check_database_connection()
    if connected:
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
        return
    
    # Check if tables exist
    print("\n📋 Checking for required tables...")
    table_checks = await check_tables_exist()
    all_tables_exist = all(table_checks.values())
    
    for table, exists in table_checks.items():
        status = "✅" if exists else "❌"
        print(f"{status} {table}")
    
    if not all_tables_exist:
        print("\n❌ Some required tables are missing. Please run setup_seo_database.py first.")
        return
    
    # Check table columns
    print("\n🔍 Verifying table columns...")
    column_checks = await check_table_columns()
    
    if column_checks["missing_columns"]:
        print("\n❌ Missing columns:")
        for table, columns in column_checks["missing_columns"].items():
            print(f"  {table}: {', '.join(columns)}")
    
    if column_checks["extra_columns"]:
        print("\n⚠️  Extra columns (usually safe to ignore):")
        for table, columns in column_checks["extra_columns"].items():
            print(f"  {table}: {', '.join(columns)}")
    
    if not column_checks["missing_columns"] and not column_checks["extra_columns"]:
        print("✅ All tables have the expected columns")
    
    # Test data insertion
    print("\n🧪 Testing data insertion...")
    insert_results = await test_insert_data()
    
    if all(insert_results.values()):
        print("\n✅ All database tests passed successfully!")
    else:
        failed_tables = [table for table, success in insert_results.items() if not success]
        print(f"\n❌ Failed to insert data into: {', '.join(failed_tables)}")

if __name__ == "__main__":
    asyncio.run(main())
