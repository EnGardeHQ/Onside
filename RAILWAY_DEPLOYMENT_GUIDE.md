# Railway Deployment Guide - Onside Platform

## Overview

This guide provides a complete walkthrough for deploying the Onside platform to Railway.app, including the main API service, Celery background workers, and all required infrastructure components.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (TL;DR)](#quick-start-tldr)
3. [Detailed Deployment Steps](#detailed-deployment-steps)
4. [Service Architecture](#service-architecture)
5. [Environment Variables](#environment-variables)
6. [Testing & Verification](#testing--verification)
7. [Post-Deployment Configuration](#post-deployment-configuration)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts & API Keys

Before starting deployment, ensure you have:

1. **Railway Account**
   - Sign up at https://railway.app
   - Connect your GitHub account

2. **GitHub Repository**
   - Onside repository access
   - Railway app authorized for the repo

3. **External API Keys** (get these first):
   - **SerpAPI:** https://serpapi.com/manage-api-key (required)
   - **OpenAI:** https://platform.openai.com/api-keys (required)
   - **Anthropic:** https://console.anthropic.com/settings/keys (required)
   - Google OAuth credentials (optional)
   - Other API keys as needed (see `.env.railway.example`)

4. **Railway CLI** (optional, but recommended):
   ```bash
   npm install -g @railway/cli
   railway login
   ```

---

## Quick Start (TL;DR)

For experienced users who want to deploy immediately:

```bash
# 1. Install Railway CLI
npm install -g @railway/cli
railway login

# 2. Create new project
railway init

# 3. Add PostgreSQL and Redis
railway add --database postgres
railway add --database redis

# 4. Set required environment variables
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set SERPAPI_KEY=your-key
railway variables set OPENAI_API_KEY=sk-proj-your-key
railway variables set ANTHROPIC_API_KEY=sk-ant-your-key
railway variables set ALLOWED_ORIGINS=https://your-frontend.railway.app

# 5. Deploy main API
railway up

# 6. Create Celery worker service (via dashboard)
# Railway Dashboard → New Service → Same Repo
# Set start command: celery -A src.celery_app worker --loglevel=info
# Copy all variables from API service

# 7. Verify
curl https://your-service.railway.app/health
```

For step-by-step instructions, continue reading.

---

## Detailed Deployment Steps

### Step 1: Create Railway Project

#### Via Railway Dashboard

1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your GitHub account
5. Select the Onside repository
6. Railway will auto-detect the Dockerfile and create a service

#### Via Railway CLI

```bash
# Navigate to Onside directory
cd /path/to/Onside

# Initialize Railway project
railway init

# Link to existing project (if already created)
railway link
```

### Step 2: Add Database Services

Railway provides managed PostgreSQL and Redis. Add them to your project:

#### Via Railway Dashboard

1. In your Railway project, click "New"
2. Select "Database" → "Add PostgreSQL"
3. Wait for provisioning (30-60 seconds)
4. Click "New" again
5. Select "Database" → "Add Redis"
6. Wait for provisioning

**Important:** Railway automatically creates and injects these environment variables:
- `DATABASE_URL` (PostgreSQL connection string)
- `REDIS_URL` (Redis connection string)

#### Via Railway CLI

```bash
railway add --database postgres
railway add --database redis
```

Verify they were added:

```bash
railway variables

# You should see:
# DATABASE_URL=postgresql://...
# REDIS_URL=redis://...
```

### Step 3: Configure Environment Variables

You have three options for setting environment variables:

#### Option A: Via Railway Dashboard (Recommended)

1. Click on your Onside service
2. Go to "Variables" tab
3. Click "Raw Editor"
4. Copy contents from `.env.railway.example`
5. Update placeholder values with actual credentials
6. Click "Save"

#### Option B: Via Railway CLI (Bulk Import)

```bash
# Copy .env.railway.example to .env.railway
cp .env.railway.example .env.railway

# Edit .env.railway with your actual values
nano .env.railway

# Import all variables
railway variables set $(cat .env.railway | grep -v '^#' | grep -v '^$')
```

#### Option C: Via Railway CLI (Individual Variables)

```bash
# Required variables
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set SERPAPI_KEY=your-serpapi-key
railway variables set OPENAI_API_KEY=sk-proj-your-openai-key
railway variables set ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
railway variables set ALLOWED_ORIGINS=https://your-frontend.railway.app

# Cache configuration
railway variables set CACHE_ENABLED=true
railway variables set CACHE_NAMESPACE=onside
railway variables set CACHE_DEFAULT_TTL=300

# Celery configuration (references Railway's REDIS_URL)
railway variables set CELERY_BROKER_URL='${REDIS_URL}'
railway variables set CELERY_RESULT_BACKEND='${REDIS_URL}'

# Add more as needed...
```

### Step 4: Deploy Main API Service

#### Via Railway Dashboard

Railway auto-deploys when you:
1. Connect the GitHub repo
2. Add environment variables
3. Click "Deploy" (or push to main branch)

Monitor deployment:
- Click "Deployments" tab
- View real-time build and deploy logs
- Check for errors

#### Via Railway CLI

```bash
# Deploy current directory
railway up

# Deploy specific service
railway up --service onside-api

# Follow logs
railway logs
```

### Step 5: Configure Custom Domain (Optional)

1. Go to service "Settings" → "Networking"
2. Under "Public Networking", you'll see Railway-generated domain
3. To add custom domain:
   - Click "Add Domain"
   - Enter your domain (e.g., `api.onside.com`)
   - Add CNAME record to your DNS:
     ```
     api.onside.com CNAME your-service.up.railway.app
     ```
4. Railway automatically provisions SSL certificate

### Step 6: Deploy Celery Worker Service

The Celery worker **must** be a separate service because:
- Railway services have request timeouts
- Long-running background tasks (5-15 min) need dedicated workers
- Worker can restart without affecting API availability

#### Create Worker Service (Dashboard Method)

1. In Railway project, click "New Service"
2. Select "GitHub Repo"
3. Choose **same repository** as API service
4. Name the service: `onside-celery-worker`
5. Railway will build using same Dockerfile

#### Configure Worker Service

1. Click new worker service → "Settings"
2. Under "Deploy", set **Start Command:**
   ```bash
   celery -A src.celery_app worker --loglevel=info --concurrency=4 -Q default,reports,scraping,analytics,emails,data_ingestion
   ```
3. Go to "Variables" tab
4. Click "Raw Editor"
5. **Copy ALL variables from API service**
   - Go to API service → Variables → Raw Editor → Copy
   - Go to Worker service → Variables → Raw Editor → Paste
6. Click "Save"

#### Add Service Dependencies

1. Worker service → "Settings" → "Service Dependencies"
2. Click "Add Dependency"
3. Add: PostgreSQL database
4. Add: Redis database
5. This ensures worker starts after databases are ready

#### Deploy Worker

1. Click "Deploy" or push to GitHub
2. Monitor logs for:
   ```
   [INFO/MainProcess] Connected to redis://...
   [INFO/MainProcess] celery@railway ready.
   [INFO/MainProcess] Listening to queues: default, reports, scraping, analytics, emails, data_ingestion
   ```

### Step 7: Deploy Celery Beat Scheduler (Optional)

For scheduled tasks (daily analytics, weekly reports):

1. Create new service: `onside-celery-beat`
2. Same repo, same Dockerfile
3. Start command:
   ```bash
   celery -A src.celery_app beat --loglevel=info
   ```
4. Copy all variables from API service
5. Add dependencies: Redis
6. Deploy

### Step 8: Deploy Flower Monitoring (Optional)

For task monitoring UI:

1. Create new service: `onside-flower`
2. Same repo, same Dockerfile
3. Start command:
   ```bash
   celery -A src.celery_app flower --port=${PORT:-5555} --basic_auth=${FLOWER_BASIC_AUTH}
   ```
4. Add environment variable:
   ```bash
   FLOWER_BASIC_AUTH=admin:your-secure-password
   ```
5. Copy all other variables from API service
6. Deploy
7. Access at generated Railway URL

---

## Service Architecture

After deployment, your Railway project should look like:

```
Railway Project: Onside Platform
│
├── PostgreSQL Database (managed by Railway)
│   └── Auto-generates: DATABASE_URL
│
├── Redis Database (managed by Railway)
│   └── Auto-generates: REDIS_URL
│
├── Service: onside-api
│   ├── Source: GitHub repo (main branch)
│   ├── Build: Dockerfile
│   ├── Start: uvicorn src.main:app --host 0.0.0.0 --port $PORT
│   ├── Public URL: https://onside-production.up.railway.app
│   ├── Health Check: /health
│   └── Dependencies: PostgreSQL, Redis
│
├── Service: onside-celery-worker
│   ├── Source: GitHub repo (same as API)
│   ├── Build: Dockerfile (same)
│   ├── Start: celery -A src.celery_app worker --loglevel=info
│   ├── Public URL: None (internal only)
│   └── Dependencies: PostgreSQL, Redis
│
├── Service: onside-celery-beat (optional)
│   ├── Source: GitHub repo (same as API)
│   ├── Build: Dockerfile (same)
│   ├── Start: celery -A src.celery_app beat --loglevel=info
│   └── Dependencies: Redis
│
└── Service: onside-flower (optional)
    ├── Source: GitHub repo (same as API)
    ├── Build: Dockerfile (same)
    ├── Start: celery -A src.celery_app flower --port=$PORT
    ├── Public URL: https://onside-flower-production.up.railway.app
    └── Dependencies: Redis
```

### Service Communication

Services communicate via Railway's internal network:

- **API ↔ Database:** Via `DATABASE_URL` (postgres.railway.internal)
- **API ↔ Redis:** Via `REDIS_URL` (redis.railway.internal)
- **Worker ↔ Redis:** Via `REDIS_URL` (same as API)
- **Worker ↔ Database:** Via `DATABASE_URL` (same as API)
- **External Clients ↔ API:** Via public Railway domain (HTTPS)

**Important:** Railway's internal networking is automatic. Services on the same project can communicate via `.railway.internal` domains.

---

## Environment Variables

### Complete Variable List

See `RAILWAY_ENV_SETUP.md` for detailed documentation on all environment variables.

### Required Variables (Minimum)

```bash
# Auto-generated by Railway (verify exist)
DATABASE_URL
REDIS_URL

# Must set manually
SECRET_KEY
SERPAPI_KEY
OPENAI_API_KEY
ANTHROPIC_API_KEY
ALLOWED_ORIGINS
```

### Variable References

Railway supports variable interpolation:

```bash
# Reference Railway's auto-generated REDIS_URL
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Reference custom PORT variable
APP_PORT=${PORT}
```

### Shared Variables Across Services

Best practice for multi-service deployments:

1. **Option A: Manual Copy-Paste**
   - Copy from API service → Variables → Raw Editor
   - Paste to Worker service → Variables → Raw Editor

2. **Option B: Use Railway Templates** (Advanced)
   - Create `railway.toml` with shared variables
   - Railway will inject into all services

3. **Option C: Environment Groups** (Railway Pro)
   - Create variable groups
   - Apply to multiple services

---

## Testing & Verification

### 1. Verify Service Health

```bash
# Replace with your actual Railway URL
export API_URL=https://onside-production.up.railway.app

# Test health endpoint
curl $API_URL/health

# Expected response:
# {"status":"healthy"}
```

### 2. Verify API Documentation

```bash
# Access OpenAPI docs
curl $API_URL/api/docs

# Should return HTML with Swagger UI
```

### 3. Verify Database Connection

Check Railway logs:

```bash
railway logs --service onside-api

# Look for:
# INFO:     Database connection established
# INFO:     Cache service initialized successfully
```

### 4. Verify Celery Worker

```bash
railway logs --service onside-celery-worker

# Look for:
# [INFO/MainProcess] Connected to redis://default:**@redis.railway.internal:6379//
# [INFO/MainProcess] celery@railway ready.
# [INFO/MainProcess] Listening to queues: default, reports, scraping, analytics, emails, data_ingestion
```

### 5. Test Background Task

Trigger a brand analysis job:

```bash
# Create brand analysis job
curl -X POST $API_URL/api/v1/engarde/brand-analysis/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "brand_name": "TestBrand",
    "website_url": "https://example.com",
    "industry": "Technology",
    "description": "Test brand for verification"
  }'

# Response will include job_id:
# {"job_id":"550e8400-e29b-41d4-a716-446655440000","status":"processing"}

# Check job status
curl $API_URL/api/v1/engarde/brand-analysis/550e8400-e29b-41d4-a716-446655440000/status
```

Check Celery worker logs for task execution:

```bash
railway logs --service onside-celery-worker

# Look for:
# [INFO/ForkPoolWorker-1] Task src.tasks.brand_analysis_task[550e8400-...] received
# [INFO/ForkPoolWorker-1] Starting brand analysis for TestBrand
```

### 6. Monitor with Flower (if deployed)

```bash
# Access Flower UI
open https://onside-flower-production.up.railway.app

# Login with credentials from FLOWER_BASIC_AUTH
# Username: admin
# Password: (your password)
```

Flower dashboard shows:
- Active workers
- Task success/failure rates
- Task execution times
- Queue lengths

---

## Post-Deployment Configuration

### 1. Configure CORS

Update `ALLOWED_ORIGINS` with your frontend domain:

```bash
railway variables set ALLOWED_ORIGINS=https://engarde-frontend.railway.app,https://onside-ui.com
```

Redeploy after changing:

```bash
railway redeploy --service onside-api
```

### 2. Set Up Monitoring

Enable Railway's built-in monitoring:

1. Go to service → "Observability"
2. View metrics:
   - CPU usage
   - Memory usage
   - Network traffic
   - Request rate

3. Set up alerts:
   - Service → "Settings" → "Alerts"
   - Configure email notifications for:
     - Deploy failures
     - High memory usage
     - Service crashes

### 3. Configure Logging

Railway automatically captures logs. Access them:

```bash
# View live logs
railway logs --service onside-api

# Filter logs
railway logs --service onside-api | grep ERROR

# Export logs
railway logs --service onside-api > logs.txt
```

Increase log verbosity for debugging:

```bash
railway variables set LOG_LEVEL=DEBUG
```

### 4. Database Backups

Railway Pro includes automatic PostgreSQL backups.

Manual backup:

```bash
# Get database credentials
railway variables | grep DATABASE_URL

# Use pg_dump
pg_dump "$(railway variables get DATABASE_URL)" > backup.sql
```

### 5. Environment-Specific Configuration

Create separate Railway projects for:
- **Development:** `onside-dev`
- **Staging:** `onside-staging`
- **Production:** `onside-production`

Use different environment variables per project:

```bash
# Development
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# Production
LOG_LEVEL=WARNING
ENVIRONMENT=production
```

---

## Troubleshooting

### Issue 1: Build Failed

**Symptom:**
```
Railway build failed: Error building Docker image
```

**Solutions:**

1. Check Dockerfile exists in repo root
2. Verify requirements.txt syntax
3. Check Railway build logs:
   - Service → "Deployments" → Failed deployment → View logs
4. Test build locally:
   ```bash
   docker build -t onside-test .
   ```

### Issue 2: Service Crashed After Deploy

**Symptom:**
```
Service is unhealthy - no response from health check
```

**Solutions:**

1. Check logs for errors:
   ```bash
   railway logs --service onside-api | tail -100
   ```

2. Common causes:
   - Missing environment variable
   - Database connection failed
   - Port binding issue

3. Verify health endpoint:
   ```bash
   # Check if /health route exists
   curl https://your-service.railway.app/health -v
   ```

4. Check PORT variable:
   ```bash
   # Railway injects PORT variable
   # Make sure your app uses it:
   railway variables | grep PORT
   ```

### Issue 3: Database Connection Error

**Symptom:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solutions:**

1. Verify PostgreSQL addon is added:
   - Railway Dashboard → Your Project → Check for PostgreSQL card

2. Verify DATABASE_URL exists:
   ```bash
   railway variables | grep DATABASE_URL
   ```

3. Check service dependencies:
   - Service → Settings → Service Dependencies
   - Add PostgreSQL if missing

4. Verify connection format:
   ```bash
   # Railway's DATABASE_URL format:
   postgresql://user:password@postgres.railway.internal:5432/railway

   # Must start with postgresql:// (not postgres://)
   ```

### Issue 4: Redis Connection Error

**Symptom:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solutions:**

1. Verify Redis addon added
2. Check REDIS_URL:
   ```bash
   railway variables | grep REDIS_URL
   ```

3. Verify CELERY_BROKER_URL references REDIS_URL:
   ```bash
   railway variables set CELERY_BROKER_URL='${REDIS_URL}'
   ```

### Issue 5: Celery Tasks Not Processing

**Symptom:**
- Tasks created but never execute
- Worker logs show no activity

**Solutions:**

1. Verify worker service is running:
   ```bash
   railway status --service onside-celery-worker
   ```

2. Check worker has same REDIS_URL as API:
   ```bash
   # Compare
   railway variables --service onside-api | grep REDIS_URL
   railway variables --service onside-celery-worker | grep REDIS_URL
   ```

3. Verify queue names match:
   - Worker start command includes: `-Q default,reports,scraping,...`
   - Task routes in `src/celery_app.py` use same queue names

4. Check for errors in worker logs:
   ```bash
   railway logs --service onside-celery-worker | grep ERROR
   ```

### Issue 6: CORS Errors

**Symptom:**
```
Access-Control-Allow-Origin header missing
```

**Solutions:**

1. Update ALLOWED_ORIGINS:
   ```bash
   railway variables set ALLOWED_ORIGINS=https://your-frontend.railway.app
   ```

2. Verify CORS middleware in code:
   ```python
   # src/main.py should have:
   app.add_middleware(
       CORSMiddleware,
       allow_origins=config.allowed_origins,
       ...
   )
   ```

3. Redeploy after changing:
   ```bash
   railway redeploy --service onside-api
   ```

### Issue 7: Environment Variables Not Loading

**Symptom:**
- Variable set in dashboard but app doesn't see it

**Solutions:**

1. Railway requires full redeploy after variable changes:
   ```bash
   railway redeploy --service onside-api
   ```

2. Don't use "Restart" - use "Redeploy"

3. Verify variable name matches code (case-sensitive)

4. Check for typos:
   ```bash
   railway variables | grep SECRET_KEY
   ```

### Issue 8: Out of Memory

**Symptom:**
```
Railway service exceeded memory limit
```

**Solutions:**

1. Upgrade Railway plan for more memory

2. Reduce worker concurrency:
   ```bash
   # Change from --concurrency=4 to --concurrency=2
   celery -A src.celery_app worker --concurrency=2
   ```

3. Enable memory tracking:
   ```bash
   railway variables set ENABLE_MEMORY_TRACKING=true
   ```

4. Monitor memory usage:
   - Service → "Observability" → "Memory"

---

## Railway CLI Reference

### Essential Commands

```bash
# Install CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to existing project
railway link

# Deploy
railway up

# View logs
railway logs
railway logs --service onside-api
railway logs --follow

# Manage variables
railway variables
railway variables set KEY=value
railway variables get KEY
railway variables delete KEY

# Service management
railway status
railway redeploy
railway restart

# Connect to database
railway connect postgres
railway connect redis

# Run commands in Railway environment
railway run python manage.py migrate
railway run celery -A src.celery_app inspect active

# Open service in browser
railway open
```

---

## Deployment Checklist

Use this before going to production:

### Pre-Deployment
- [ ] All API keys obtained (SerpAPI, OpenAI, Anthropic)
- [ ] SECRET_KEY generated (unique, random, 32+ chars)
- [ ] Frontend domain configured
- [ ] Railway account set up
- [ ] GitHub repo connected to Railway

### Infrastructure
- [ ] PostgreSQL addon added
- [ ] Redis addon added
- [ ] DATABASE_URL auto-generated and verified
- [ ] REDIS_URL auto-generated and verified

### Main API Service
- [ ] Service created from GitHub repo
- [ ] All environment variables set (see `.env.railway.example`)
- [ ] ALLOWED_ORIGINS updated with frontend domain
- [ ] Service deployed successfully
- [ ] Health check passing: `/health` returns 200
- [ ] API docs accessible: `/api/docs`

### Celery Worker Service
- [ ] Worker service created (same repo as API)
- [ ] Start command set correctly
- [ ] All variables copied from API service
- [ ] Service dependencies added (PostgreSQL, Redis)
- [ ] Worker deployed and showing "ready" in logs
- [ ] Test task executed successfully

### Optional Services
- [ ] Celery Beat deployed (if using scheduled tasks)
- [ ] Flower deployed (if monitoring tasks)
- [ ] Custom domain configured (if needed)

### Testing
- [ ] `/health` endpoint returns healthy
- [ ] `/api/docs` accessible
- [ ] Database connection verified in logs
- [ ] Redis connection verified in logs
- [ ] Test API request succeeds
- [ ] Test background task executes
- [ ] CORS working from frontend
- [ ] Error logging working

### Security
- [ ] SECRET_KEY is unique (not default)
- [ ] No sensitive data in GitHub repo
- [ ] `.env` file in `.gitignore`
- [ ] FLOWER_BASIC_AUTH set (if using Flower)
- [ ] ALLOWED_ORIGINS restricted to actual domains

### Monitoring
- [ ] Railway alerts configured
- [ ] Log level appropriate (INFO for prod)
- [ ] Flower accessible (if deployed)
- [ ] Health checks configured
- [ ] Database backup strategy in place

---

## Next Steps

After successful deployment:

1. **Monitor Performance**
   - Watch Railway metrics
   - Check Celery task execution times
   - Monitor database query performance

2. **Set Up CI/CD**
   - Railway auto-deploys on git push
   - Configure branch protection
   - Add automated tests before deploy

3. **Scale as Needed**
   - Increase worker concurrency
   - Add more worker instances
   - Upgrade Railway plan

4. **Documentation**
   - Document your specific Railway URLs
   - Create runbooks for common issues
   - Train team on Railway dashboard

5. **Backup & Recovery**
   - Set up automated database backups
   - Test restore procedures
   - Document disaster recovery plan

---

## Support Resources

- **Railway Documentation:** https://docs.railway.app
- **Railway Community:** https://discord.gg/railway
- **Railway Status:** https://status.railway.app
- **Onside Documentation:** See `docs/` directory
- **Celery Documentation:** https://docs.celeryq.dev

---

**Last Updated:** 2024-12-24
**Railway CLI Version:** 3.x
**Onside Version:** See `requirements.txt`
