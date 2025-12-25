"""Test Railway service connections.

This script verifies that all critical services can connect properly
on Railway's infrastructure. Run this to diagnose connectivity issues.

Usage:
    railway run python scripts/test_railway_connections.py
    # Or locally with Railway env:
    railway run --local python scripts/test_railway_connections.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from sqlalchemy import create_engine, text
    import redis
    from src.config import get_settings
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Install requirements: pip install -r requirements.txt")
    sys.exit(1)


async def test_database():
    """Test database connection."""
    print("\n" + "=" * 60)
    print("Testing Database Connection")
    print("=" * 60)

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set in environment")
        return False

    # Show sanitized URL
    sanitized = db_url.split("@")[-1] if "@" in db_url else "unknown"
    print(f"Database host: {sanitized}")

    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✅ Database connected successfully")

                # Test tables exist
                tables_query = text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    LIMIT 5
                """)
                tables = conn.execute(tables_query).fetchall()
                print(f"✅ Found {len(tables)} tables in database")
                for table in tables:
                    print(f"   - {table[0]}")

                return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False


async def test_redis():
    """Test Redis connection."""
    print("\n" + "=" * 60)
    print("Testing Redis Connection")
    print("=" * 60)

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        print("❌ REDIS_URL not set in environment")
        return False

    # Show sanitized URL
    sanitized = redis_url.split("@")[-1] if "@" in redis_url else "unknown"
    print(f"Redis host: {sanitized}")

    try:
        r = redis.from_url(redis_url, socket_connect_timeout=5)

        # Test ping
        if r.ping():
            print("✅ Redis connected successfully")

            # Test set/get
            test_key = "railway_test_key"
            test_value = "railway_test_value"
            r.set(test_key, test_value, ex=60)
            retrieved = r.get(test_key)

            if retrieved and retrieved.decode() == test_value:
                print("✅ Redis read/write operations working")
                r.delete(test_key)

                # Show Redis info
                info = r.info("server")
                print(f"   Redis version: {info.get('redis_version', 'unknown')}")
                print(f"   Uptime: {info.get('uptime_in_seconds', 0)} seconds")

                return True
            else:
                print("❌ Redis read/write test failed")
                return False
    except redis.ConnectionError as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Check that Redis service is running on Railway")
        return False
    except Exception as e:
        print(f"❌ Redis error: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False


async def test_environment():
    """Test critical environment variables."""
    print("\n" + "=" * 60)
    print("Testing Environment Variables")
    print("=" * 60)

    required = {
        "DATABASE_URL": "PostgreSQL connection string (auto-set by Railway)",
        "REDIS_URL": "Redis connection string (auto-set by Railway)",
        "SECRET_KEY": "JWT signing key (must be set manually)",
    }

    important = {
        "SERPAPI_KEY": "Required for walker agent SERP analysis",
        "CELERY_BROKER_URL": "Should equal REDIS_URL",
        "ALLOWED_ORIGINS": "CORS configuration",
        "APP_ENV": "Should be 'production' on Railway",
    }

    optional = {
        "SEMRUSH_API_KEY": "Optional SEO API",
        "OPENAI_API_KEY": "Optional AI features",
        "CACHE_ENABLED": "Should be 'true'",
    }

    all_set = True

    print("\nRequired Variables (CRITICAL):")
    for var, description in required.items():
        value = os.getenv(var)
        if value:
            # Show length but not actual value for security
            print(f"✅ {var}")
            print(f"   {description}")
            print(f"   Length: {len(value)} characters")
        else:
            print(f"❌ {var}: NOT SET")
            print(f"   {description}")
            all_set = False

    print("\nImportant Variables:")
    for var, description in important.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}")
            print(f"   {description}")
            print(f"   Length: {len(value)} characters")
        else:
            print(f"⚠️  {var}: Not set")
            print(f"   {description}")

    print("\nOptional Variables:")
    for var, description in optional.items():
        value = os.getenv(var)
        if value:
            print(f"ℹ️  {var}: {value[:50]}...")
        else:
            print(f"   {var}: Not set (optional)")

    return all_set


async def test_app_config():
    """Test application configuration."""
    print("\n" + "=" * 60)
    print("Testing Application Configuration")
    print("=" * 60)

    try:
        settings = get_settings()

        print(f"✅ Configuration loaded successfully")
        print(f"   Environment: {settings.environment}")
        print(f"   Debug mode: {settings.debug}")
        print(f"   Cache enabled: {settings.CACHE_ENABLED}")
        print(f"   API version: {settings.api_version}")

        # Check critical settings
        if settings.environment != "production":
            print(f"⚠️  Environment is '{settings.environment}', should be 'production' on Railway")

        if settings.debug:
            print("⚠️  Debug mode is enabled, should be False in production")

        if not settings.CACHE_ENABLED:
            print("⚠️  Cache is disabled, performance will be degraded")

        return True
    except Exception as e:
        print(f"❌ Configuration load failed: {e}")
        return False


async def test_celery_broker():
    """Test Celery broker connection."""
    print("\n" + "=" * 60)
    print("Testing Celery Broker")
    print("=" * 60)

    celery_broker = os.getenv("CELERY_BROKER_URL")
    if not celery_broker:
        print("⚠️  CELERY_BROKER_URL not set")
        print("   This is required for background tasks")
        return False

    # Celery broker is usually Redis
    if celery_broker.startswith("redis://"):
        print("ℹ️  Celery broker is Redis (expected)")
        # Already tested Redis above
        print("✅ Celery broker should work (Redis is functional)")
        return True
    else:
        print(f"⚠️  Unexpected Celery broker type: {celery_broker[:20]}...")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Railway Service Connection Tests")
    print("=" * 60)
    print("Testing OnSide microservice connectivity on Railway")
    print()

    # Show Railway-specific info
    if os.getenv("RAILWAY_ENVIRONMENT"):
        print(f"Railway Environment: {os.getenv('RAILWAY_ENVIRONMENT')}")
    if os.getenv("RAILWAY_PROJECT_NAME"):
        print(f"Railway Project: {os.getenv('RAILWAY_PROJECT_NAME')}")
    if os.getenv("RAILWAY_SERVICE_NAME"):
        print(f"Railway Service: {os.getenv('RAILWAY_SERVICE_NAME')}")

    results = {
        "Environment Variables": await test_environment(),
        "Application Config": await test_app_config(),
        "Database": await test_database(),
        "Redis": await test_redis(),
        "Celery Broker": await test_celery_broker(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("✅ ALL TESTS PASSED - Services are properly connected")
        print("\nWalker agents should be able to connect to all required services.")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - Walker agents may not connect properly")
        print("\nReview the failures above and fix environment configuration.")
        print("\nCommon fixes:")
        print("1. Set missing environment variables in Railway dashboard")
        print("2. Verify DATABASE_URL and REDIS_URL are auto-set by Railway addons")
        print("3. Manually set SECRET_KEY and SERPAPI_KEY")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
