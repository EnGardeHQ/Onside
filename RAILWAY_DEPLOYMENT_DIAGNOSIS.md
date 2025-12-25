# Railway Deployment Diagnosis: Walker Agent Connectivity Issues

**Date:** 2025-12-24
**Status:** CRITICAL - Walker agents may not be connecting properly
**Deployment URL:** https://onside-production.up.railway.app

## Executive Summary

Analysis of the OnSide application reveals that while microservices have deployed to Railway successfully, the **SEO Content Walker Agent** and other background services may have connectivity issues due to misconfigured service discovery and environment variables for Railway's infrastructure.

## Critical Issues Identified

### 1. SERVICE DISCOVERY PROBLEM - HIGHEST PRIORITY

**Issue:** The application is configured for Docker Compose with internal DNS (`onside-db`, `onside-redis`, `onside-minio`) but Railway uses different service discovery mechanisms.

**Local Docker URLs (WRONG for Railway):**
- `DATABASE_URL=postgresql://postgres:onside-dev-password@onside-db:5432/onside`
- `REDIS_URL=redis://onside-redis:6379/0`
- `MINIO_ENDPOINT=onside-minio:9000`
- `CELERY_BROKER_URL=redis://onside-redis:6379/0`

**Railway Service Discovery:**
Railway provides private networking URLs via environment variables:
- `DATABASE_URL` - Provided by Railway Postgres
- `REDIS_URL` - Provided by Railway Redis
- Services communicate via Railway's private network URLs (NOT Docker Compose service names)

### 2. WALKER AGENT EXECUTION MODEL

**Architecture:**
The SEO Content Walker Agent (`SEOContentWalkerAgent`) is triggered via:

**Location:** `/Users/cope/EnGardeHQ/Onside/src/api/v1/engarde.py`

```python
# Line 708-712
background_tasks.add_task(
    process_brand_analysis,
    str(job.id),
    questionnaire.dict(),
    db
)
```

**Execution Path:**
1. User initiates via `/api/v1/engarde/brand-analysis/initiate` endpoint
2. FastAPI creates a `BackgroundTask` (NOT Celery)
3. Calls `process_brand_analysis()` which creates `SEOContentWalkerAgent`
4. Agent needs to connect to:
   - **Database** (PostgreSQL) - Store analysis results
   - **Cache** (Redis) - Cache SERP results and crawl data
   - **External APIs** - SerpAPI for keyword analysis

**Problem:** FastAPI `BackgroundTasks` run in the same process as the web server. On Railway:
- If the web server restarts, background tasks are lost
- No task queue persistence
- No worker separation
- Tasks time out after Railway's request timeout (~30s for free tier)

### 3. MISSING RAILWAY-SPECIFIC CONFIGURATION

**Current Configuration:**
- `railway.json` only configures the main API service
- No separate service definitions for workers
- No environment variable mapping for Railway's service URLs

**What's Missing:**
- Railway doesn't use Docker Compose
- Each service needs separate Railway service configuration
- Environment variables must be set in Railway dashboard
- Private networking URLs must be configured

### 4. REDIS CONNECTION CONFIGURATION

**Current Config (`/Users/cope/EnGardeHQ/Onside/src/config.py`):**
```python
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
```

**Issue:** The walker agent initializes cache service:
```python
# Line 139 in seo_content_walker.py
self.serp_analyzer = SerpAnalyzer(cache=cache)
```

If `REDIS_URL` points to `redis://onside-redis:6379/0` (Docker Compose name), it will fail on Railway.

### 5. CELERY WORKER CONFIGURATION MISMATCH

**Docker Compose has Celery workers:**
- `onside-celery-worker` (lines 267-319 in docker-compose.prod.yml)
- `onside-celery-beat` (lines 324-362)
- Configured to run background tasks with queues: `default,reports,scraping,analytics,emails,data_ingestion`

**But the walker agent uses FastAPI BackgroundTasks instead:**
```python
background_tasks.add_task(process_brand_analysis, ...)
```

**Mismatch:**
- Celery infrastructure exists but isn't being used for walker agents
- This means walker agents won't benefit from:
  - Task persistence
  - Worker separation
  - Retry mechanisms
  - Distributed execution

## Railway Deployment Architecture

### Services That Need to Be Deployed Separately on Railway:

1. **Main API Service** (Currently Deployed)
   - Port: 8000
   - Dockerfile: `/Users/cope/EnGardeHQ/Onside/Dockerfile`
   - Start Command: `uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}`

2. **PostgreSQL Database** (Railway Addon)
   - Railway provides `DATABASE_URL` automatically
   - Private network URL provided

3. **Redis Cache** (Railway Addon)
   - Railway provides `REDIS_URL` automatically
   - Private network URL provided

4. **Celery Worker** (MISSING - Needs Deployment)
   - Same Dockerfile, different start command
   - Start Command: `celery -A src.celery_app worker --loglevel=info`
   - Needs same environment variables as API

5. **Celery Beat** (MISSING - Needs Deployment)
   - Same Dockerfile, different start command
   - Start Command: `celery -A src.celery_app beat --loglevel=info`

6. **MinIO Object Storage** (NEEDS ALTERNATIVE)
   - MinIO not available as Railway addon
   - **Recommendation:** Use AWS S3, Cloudflare R2, or Railway volumes

### Environment Variables Required on Railway:

#### Critical Variables (Must Be Set):
```bash
# Database - Auto-provided by Railway Postgres addon
DATABASE_URL=<railway-postgres-url>

# Redis - Auto-provided by Railway Redis addon
REDIS_URL=<railway-redis-url>

# Celery
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Security
SECRET_KEY=<generate-secure-random-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
APP_ENV=production
ALLOWED_ORIGINS=https://onside-production.up.railway.app,https://your-frontend-domain.com

# External APIs (Required for Walker Agent)
SERPAPI_KEY=<your-serpapi-key>
SEMRUSH_API_KEY=<your-semrush-key>
OPENAI_API_KEY=<optional-for-ai-features>

# Object Storage (Alternative to MinIO)
# Option 1: AWS S3
AWS_ACCESS_KEY_ID=<your-aws-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret>
AWS_S3_BUCKET=<your-bucket-name>
AWS_REGION=us-east-1

# Option 2: Use Railway volumes
UPLOAD_DIR=/app/uploads
```

#### Optional but Recommended:
```bash
# Caching
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=300
CACHE_TTL_SERP_RESULTS=86400
CACHE_TTL_WEBSITE_CRAWL=3600

# Performance
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIME_LIMIT=1800
```

## Specific Problems with Walker Agent Connectivity

### Problem 1: Database Connection
**File:** `/Users/cope/EnGardeHQ/Onside/src/agents/seo_content_walker.py`

```python
# Line 125-132
def __init__(self, db: Session, cache: Optional[AsyncCacheService] = None):
    self.db = db
    self.cache = cache
```

**Issue:** If `DATABASE_URL` uses Docker Compose hostname, agent can't connect to database.

**Fix Required:** Ensure Railway's `DATABASE_URL` environment variable is used.

### Problem 2: Redis/Cache Connection
**File:** `/Users/cope/EnGardeHQ/Onside/src/agents/seo_content_walker.py`

```python
# Lines 318-326
if self.cache and settings.CACHE_ENABLED:
    cache_key = hashlib.md5(f"crawl:{url}".encode()).hexdigest()
    cached_result = await self.cache.get(
        cache_key,
        category="website_crawl"
    )
```

**Issue:** Cache service initialized with `REDIS_URL` from environment. If pointing to `onside-redis:6379`, connection fails.

### Problem 3: SERP API Access
**File:** `/Users/cope/EnGardeHQ/Onside/src/agents/seo_content_walker.py`

```python
# Line 139
self.serp_analyzer = SerpAnalyzer(cache=cache)
```

**Dependency:** Requires `SERPAPI_KEY` environment variable.

**Check Required:** Verify `SERPAPI_KEY` is set in Railway dashboard.

### Problem 4: Task Timeout
**Issue:** Walker agent can take 5-15 minutes per analysis (line 653 in engarde.py).

FastAPI BackgroundTasks run in-process, subject to:
- Railway request timeouts
- Server restart = lost tasks
- No visibility into task status

**Fix Required:** Migrate to Celery tasks for long-running operations.

## Recommended Fixes (Priority Order)

### IMMEDIATE FIX 1: Verify Environment Variables in Railway Dashboard

**Action:** Log into Railway dashboard and verify these variables are set:

```bash
# Auto-set by Railway (verify):
DATABASE_URL=postgresql://...railway.app/...
REDIS_URL=redis://...railway.app/...

# Must be manually set:
SECRET_KEY=<random-secure-value>
SERPAPI_KEY=<your-api-key>
ALLOWED_ORIGINS=https://onside-production.up.railway.app

# Application config:
APP_ENV=production
CACHE_ENABLED=true
```

**Verification Command:**
```bash
# From Railway CLI or dashboard, check:
railway variables
```

### IMMEDIATE FIX 2: Add Railway Service for Celery Worker

**Steps:**
1. In Railway dashboard, create new service
2. Link to same GitHub repo
3. Set build configuration:
   - Builder: Dockerfile
   - Dockerfile Path: `Dockerfile`
4. Set start command:
   ```bash
   celery -A src.celery_app worker --loglevel=info --concurrency=4 -Q default,reports,scraping,analytics,emails,data_ingestion
   ```
5. Copy ALL environment variables from main API service
6. Deploy

### IMMEDIATE FIX 3: Convert Walker Agent to Celery Task

**File to Modify:** `/Users/cope/EnGardeHQ/Onside/src/api/v1/engarde.py`

**Current (Line 708-712):**
```python
background_tasks.add_task(
    process_brand_analysis,
    str(job.id),
    questionnaire.dict(),
    db
)
```

**Should Be:**
```python
from src.tasks.brand_analysis_tasks import process_brand_analysis_task

# Queue as Celery task instead
process_brand_analysis_task.delay(
    job_id=str(job.id),
    questionnaire_data=questionnaire.dict()
)
```

**New File Required:** `/Users/cope/EnGardeHQ/Onside/src/tasks/brand_analysis_tasks.py`

### MEDIUM PRIORITY: Replace MinIO with S3-Compatible Storage

**Options:**
1. **AWS S3** (Recommended for production)
2. **Cloudflare R2** (S3-compatible, cheaper)
3. **Railway Volumes** (Simple but limited)

**Code Changes Required:**
- Update MinIO client to use S3 SDK
- Configure S3 credentials in Railway
- Update file upload/download logic

### LONG-TERM: Add Monitoring and Error Tracking

**Recommendations:**
1. Add Sentry for error tracking
2. Add Prometheus/Grafana for metrics
3. Add logging aggregation (Datadog, LogTail)
4. Add uptime monitoring (UptimeRobot, Pingdom)

## Testing the Walker Agent Connection

### Test Script to Run on Railway:

Create `/Users/cope/EnGardeHQ/Onside/scripts/test_railway_connections.py`:

```python
"""Test Railway service connections."""
import asyncio
import os
import sys
from sqlalchemy import create_engine, text
import redis

async def test_database():
    """Test database connection."""
    print("Testing Database Connection...")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return False

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✅ Database connected: {db_url[:30]}...")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def test_redis():
    """Test Redis connection."""
    print("\nTesting Redis Connection...")
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        print("❌ REDIS_URL not set")
        return False

    try:
        r = redis.from_url(redis_url)
        r.ping()
        print(f"✅ Redis connected: {redis_url[:30]}...")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

async def test_environment():
    """Test critical environment variables."""
    print("\nTesting Environment Variables...")

    required = [
        "DATABASE_URL",
        "REDIS_URL",
        "SECRET_KEY",
        "SERPAPI_KEY",
    ]

    optional = [
        "CELERY_BROKER_URL",
        "ALLOWED_ORIGINS",
        "APP_ENV",
    ]

    for var in required:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Set ({len(value)} chars)")
        else:
            print(f"❌ {var}: NOT SET (REQUIRED)")

    for var in optional:
        value = os.getenv(var)
        if value:
            print(f"ℹ️  {var}: Set ({len(value)} chars)")
        else:
            print(f"⚠️  {var}: Not set (optional)")

async def main():
    """Run all tests."""
    print("=" * 60)
    print("Railway Service Connection Tests")
    print("=" * 60)

    await test_environment()
    db_ok = await test_database()
    redis_ok = await test_redis()

    print("\n" + "=" * 60)
    if db_ok and redis_ok:
        print("✅ ALL CRITICAL SERVICES CONNECTED")
        sys.exit(0)
    else:
        print("❌ SOME SERVICES FAILED")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

**Run on Railway:**
```bash
railway run python scripts/test_railway_connections.py
```

## Configuration Files That Need Updates

### 1. `/Users/cope/EnGardeHQ/Onside/.env.production` (Create if missing)

```bash
# Railway Production Environment
APP_ENV=production
DEBUG=false

# Database - Set by Railway
DATABASE_URL=${DATABASE_URL}

# Redis - Set by Railway
REDIS_URL=${REDIS_URL}
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Security
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=https://onside-production.up.railway.app

# APIs
SERPAPI_KEY=${SERPAPI_KEY}

# Caching
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=300

# Celery
CELERY_TASK_TRACK_STARTED=true
CELERY_TASK_TIME_LIMIT=1800
```

### 2. `/Users/cope/EnGardeHQ/Onside/railway.json` (Update)

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 3. Create `railway-worker.json` for Celery Worker

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "celery -A src.celery_app worker --loglevel=info --concurrency=4 -Q default,reports,scraping,analytics,emails,data_ingestion",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## Summary of Required Actions

### Immediate (Do Today):
1. ✅ Log into Railway dashboard
2. ✅ Verify `DATABASE_URL` and `REDIS_URL` are auto-set
3. ✅ Manually set: `SECRET_KEY`, `SERPAPI_KEY`, `ALLOWED_ORIGINS`
4. ✅ Check Railway logs for connection errors
5. ✅ Run connection test script

### Short-term (This Week):
1. ⚠️ Deploy Celery worker service to Railway
2. ⚠️ Migrate walker agent from BackgroundTasks to Celery
3. ⚠️ Replace MinIO with S3 or Railway volumes
4. ⚠️ Add error monitoring (Sentry)

### Medium-term (This Month):
1. 📊 Add monitoring dashboard
2. 📊 Set up automated health checks
3. 📊 Configure alerting for failures
4. 📊 Document Railway deployment process

## Key Files Reference

### Configuration Files:
- `/Users/cope/EnGardeHQ/Onside/railway.json` - Main API config
- `/Users/cope/EnGardeHQ/Onside/.env.example` - Environment template
- `/Users/cope/EnGardeHQ/Onside/src/config.py` - Application settings
- `/Users/cope/EnGardeHQ/Onside/docker-compose.prod.yml` - Production docker config (NOT used on Railway)

### Walker Agent Files:
- `/Users/cope/EnGardeHQ/Onside/src/agents/seo_content_walker.py` - Main walker agent
- `/Users/cope/EnGardeHQ/Onside/src/api/v1/engarde.py` - API endpoints that trigger walker
- `/Users/cope/EnGardeHQ/Onside/src/services/serp_analyzer.py` - SERP analysis service (used by walker)

### Service Dependencies:
- `/Users/cope/EnGardeHQ/Onside/src/services/cache_service.py` - Redis cache
- `/Users/cope/EnGardeHQ/Onside/src/database/config.py` - Database connection
- `/Users/cope/EnGardeHQ/Onside/src/celery_app.py` - Celery configuration

## Next Steps

1. **Verify current Railway deployment status**
   ```bash
   railway status
   railway logs
   ```

2. **Check environment variables**
   ```bash
   railway variables
   ```

3. **Test a brand analysis request**
   ```bash
   curl -X POST https://onside-production.up.railway.app/api/v1/engarde/brand-analysis/initiate \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{
       "brand_name": "Test Brand",
       "primary_website": "https://example.com",
       "industry": "Technology"
     }'
   ```

4. **Monitor logs for errors**
   ```bash
   railway logs --tail
   ```

## Contact and Support

If you need assistance with any of these fixes, the critical issues to address first are:

1. Environment variable configuration in Railway dashboard
2. Database and Redis connection verification
3. Deploying Celery worker service
4. Testing the walker agent with proper connectivity

---

**Generated:** 2025-12-24
**Document Version:** 1.0
**Priority:** CRITICAL
