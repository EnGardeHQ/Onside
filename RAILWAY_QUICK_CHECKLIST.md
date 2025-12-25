# Railway Deployment Quick Checklist

## Pre-Deployment Setup

### 1. Get API Keys (Before Starting)

- [ ] **SerpAPI**: https://serpapi.com/manage-api-key
- [ ] **OpenAI**: https://platform.openai.com/api-keys
- [ ] **Anthropic**: https://console.anthropic.com/settings/keys
- [ ] Generate SECRET_KEY: `openssl rand -hex 32`

### 2. Railway Project Setup

- [ ] Create Railway account: https://railway.app
- [ ] Connect GitHub account to Railway
- [ ] Create new Railway project
- [ ] Connect Onside GitHub repository

---

## Main API Service Deployment

### Step 1: Add Databases

- [ ] Add PostgreSQL addon (Railway dashboard → New → Database → PostgreSQL)
- [ ] Add Redis addon (Railway dashboard → New → Database → Redis)
- [ ] Verify `DATABASE_URL` auto-generated
- [ ] Verify `REDIS_URL` auto-generated

### Step 2: Set Environment Variables

Copy from `.env.railway.example` and update these required variables:

```bash
# Critical - Must Change
SECRET_KEY=<output-of-openssl-rand-hex-32>
SERPAPI_KEY=<your-serpapi-key>
OPENAI_API_KEY=sk-proj-<your-openai-key>
ANTHROPIC_API_KEY=sk-ant-<your-anthropic-key>
ALLOWED_ORIGINS=https://your-frontend-domain.railway.app

# Celery (reference Railway's auto-generated REDIS_URL)
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Cache
CACHE_ENABLED=true
CACHE_NAMESPACE=onside
CACHE_DEFAULT_TTL=300

# Application
APP_ENV=production
LOG_LEVEL=INFO
```

**Set in Railway:**
1. Service → Variables → Raw Editor
2. Paste variables above (with your values)
3. Click Save

### Step 3: Deploy API

- [ ] Railway auto-deploys after variables set
- [ ] Monitor: Service → Deployments → View Logs
- [ ] Wait for: `Application startup complete`

### Step 4: Verify API Service

```bash
export API_URL=https://your-service.up.railway.app

# Test health
curl $API_URL/health
# Expected: {"status":"healthy"}

# Test API docs
curl $API_URL/api/docs
# Expected: HTML page
```

- [ ] Health endpoint returns 200 OK
- [ ] API docs accessible
- [ ] Check logs for database connection: "Database connection established"
- [ ] Check logs for cache: "Cache service initialized successfully"

---

## Celery Worker Deployment

### Step 1: Create Worker Service

- [ ] Railway Dashboard → New Service
- [ ] Select: GitHub Repo (same as API)
- [ ] Name: `onside-celery-worker`

### Step 2: Configure Worker

- [ ] Service → Settings → Deploy
- [ ] Set Start Command:
  ```bash
  celery -A src.celery_app worker --loglevel=info --concurrency=4 -Q default,reports,scraping,analytics,emails,data_ingestion
  ```

### Step 3: Copy Variables

- [ ] Go to API service → Variables → Raw Editor → Copy all
- [ ] Go to Worker service → Variables → Raw Editor → Paste
- [ ] Click Save

### Step 4: Add Dependencies

- [ ] Worker service → Settings → Service Dependencies
- [ ] Add: PostgreSQL database
- [ ] Add: Redis database

### Step 5: Deploy Worker

- [ ] Click Deploy
- [ ] Monitor logs for:
  ```
  [INFO/MainProcess] celery@railway ready.
  [INFO/MainProcess] Listening to queues: default, reports, scraping, analytics, emails, data_ingestion
  ```

- [ ] Worker shows "ready" in logs
- [ ] No connection errors in logs

---

## Optional: Celery Beat (Scheduled Tasks)

- [ ] Create service: `onside-celery-beat`
- [ ] Same repo, same Dockerfile
- [ ] Start command: `celery -A src.celery_app beat --loglevel=info`
- [ ] Copy all variables from API service
- [ ] Add dependency: Redis
- [ ] Deploy

---

## Optional: Flower (Task Monitoring)

- [ ] Create service: `onside-flower`
- [ ] Same repo, same Dockerfile
- [ ] Start command: `celery -A src.celery_app flower --port=${PORT:-5555} --basic_auth=${FLOWER_BASIC_AUTH}`
- [ ] Add variable: `FLOWER_BASIC_AUTH=admin:your-secure-password`
- [ ] Copy all other variables
- [ ] Deploy
- [ ] Access at generated Railway URL

---

## Post-Deployment Testing

### Test 1: API Health

```bash
curl https://your-api-url.railway.app/health
```

- [ ] Returns: `{"status":"healthy"}`

### Test 2: Background Task

```bash
curl -X POST https://your-api-url.railway.app/api/v1/engarde/brand-analysis/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "brand_name": "TestBrand",
    "website_url": "https://example.com",
    "industry": "Technology"
  }'
```

- [ ] Returns job_id
- [ ] Check worker logs: See task execution
- [ ] Task completes without errors

### Test 3: CORS (from Frontend)

```bash
# From browser console on your frontend domain
fetch('https://your-api-url.railway.app/health')
```

- [ ] No CORS errors
- [ ] Response received

---

## Troubleshooting Quick Reference

### Problem: Build Failed

1. Check Dockerfile exists in repo root
2. View build logs: Service → Deployments → Failed build → Logs
3. Test locally: `docker build -t test .`

### Problem: Service Crashed

1. Check logs: `railway logs --service onside-api`
2. Look for error stack traces
3. Common issues:
   - Missing environment variable
   - Invalid DATABASE_URL format
   - Port binding issue

### Problem: Database Connection Failed

1. Verify PostgreSQL addon added
2. Check `DATABASE_URL` exists in Variables
3. Verify service has PostgreSQL dependency
4. Restart service

### Problem: Redis Connection Failed

1. Verify Redis addon added
2. Check `REDIS_URL` exists in Variables
3. Verify `CELERY_BROKER_URL=${REDIS_URL}` (with $ sign)
4. Check Redis service is running

### Problem: Tasks Not Processing

1. Verify worker service is running
2. Check worker has same `REDIS_URL` as API
3. Verify start command includes all queues
4. Check worker logs for errors

### Problem: CORS Errors

1. Update `ALLOWED_ORIGINS` with correct domain
2. Include protocol: `https://domain.com` (not `domain.com`)
3. Redeploy after variable change
4. Test again

---

## Railway Service URLs

After deployment, record your URLs here:

```
API Service:     https://__________________________.railway.app
Worker Service:  (no public URL - internal only)
Flower Service:  https://__________________________.railway.app
Frontend:        https://__________________________.railway.app

PostgreSQL:      postgres.railway.internal (internal)
Redis:           redis.railway.internal (internal)
```

---

## Critical Environment Variables Summary

| Variable | Source | Required |
|----------|--------|----------|
| `DATABASE_URL` | Auto (PostgreSQL addon) | Yes |
| `REDIS_URL` | Auto (Redis addon) | Yes |
| `SECRET_KEY` | Manual (generate) | Yes |
| `SERPAPI_KEY` | Manual (serpapi.com) | Yes |
| `OPENAI_API_KEY` | Manual (OpenAI) | Yes |
| `ANTHROPIC_API_KEY` | Manual (Anthropic) | Yes |
| `ALLOWED_ORIGINS` | Manual (your frontend) | Yes |
| `CELERY_BROKER_URL` | `${REDIS_URL}` | Yes |
| `CELERY_RESULT_BACKEND` | `${REDIS_URL}` | Yes |

---

## Deployment Time Estimate

- PostgreSQL addon: 1-2 min
- Redis addon: 1-2 min
- Set environment variables: 5 min
- API service deploy: 5-10 min
- Worker service setup: 5 min
- Testing: 5 min

**Total: ~25-30 minutes**

---

## Next Steps After Deployment

1. **Monitor Logs**
   - Watch for errors in first 24 hours
   - Check worker task execution
   - Monitor memory usage

2. **Configure Alerts**
   - Service → Settings → Alerts
   - Add email notifications

3. **Update Frontend**
   - Update API URL in frontend config
   - Test end-to-end workflow

4. **Documentation**
   - Record Railway URLs
   - Update team docs with new endpoints

5. **Backup Strategy**
   - Set up database backups
   - Test restore procedure

---

## Support

- **Full Guide**: See `RAILWAY_DEPLOYMENT_GUIDE.md`
- **Environment Variables**: See `RAILWAY_ENV_SETUP.md`
- **Example Config**: See `.env.railway.example`
- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway

---

**Quick Deploy Command** (if using Railway CLI):

```bash
# Install CLI
npm i -g @railway/cli && railway login

# Deploy
railway init
railway add --database postgres
railway add --database redis
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set SERPAPI_KEY=your-key
railway variables set OPENAI_API_KEY=sk-proj-your-key
railway variables set ANTHROPIC_API_KEY=sk-ant-your-key
railway up

# Then create worker service via dashboard
```

---

**Last Updated:** 2024-12-24
