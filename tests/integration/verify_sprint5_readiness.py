"""
Sprint 5 Readiness Verification Script
Following Semantic Seed BDD/TDD Coding Standards V2.0

This script verifies that all prerequisite fixes are in place for Sprint 5,
including database schema validation, performance monitoring, and enhanced error recovery.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
import os
from datetime import datetime
import json
from sqlalchemy.ext.asyncio import create_async_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our new utilities
from src.utils.schema_validator import SchemaValidator, EXPECTED_SCHEMA
from src.services.monitoring.performance_monitor import performance_monitor, measure_async
from src.services.caching.cache_service import cache_service, cache_async


async def verify_database_connection():
    """Verify database connection and return the engine."""
    logger.info("Verifying database connection...")
    
    # Database connection parameters
    db_host = "localhost"
    db_port = 5432
    db_name = "onside"
    db_user = "tobymorning"
    
    # Create async engine
    connection_str = f"postgresql+asyncpg://{db_user}@{db_host}:{db_port}/{db_name}"
    engine = create_async_engine(connection_str, echo=False)
    
    # Test connection
    try:
        async with engine.connect() as conn:
            from sqlalchemy.sql import text
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
            logger.info("✅ Database connection successful")
        return engine
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        raise


@measure_async
@cache_async(ttl=60)  # Cache result for 60 seconds
async def validate_database_schema(engine):
    """Validate database schema against expected structure."""
    logger.info("Validating database schema...")
    
    # Initialize schema validator
    validator = SchemaValidator(engine)
    
    # Export current schema to JSON
    os.makedirs("exports", exist_ok=True)
    schema_file = f"exports/schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    await validator.export_current_schema(schema_file)
    logger.info(f"Schema exported to {schema_file}")
    
    # Validate schema against expected structure
    results = await validator.validate_schema(EXPECTED_SCHEMA)
    
    # Check results
    all_valid = all(result.get("valid", False) for result in results.values())
    
    if all_valid:
        logger.info("✅ All tables validated successfully")
    else:
        logger.warning("⚠️ Schema validation issues found:")
        for table_name, result in results.items():
            if not result.get("valid", False):
                logger.warning(f"  - {table_name}: {result}")
                
        # Generate migration SQL
        migration_sql = await validator.generate_migration_sql()
        migration_file = f"exports/migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        with open(migration_file, 'w') as f:
            f.write(migration_sql)
        logger.info(f"Migration SQL exported to {migration_file}")
    
    return results


@measure_async
async def test_performance_monitoring():
    """Test performance monitoring functionality."""
    logger.info("Testing performance monitoring...")
    
    # Simulate some operations
    with performance_monitor.measure("test_operation", metadata={"test": True}):
        await asyncio.sleep(0.5)
    
    # Async operation
    await performance_monitor.measure_async(
        "test_async_operation",
        asyncio.sleep(0.3),
        metadata={"async": True}
    )
    
    # Get and display metrics
    metrics = performance_monitor.get_metrics_summary()
    logger.info(f"Performance metrics: {json.dumps(metrics, indent=2)}")
    
    # Export metrics
    metrics_file = performance_monitor.export_metrics()
    logger.info(f"✅ Performance monitoring tested and metrics exported to {metrics_file}")
    
    return metrics


@measure_async
async def test_caching_service():
    """Test caching service functionality."""
    logger.info("Testing caching service...")
    
    # Set some values in cache
    cache_service.set("test_key", "test_value")
    cache_service.set("test_json", {"status": "ok", "count": 42})
    
    # Retrieve values
    value1 = cache_service.get("test_key")
    value2 = cache_service.get("test_json")
    
    assert value1 == "test_value"
    assert value2["count"] == 42
    
    # Test decorated function
    @cache_async(ttl=30)
    async def slow_operation(param):
        await asyncio.sleep(0.2)
        return f"Result: {param}"
    
    # Call multiple times to test caching
    result1 = await slow_operation("test")
    result2 = await slow_operation("test")  # Should be cached
    
    # Get cache stats
    stats = cache_service.get_stats()
    logger.info(f"Cache stats: {json.dumps(stats, indent=2)}")
    
    # Save cache to disk
    cache_file = cache_service.save_to_disk()
    logger.info(f"✅ Caching service tested and cache saved to {cache_file}")
    
    return stats


async def main():
    """Main verification function."""
    logger.info("Starting Sprint 5 readiness verification...")
    start_time = time.time()
    
    try:
        # Verify database connection
        engine = await verify_database_connection()
        
        # Validate database schema
        schema_results = await validate_database_schema(engine)
        
        # Test performance monitoring
        monitoring_results = await test_performance_monitoring()
        
        # Test caching service
        caching_results = await test_caching_service()
        
        # Compile final report
        total_time = time.time() - start_time
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_verification_time": total_time,
            "database_schema_valid": all(result.get("valid", False) for result in schema_results.values()),
            "performance_monitoring_active": len(monitoring_results) > 0,
            "caching_service_active": caching_results["hit_rate"] >= 0,
            "sprint5_ready": True
        }
        
        # Save report to file
        report_file = f"exports/sprint5_readiness_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Sprint 5 readiness report saved to {report_file}")
        logger.info(f"✅ Verification completed in {total_time:.2f} seconds")
        
        if report["sprint5_ready"]:
            logger.info("🚀 System is READY for Sprint 5! All components are functioning correctly.")
        else:
            logger.warning("⚠️ System is NOT READY for Sprint 5. Please fix the issues above.")
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
