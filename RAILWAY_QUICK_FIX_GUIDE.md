# Railway Quick Fix Guide: Walker Agent Connectivity

**Priority:** CRITICAL
**Time to Fix:** 15-30 minutes
**Difficulty:** Easy to Medium

## Problem Summary

Walker agents deployed to Railway cannot connect because:
1. Environment variables use Docker Compose service names (wrong)
2. Missing critical API keys
3. No Celery worker service deployed
4. Walker agents use FastAPI BackgroundTasks (not persistent)

## Quick Fix Steps

### Step 1: Access Railway Dashboard (2 min)

1. Go to https://railway.app
2. Log in to your account
3. Select the OnSide project
4. You should see services deployed

### Step 2: Check Current Environment Variables (3 min)

Click on your main API service, then go to "Variables" tab.

**Verify these are AUTO-SET by Railway:**
- `DATABASE_URL` - Should start with `postgresql://`
- `REDIS_URL` - Should start with `redis://`

If missing:
1. Go to project root
2. Click "New" → "Database" → "Add PostgreSQL"
3. Click "New" → "Database" → "Add Redis"
4. Railway will auto-set these variables

### Step 3: Set Required Variables (5 min)

In the Variables tab, add these if missing:

```bash
# Critical - Generate a random string
SECRET_KEY=<paste-random-64-char-string>

# Critical - Your SerpAPI key
SERPAPI_KEY=<your-serpapi-key-from-serpapi.com>

# Important - Your frontend URL
ALLOWED_ORIGINS=https://onside-production.up.railway.app

# Environment
APP_ENV=production
CACHE_ENABLED=true

# Celery Configuration
CELERY_BROKER_URL=${{REDIS_URL}}
CELERY_RESULT_BACKEND=${{REDIS_URL}}
```

**To generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**To get SERPAPI_KEY:**
1. Go to https://serpapi.com
2. Sign up for account
3. Get API key from dashboard

### Step 4: Verify Configuration (2 min)

Click "Deploy" to restart the service with new variables.

Wait for deployment to complete (green checkmark).

### Step 5: Test Connections (5 min)

From your local terminal:

```bash
# Install Railway CLI if not installed
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run connection test
railway run python scripts/test_railway_connections.py
```

Expected output:
```
✅ ALL TESTS PASSED - Services are properly connected
```

If you see failures, check the specific error messages.

### Step 6: Deploy Celery Worker Service (10 min)

**IMPORTANT:** Walker agents need a separate Celery worker to run properly.

#### Option A: Via Railway Dashboard (Recommended)

1. In Railway dashboard, click "New" → "Empty Service"
2. Name it `onside-celery-worker`
3. Under "Settings" → "Source":
   - Connect to same GitHub repo
   - Set root directory to `/` (same as main service)
4. Under "Settings" → "Build":
   - Builder: Dockerfile
   - Dockerfile Path: `Dockerfile`
5. Under "Settings" → "Deploy":
   - Start Command:
     ```bash
     celery -A src.celery_app worker --loglevel=info --concurrency=4 -Q default,reports,scraping,analytics,emails,data_ingestion
     ```
6. Under "Variables":
   - Click "Raw Editor"
   - Copy ALL variables from main API service
   - Paste into worker service
7. Click "Deploy"

#### Option B: Via Railway CLI

```bash
# Create new service
railway service create onside-celery-worker

# Link to GitHub repo (same as main service)
railway up --service onside-celery-worker

# Set start command
railway variables set START_COMMAND="celery -A src.celery_app worker --loglevel=info"

# Deploy
railway deploy --service onside-celery-worker
```

### Step 7: Verify Worker is Running (3 min)

In Railway dashboard:
1. Click on `onside-celery-worker` service
2. Go to "Deployments" tab
3. Check status is "Active" (green)
4. Go to "Logs" tab
5. You should see:
   ```
   [2024-12-24 HH:MM:SS] celery@worker ready
   ```

### Step 8: Test Walker Agent (5 min)

```bash
# Get your API URL from Railway dashboard
export API_URL=https://onside-production.up.railway.app

# Get your auth token (you'll need to login first)
export TOKEN=your-auth-token

# Test brand analysis endpoint
curl -X POST "${API_URL}/api/v1/engarde/brand-analysis/initiate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "brand_name": "Test Brand",
    "primary_website": "https://example.com",
    "industry": "Technology"
  }'
```

Expected response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "initiated",
  "message": "Brand analysis initiated successfully"
}
```

Then check status:
```bash
curl "${API_URL}/api/v1/engarde/brand-analysis/{job_id}/status" \
  -H "Authorization: Bearer ${TOKEN}"
```

## Troubleshooting

### Problem: DATABASE_URL not set

**Solution:**
1. Go to Railway project
2. Click "New" → "Database" → "Add PostgreSQL"
3. Wait for provisioning
4. `DATABASE_URL` will be auto-added to all services

### Problem: REDIS_URL not set

**Solution:**
1. Go to Railway project
2. Click "New" → "Database" → "Add Redis"
3. Wait for provisioning
4. `REDIS_URL` will be auto-added to all services

### Problem: Worker service fails to start

**Check Logs:**
```bash
railway logs --service onside-celery-worker
```

**Common Issues:**
1. Missing environment variables - Copy from main service
2. Wrong start command - Check command in Step 6
3. Build failing - Check Dockerfile exists

### Problem: Walker agent times out

**This means:**
- Worker service not running
- Or walker still using BackgroundTasks instead of Celery

**Solution:**
1. Verify worker service is deployed (Step 6)
2. Check worker logs for task execution
3. If still using BackgroundTasks, you need code changes (see main diagnosis doc)

### Problem: "No module named src"

**Solution:**
Add to worker service variables:
```bash
PYTHONPATH=/app
```

### Problem: SERPAPI_KEY errors in logs

**Solution:**
1. Get API key from https://serpapi.com
2. Add to Railway variables:
   ```bash
   SERPAPI_KEY=your-key-here
   ```
3. Redeploy service

## Verification Checklist

After completing all steps, verify:

- [ ] `DATABASE_URL` is set (auto by PostgreSQL addon)
- [ ] `REDIS_URL` is set (auto by Redis addon)
- [ ] `SECRET_KEY` is set manually
- [ ] `SERPAPI_KEY` is set manually
- [ ] `ALLOWED_ORIGINS` includes your frontend URL
- [ ] Main API service shows "Active" status
- [ ] Celery worker service shows "Active" status
- [ ] Connection test script passes all tests
- [ ] Brand analysis can be initiated
- [ ] Worker logs show task processing

## Next Steps

Once walker agents are connected:

1. **Monitor Performance:**
   - Check Railway metrics dashboard
   - Review worker logs for errors
   - Set up alerts for failures

2. **Optimize Configuration:**
   - Adjust worker concurrency based on load
   - Set resource limits in Railway
   - Configure auto-scaling if needed

3. **Add Monitoring:**
   - Integrate Sentry for error tracking
   - Set up log aggregation
   - Add uptime monitoring

4. **Handle Object Storage:**
   - Replace MinIO with S3 or Cloudflare R2
   - Or use Railway volumes for uploads
   - Update configuration accordingly

## Emergency Rollback

If something breaks:

```bash
# Via Railway dashboard
1. Go to service → Deployments
2. Find last working deployment
3. Click "..." → "Redeploy"

# Via Railway CLI
railway rollback --service onside-api
```

## Getting Help

If you're stuck:

1. **Check Railway Logs:**
   ```bash
   railway logs --tail
   ```

2. **Check Worker Logs:**
   ```bash
   railway logs --service onside-celery-worker --tail
   ```

3. **Run Connection Test:**
   ```bash
   railway run python scripts/test_railway_connections.py
   ```

4. **Railway Discord:**
   - https://discord.gg/railway
   - #help channel

5. **Review Full Diagnosis:**
   - See `RAILWAY_DEPLOYMENT_DIAGNOSIS.md` for detailed analysis

## Time Estimates

- **Minimum Fix** (Steps 1-5): 15 minutes
  - Gets basic connectivity working
  - Walker agents may still timeout

- **Full Fix** (Steps 1-7): 30 minutes
  - Complete worker deployment
  - Walker agents fully functional

- **With Testing** (Steps 1-8): 45 minutes
  - Verified end-to-end functionality

## Success Criteria

You'll know it's working when:
1. ✅ All connection tests pass
2. ✅ Worker service shows "Active" status
3. ✅ Brand analysis jobs complete without timeout
4. ✅ No connection errors in logs
5. ✅ Results are saved to database

---

**Last Updated:** 2025-12-24
**Priority:** CRITICAL
**Status:** Ready to Execute
