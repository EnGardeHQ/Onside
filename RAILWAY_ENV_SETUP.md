# Railway Environment Variables Setup Guide

## Overview

This guide provides step-by-step instructions for configuring environment variables for the Onside service on Railway. The Onside platform requires proper configuration of database connections, external API keys, service integrations, and security settings.

---

## Table of Contents

1. [Quick Start Checklist](#quick-start-checklist)
2. [Railway Dashboard Setup](#railway-dashboard-setup)
3. [Environment Variables Reference](#environment-variables-reference)
4. [Celery Worker Deployment](#celery-worker-deployment)
5. [Testing & Verification](#testing--verification)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start Checklist

Before deploying to Railway, ensure you have:

- [ ] Railway account with project created
- [ ] GitHub repository connected to Railway
- [ ] SerpAPI key (https://serpapi.com/manage-api-key)
- [ ] OpenAI API key (https://platform.openai.com/api-keys)
- [ ] Anthropic API key (https://console.anthropic.com/settings/keys)
- [ ] Google OAuth credentials (optional, for analytics)
- [ ] Generated SECRET_KEY (use: `openssl rand -hex 32`)

---

## Railway Dashboard Setup

### Step 1: Access Railway Dashboard

1. Log into Railway at https://railway.app
2. Navigate to your project
3. Select the Onside service (or create new service from GitHub repo)

### Step 2: Add Railway Addons

Railway automatically provisions these services with environment variables:

#### PostgreSQL Database

1. Click "New" → "Database" → "Add PostgreSQL"
2. Railway automatically sets: `DATABASE_URL`
3. **Format:** `postgresql://user:password@host:port/database`
4. **No manual configuration needed**

#### Redis Cache

1. Click "New" → "Database" → "Add Redis"
2. Railway automatically sets: `REDIS_URL`
3. **Format:** `redis://user:password@host:port`
4. **No manual configuration needed**

### Step 3: Configure Environment Variables

Click on your Onside service → "Variables" tab → "Raw Editor"

Copy the template from [.env.railway.example](#envrailwayexample) and update with your values.

### Step 4: Deploy

After setting variables:
1. Click "Deploy" or push to connected GitHub branch
2. Railway will rebuild with new environment variables
3. Monitor logs in "Deployments" tab

---

## Environment Variables Reference

### Category 1: Auto-Provisioned by Railway (Read-Only)

These are automatically set when you add Railway addons:

```bash
# PostgreSQL - Auto-set by Railway PostgreSQL addon
DATABASE_URL=postgresql://postgres:password@postgres.railway.internal:5432/railway

# Redis - Auto-set by Railway Redis addon
REDIS_URL=redis://default:password@redis.railway.internal:6379
```

**Action Required:** None. Verify they exist in Variables tab.

---

### Category 2: Application Core Settings (Required)

```bash
# Application Environment
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
APP_WORKERS=4

# Security (CRITICAL - Generate unique value)
# Generate with: openssl rand -hex 32
SECRET_KEY=your-generated-secret-key-here-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS Configuration
# Add your frontend domains (comma-separated)
ALLOWED_ORIGINS=https://your-frontend-domain.com,https://engarde-production.up.railway.app
```

**How to Set:**
1. Generate SECRET_KEY: Run `openssl rand -hex 32` locally
2. Update ALLOWED_ORIGINS with your actual frontend URL
3. Keep other values as-is for production

---

### Category 3: Redis/Cache Configuration (Required)

```bash
# Cache Settings
CACHE_ENABLED=true
CACHE_NAMESPACE=onside
CACHE_DEFAULT_TTL=300

# Cache TTL per data type (seconds)
CACHE_TTL_SERP_RESULTS=86400
CACHE_TTL_WEBSITE_CRAWL=3600
CACHE_TTL_KEYWORD_DATA=604800
CACHE_TTL_API_RESPONSE=300
CACHE_TTL_ANALYTICS=1800
CACHE_TTL_SCRAPED_CONTENT=3600

# Legacy Redis Config (optional - REDIS_URL takes precedence)
REDIS_HOST=redis.railway.internal
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

**Action Required:** Copy these values as-is. Railway's REDIS_URL will override individual settings.

---

### Category 4: Celery Configuration (Required for Background Tasks)

```bash
# Celery Task Queue
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
CELERY_TASK_TRACK_STARTED=true
CELERY_TASK_TIME_LIMIT=1800
CELERY_TASK_SOFT_TIME_LIMIT=1500
```

**Action Required:**
- In Railway, `${REDIS_URL}` automatically references the Redis addon URL
- Copy these values as-is

---

### Category 5: External API Keys (Required)

#### SerpAPI (Required for SERP Analysis)

```bash
SERPAPI_KEY=your-serpapi-key-here
```

**How to Get:**
1. Sign up at https://serpapi.com/
2. Go to https://serpapi.com/manage-api-key
3. Copy your API key
4. Free tier: 100 searches/month

#### AI Service Keys (Required for Analysis)

```bash
# OpenAI
OPENAI_API_KEY=sk-proj-...your-key-here
OPENAI_MODEL=gpt-4

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...your-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# AI Fallback Settings
ENABLE_AI_FALLBACK=true
MAX_RETRY_ATTEMPTS=3
```

**How to Get:**
- **OpenAI:** https://platform.openai.com/api-keys
- **Anthropic:** https://console.anthropic.com/settings/keys

---

### Category 6: Optional External APIs

These enhance functionality but are not required for basic operation:

```bash
# Google OAuth (for Analytics integration)
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=https://your-domain.railway.app/api/v1/analytics/auth/callback
GOOGLE_ANALYTICS_VIEW_ID=

# SEMrush (alternative to SerpAPI)
SEMRUSH_API_KEY=

# GNews API
GNEWS_API_KEY=
GNEWS_DAILY_QUOTA=1000

# IPInfo API
IPINFO_API_KEY=

# WhoAPI
WHOAPI_API_KEY=
WHOAPI_BASE_URL=https://api.whoapi.com
WHOAPI_TIMEOUT=30
WHOAPI_MAX_RETRIES=3

# Meltwater
MELTWATER_API_KEY=
MELTWATER_BASE_URL=https://api.meltwater.com/v3
MELTWATER_API_RATE_LIMIT=100
```

**Action Required:** Only add if you have accounts for these services.

---

### Category 7: MinIO Object Storage (Optional)

If using MinIO for file storage:

```bash
MINIO_ENDPOINT=minio.railway.internal:9000
MINIO_ACCESS_KEY=your-minio-access-key
MINIO_SECRET_KEY=your-minio-secret-key
MINIO_SECURE=false
MINIO_REGION=us-east-1
```

**Action Required:** Only set if deploying MinIO service on Railway.

---

### Category 8: EnGarde Integration (Required if using En Garde)

```bash
# En Garde Backend API URL
ENGARDE_API_URL=https://engarde-backend-production.up.railway.app

# Campaign Space Integration
ENABLE_CAMPAIGN_SPACE_INTEGRATION=true
```

**Action Required:** Update ENGARDE_API_URL with actual En Garde backend Railway URL.

---

### Category 9: Performance & Monitoring

```bash
# Performance Monitoring
ENABLE_PERFORMANCE_MONITORING=true
SLOW_REQUEST_THRESHOLD=1.0
ENABLE_MEMORY_TRACKING=true
LOG_LEVEL=INFO

# Rate Limiting
ENABLE_RATE_LIMITING=true
DEFAULT_RATE_LIMIT_REQUESTS=100
DEFAULT_RATE_LIMIT_WINDOW=60
```

**Action Required:** Copy as-is. Adjust LOG_LEVEL to DEBUG for troubleshooting.

---

### Category 10: Analysis Configuration

```bash
# AI Analysis Thresholds
COMPETITOR_ANALYSIS_CONFIDENCE_THRESHOLD=0.85
MARKET_ANALYSIS_CONFIDENCE_THRESHOLD=0.85
AUDIENCE_ANALYSIS_CONFIDENCE_THRESHOLD=0.85

# Chain of Thought
ENABLE_CHAIN_OF_THOUGHT=true
COT_DETAIL_LEVEL=comprehensive

# Web Scraping
SCRAPER_USER_AGENT=Mozilla/5.0 (compatible; OnSideBot/1.0; +https://onside.ai)
SCRAPER_TIMEOUT=30
SCRAPER_MAX_RETRIES=3
SCRAPER_RETRY_DELAY=5
```

**Action Required:** Copy as-is.

---

## Celery Worker Deployment

The Onside platform requires a separate Celery worker service for background task processing. This handles long-running operations like:

- Brand analysis workflows (5-15 minutes)
- Web scraping batch jobs
- Report generation
- SERP data collection
- Scheduled analytics

### Why Separate Celery Worker?

Railway services have request timeouts. Long-running tasks in the main API service will fail. Celery workers:
- Run tasks asynchronously
- Survive across API restarts
- Provide task monitoring via Flower
- Support retry logic and error handling

---

### Deployment Steps

#### Step 1: Create New Service in Railway

1. In Railway project dashboard, click "New Service"
2. Select "GitHub Repo"
3. Choose the **same repository** as your Onside API service
4. Name it: `onside-celery-worker`

#### Step 2: Configure Build Settings

1. Click the new service → "Settings" tab
2. Under "Build":
   - **Builder:** Dockerfile
   - **Dockerfile Path:** `Dockerfile`
   - **Build Command:** (leave empty)

#### Step 3: Set Start Command

1. In "Settings" → "Deploy"
2. Set **Start Command:**
   ```bash
   celery -A src.celery_app worker --loglevel=info --concurrency=4 -Q default,reports,scraping,analytics,emails,data_ingestion
   ```

**Command Breakdown:**
- `-A src.celery_app` - Application module
- `worker` - Run as worker process
- `--loglevel=info` - Log verbosity
- `--concurrency=4` - Number of worker processes (adjust based on Railway plan)
- `-Q default,reports,...` - Queues to listen to

#### Step 4: Copy Environment Variables

**IMPORTANT:** The Celery worker needs the same environment variables as the API service.

**Method 1: Via Railway Dashboard**

1. Go to main Onside API service → "Variables" tab
2. Click "Raw Editor" → Copy all variables
3. Go to Celery worker service → "Variables" tab
4. Click "Raw Editor" → Paste
5. Click "Save"

**Method 2: Via Railway CLI**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Copy variables from API to worker (requires manual scripting)
# Recommended: Use dashboard method
```

**Critical Variables for Celery Worker:**

```bash
# Redis (for task queue)
REDIS_URL=redis://...
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Database (for task persistence)
DATABASE_URL=postgresql://...

# API Keys (for tasks that call external services)
SERPAPI_KEY=...
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...

# Cache
CACHE_ENABLED=true
CACHE_NAMESPACE=onside

# All other variables from main service
```

#### Step 5: Add Service Dependencies

1. In Celery worker service → "Settings" tab
2. Under "Service Dependencies"
3. Add: PostgreSQL addon, Redis addon (same as API service)
4. Railway will automatically inject DATABASE_URL and REDIS_URL

#### Step 6: Deploy

1. Click "Deploy" in Celery worker service
2. Monitor logs: You should see:
   ```
   [2024-12-24 20:00:00,000: INFO/MainProcess] Connected to redis://...
   [2024-12-24 20:00:00,100: INFO/MainProcess] celery@worker ready
   [2024-12-24 20:00:00,200: INFO/MainProcess] Listening to queues: default, reports, scraping, analytics, emails, data_ingestion
   ```

---

### Optional: Deploy Celery Beat Scheduler

For scheduled tasks (daily analytics, weekly reports):

#### Create Third Service: `onside-celery-beat`

1. Same repo, same Dockerfile
2. Start command:
   ```bash
   celery -A src.celery_app beat --loglevel=info
   ```
3. Copy same environment variables
4. Deploy

---

### Optional: Deploy Flower Monitoring

For task monitoring dashboard:

#### Create Fourth Service: `onside-flower`

1. Same repo, same Dockerfile
2. Start command:
   ```bash
   celery -A src.celery_app flower --port=5555
   ```
3. Copy same environment variables
4. Add environment variable:
   ```bash
   FLOWER_PORT=5555
   FLOWER_BASIC_AUTH=admin:your-secure-password
   ```
5. Deploy
6. Access at: `https://onside-flower-production.up.railway.app`

---

## .env.railway.example

Create this file in your repository for reference:

```bash
# =============================================================================
# Railway Environment Configuration for Onside Platform
# =============================================================================
# This file is a template for Railway environment variables
# DO NOT commit actual values - use Railway dashboard to set variables
# =============================================================================

# -----------------------------------------------------------------------------
# AUTO-PROVISIONED BY RAILWAY (verify these exist)
# -----------------------------------------------------------------------------
# DATABASE_URL=postgresql://...  (set by PostgreSQL addon)
# REDIS_URL=redis://...          (set by Redis addon)

# -----------------------------------------------------------------------------
# APPLICATION CORE
# -----------------------------------------------------------------------------
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
APP_WORKERS=4

# -----------------------------------------------------------------------------
# SECURITY (CRITICAL - GENERATE UNIQUE VALUES)
# -----------------------------------------------------------------------------
# Generate with: openssl rand -hex 32
SECRET_KEY=CHANGE_THIS_TO_RANDOM_VALUE
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# -----------------------------------------------------------------------------
# CORS CONFIGURATION
# -----------------------------------------------------------------------------
# Update with your actual frontend domains
ALLOWED_ORIGINS=https://your-frontend-domain.railway.app,https://engarde-frontend.railway.app

# -----------------------------------------------------------------------------
# CACHE CONFIGURATION
# -----------------------------------------------------------------------------
CACHE_ENABLED=true
CACHE_NAMESPACE=onside
CACHE_DEFAULT_TTL=300
CACHE_TTL_SERP_RESULTS=86400
CACHE_TTL_WEBSITE_CRAWL=3600
CACHE_TTL_KEYWORD_DATA=604800
CACHE_TTL_API_RESPONSE=300
CACHE_TTL_ANALYTICS=1800
CACHE_TTL_SCRAPED_CONTENT=3600

# Legacy Redis config (REDIS_URL takes precedence)
REDIS_HOST=redis.railway.internal
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# -----------------------------------------------------------------------------
# CELERY CONFIGURATION
# -----------------------------------------------------------------------------
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
CELERY_TASK_TRACK_STARTED=true
CELERY_TASK_TIME_LIMIT=1800
CELERY_TASK_SOFT_TIME_LIMIT=1500

# -----------------------------------------------------------------------------
# EXTERNAL API KEYS (REQUIRED)
# -----------------------------------------------------------------------------
# SerpAPI - https://serpapi.com/manage-api-key
SERPAPI_KEY=your-serpapi-key

# OpenAI - https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-your-key
OPENAI_MODEL=gpt-4

# Anthropic - https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# AI Fallback
ENABLE_AI_FALLBACK=true
MAX_RETRY_ATTEMPTS=3

# -----------------------------------------------------------------------------
# OPTIONAL EXTERNAL APIs
# -----------------------------------------------------------------------------
# Google OAuth (for Analytics)
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
GOOGLE_OAUTH_REDIRECT_URI=
GOOGLE_ANALYTICS_VIEW_ID=

# SEMrush
SEMRUSH_API_KEY=

# Additional APIs
GNEWS_API_KEY=
IPINFO_API_KEY=
WHOAPI_API_KEY=
MELTWATER_API_KEY=

# -----------------------------------------------------------------------------
# ENGARDE INTEGRATION
# -----------------------------------------------------------------------------
# Update with actual En Garde backend URL
ENGARDE_API_URL=https://engarde-backend-production.railway.app
ENABLE_CAMPAIGN_SPACE_INTEGRATION=true

# -----------------------------------------------------------------------------
# PERFORMANCE & MONITORING
# -----------------------------------------------------------------------------
ENABLE_PERFORMANCE_MONITORING=true
SLOW_REQUEST_THRESHOLD=1.0
ENABLE_MEMORY_TRACKING=true
LOG_LEVEL=INFO
ENABLE_RATE_LIMITING=true
DEFAULT_RATE_LIMIT_REQUESTS=100
DEFAULT_RATE_LIMIT_WINDOW=60

# -----------------------------------------------------------------------------
# ANALYSIS CONFIGURATION
# -----------------------------------------------------------------------------
COMPETITOR_ANALYSIS_CONFIDENCE_THRESHOLD=0.85
MARKET_ANALYSIS_CONFIDENCE_THRESHOLD=0.85
AUDIENCE_ANALYSIS_CONFIDENCE_THRESHOLD=0.85
ENABLE_CHAIN_OF_THOUGHT=true
COT_DETAIL_LEVEL=comprehensive

# -----------------------------------------------------------------------------
# WEB SCRAPING SETTINGS
# -----------------------------------------------------------------------------
SCRAPER_USER_AGENT=Mozilla/5.0 (compatible; OnSideBot/1.0; +https://onside.ai)
SCRAPER_TIMEOUT=30
SCRAPER_MAX_RETRIES=3
SCRAPER_RETRY_DELAY=5

# -----------------------------------------------------------------------------
# MINIO OBJECT STORAGE (Optional)
# -----------------------------------------------------------------------------
MINIO_ENDPOINT=minio.railway.internal:9000
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
MINIO_SECURE=false
MINIO_REGION=us-east-1
```

---

## Testing & Verification

### 1. Verify Service Health

After deployment, test the health endpoint:

```bash
# Replace with your actual Railway URL
curl https://onside-production.up.railway.app/health

# Expected response:
# {"status":"healthy"}
```

### 2. Verify Database Connection

Check logs for successful database connection:

```
INFO:     Database connection established
INFO:     Cache service initialized successfully
```

### 3. Verify Environment Variables

In Railway dashboard:

1. Service → "Variables" tab
2. Verify all required variables are set
3. Check for Railway warnings (yellow triangles)

### 4. Test API Endpoints

```bash
# Test API docs
curl https://onside-production.up.railway.app/api/docs

# Should return OpenAPI documentation HTML
```

### 5. Verify Celery Worker

Check Celery worker logs:

```
[INFO/MainProcess] Connected to redis://default:**@redis.railway.internal:6379//
[INFO/MainProcess] mingle: searching for neighbors
[INFO/MainProcess] mingle: all alone
[INFO/MainProcess] celery@railway ready.
```

### 6. Test Background Task

Trigger a brand analysis and verify it runs in Celery:

```bash
curl -X POST https://onside-production.up.railway.app/api/v1/engarde/brand-analysis/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "brand_name": "TestBrand",
    "website_url": "https://example.com",
    "industry": "Technology"
  }'
```

Check Celery worker logs for task execution.

### 7. Monitor with Flower (if deployed)

Visit: `https://onside-flower-production.up.railway.app`

You should see:
- Active workers
- Task history
- Success/failure rates

---

## Troubleshooting

### Issue 1: Database Connection Failed

**Symptom:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**Solution:**
1. Verify PostgreSQL addon is added to project
2. Check `DATABASE_URL` is set in Variables tab
3. Ensure service has dependency on PostgreSQL addon
4. Restart service after adding addon

### Issue 2: Redis Connection Failed

**Symptom:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution:**
1. Verify Redis addon is added to project
2. Check `REDIS_URL` is set in Variables tab
3. Ensure `CELERY_BROKER_URL=${REDIS_URL}` references it
4. Check Redis addon is running (Railway dashboard)

### Issue 3: SERPAPI_KEY Not Set

**Symptom:**
```
ValueError: SERPAPI_KEY environment variable is required
```

**Solution:**
1. Add `SERPAPI_KEY=your-key` to Railway variables
2. Get key from https://serpapi.com/manage-api-key
3. Redeploy service

### Issue 4: CORS Errors from Frontend

**Symptom:**
```
Access to fetch at 'https://onside.railway.app' from origin 'https://frontend.com' has been blocked by CORS policy
```

**Solution:**
1. Update `ALLOWED_ORIGINS` in Railway variables
2. Add frontend domain: `ALLOWED_ORIGINS=https://your-frontend.railway.app`
3. Multiple origins: `ALLOWED_ORIGINS=https://domain1.com,https://domain2.com`
4. Redeploy

### Issue 5: Celery Tasks Not Processing

**Symptom:**
- Tasks queued but not executing
- Worker logs show no activity

**Solution:**
1. Verify Celery worker service is running
2. Check worker has same `REDIS_URL` as API service
3. Verify worker start command includes all queues:
   ```
   celery -A src.celery_app worker --loglevel=info -Q default,reports,scraping,analytics,emails,data_ingestion
   ```
4. Check for errors in worker logs

### Issue 6: 500 Internal Server Error

**Symptom:**
```
{"detail":"Internal Server Error"}
```

**Solution:**
1. Check Railway logs: Service → "Deployments" → Click latest deployment
2. Look for Python stack traces
3. Common causes:
   - Missing environment variable
   - Database migration not run
   - Invalid API key
4. Set `LOG_LEVEL=DEBUG` for detailed logs

### Issue 7: Build Failure

**Symptom:**
```
Railway build failed
```

**Solution:**
1. Check build logs in Railway dashboard
2. Verify Dockerfile exists in repo root
3. Check requirements.txt syntax
4. Verify Railway has access to GitHub repo
5. Try manual rebuild: Service → "Settings" → "Redeploy"

### Issue 8: Environment Variable Not Loading

**Symptom:**
- Variable set in dashboard but app doesn't see it

**Solution:**
1. Railway requires **full redeploy** after variable changes
2. Don't just restart - click "Redeploy"
3. Or push new commit to trigger rebuild
4. Verify variable name matches exactly (case-sensitive)

---

## Railway Service Architecture Summary

After full deployment, you should have:

```
Railway Project: Onside Platform
├── Service: onside-api
│   ├── Start Command: uvicorn src.main:app --host 0.0.0.0 --port 8000
│   ├── Public URL: https://onside-production.up.railway.app
│   └── Dependencies: PostgreSQL, Redis
│
├── Service: onside-celery-worker
│   ├── Start Command: celery -A src.celery_app worker --loglevel=info
│   ├── No public URL (internal only)
│   └── Dependencies: PostgreSQL, Redis
│
├── Service: onside-celery-beat (optional)
│   ├── Start Command: celery -A src.celery_app beat --loglevel=info
│   └── Dependencies: Redis
│
├── Service: onside-flower (optional)
│   ├── Start Command: celery -A src.celery_app flower --port=5555
│   ├── Public URL: https://onside-flower-production.up.railway.app
│   └── Dependencies: Redis
│
├── Database: PostgreSQL
│   └── Auto-generates DATABASE_URL
│
└── Database: Redis
    └── Auto-generates REDIS_URL
```

---

## Quick Deployment Checklist

Use this checklist when deploying:

- [ ] PostgreSQL addon added
- [ ] Redis addon added
- [ ] `DATABASE_URL` auto-set and verified
- [ ] `REDIS_URL` auto-set and verified
- [ ] `SECRET_KEY` generated and set (unique random value)
- [ ] `SERPAPI_KEY` set (from serpapi.com)
- [ ] `OPENAI_API_KEY` set (from OpenAI)
- [ ] `ANTHROPIC_API_KEY` set (from Anthropic)
- [ ] `ALLOWED_ORIGINS` updated with frontend URL
- [ ] `ENGARDE_API_URL` updated (if using En Garde)
- [ ] All cache TTL variables copied
- [ ] Celery configuration copied
- [ ] Main API service deployed and healthy
- [ ] Celery worker service created with same variables
- [ ] Celery worker deployed and shows "ready" in logs
- [ ] Health endpoint returns 200 OK
- [ ] API docs accessible at /api/docs
- [ ] Test brand analysis job completes successfully

---

## Support & Resources

- **Railway Documentation:** https://docs.railway.app
- **Railway CLI:** https://docs.railway.app/develop/cli
- **SerpAPI Docs:** https://serpapi.com/docs
- **Celery Documentation:** https://docs.celeryq.dev
- **FastAPI Deployment:** https://fastapi.tiangolo.com/deployment/

---

**Last Updated:** 2024-12-24
**Platform:** Railway
**Service:** Onside Analytics Platform
