# Railway Deployment Checklist

**Project:** OnSide Competitive Intelligence Platform
**Deployment URL:** https://onside-production.up.railway.app
**Date:** 2025-12-24

## Pre-Deployment Checklist

### Infrastructure Setup
- [ ] Railway account created and verified
- [ ] GitHub repository connected to Railway
- [ ] PostgreSQL addon added to project
- [ ] Redis addon added to project
- [ ] Domain configured (if using custom domain)

### Environment Variables - Required
- [ ] `DATABASE_URL` - Auto-set by PostgreSQL addon
- [ ] `REDIS_URL` - Auto-set by Redis addon
- [ ] `SECRET_KEY` - Manually set (64+ character random string)
- [ ] `SERPAPI_KEY` - Manually set (from serpapi.com)
- [ ] `ALLOWED_ORIGINS` - Set to frontend URL(s)
- [ ] `APP_ENV` - Set to `production`

### Environment Variables - Recommended
- [ ] `CELERY_BROKER_URL` - Set to `${REDIS_URL}`
- [ ] `CELERY_RESULT_BACKEND` - Set to `${REDIS_URL}`
- [ ] `CACHE_ENABLED` - Set to `true`
- [ ] `CACHE_DEFAULT_TTL` - Set to `300`
- [ ] `ALGORITHM` - Set to `HS256`
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` - Set to `30`

### Environment Variables - Optional
- [ ] `SEMRUSH_API_KEY` - For additional SEO features
- [ ] `OPENAI_API_KEY` - For AI-powered features
- [ ] `ANTHROPIC_API_KEY` - For Claude AI features
- [ ] `SENTRY_DSN` - For error tracking

## Service Deployment Checklist

### Main API Service
- [ ] Service created in Railway
- [ ] Connected to GitHub repository
- [ ] Dockerfile detected (`/Dockerfile`)
- [ ] Build successful
- [ ] Start command: `uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4`
- [ ] Health check configured: `/health`
- [ ] All environment variables set
- [ ] Service deployed and running (green status)
- [ ] Public URL accessible
- [ ] `/health` endpoint returns 200 OK

### Celery Worker Service
- [ ] New service created (`onside-celery-worker`)
- [ ] Connected to same GitHub repository
- [ ] Same Dockerfile used
- [ ] Build successful
- [ ] Start command: `celery -A src.celery_app worker --loglevel=info --concurrency=4 -Q default,reports,scraping,analytics,emails,data_ingestion`
- [ ] All environment variables copied from API service
- [ ] Service deployed and running
- [ ] Logs show "celery@worker ready"
- [ ] No connection errors in logs

### Celery Beat Service (Optional - for scheduled tasks)
- [ ] New service created (`onside-celery-beat`)
- [ ] Connected to same GitHub repository
- [ ] Same Dockerfile used
- [ ] Start command: `celery -A src.celery_app beat --loglevel=info`
- [ ] Environment variables set
- [ ] Service deployed and running

### Database Service (PostgreSQL)
- [ ] PostgreSQL addon added
- [ ] Database provisioned
- [ ] `DATABASE_URL` auto-set
- [ ] Connection successful from API service
- [ ] Tables created (via migrations)
- [ ] Sample data inserted (if applicable)

### Cache Service (Redis)
- [ ] Redis addon added
- [ ] Redis provisioned
- [ ] `REDIS_URL` auto-set
- [ ] Connection successful from API service
- [ ] Ping test successful

## Post-Deployment Verification

### Connectivity Tests
- [ ] Run connection test script:
  ```bash
  railway run python scripts/test_railway_connections.py
  ```
- [ ] Database connection test passes
- [ ] Redis connection test passes
- [ ] All environment variables verified
- [ ] Application config loads correctly
- [ ] Celery broker connection successful

### API Endpoint Tests
- [ ] Root endpoint `/` returns welcome message
- [ ] Health check `/health` returns 200 OK
- [ ] API docs accessible at `/api/docs`
- [ ] Authentication endpoints working
- [ ] Brand analysis endpoint accessible

### Walker Agent Tests
- [ ] Initiate brand analysis request
- [ ] Job ID returned successfully
- [ ] Job status updates in database
- [ ] Worker logs show task processing
- [ ] Analysis completes without timeout
- [ ] Results saved to database
- [ ] WebSocket updates sent (if applicable)

### Error Handling
- [ ] 404 errors return proper responses
- [ ] 500 errors logged properly
- [ ] Database errors handled gracefully
- [ ] Redis errors don't crash service
- [ ] SERP API errors handled with fallback

## Monitoring Setup

### Logging
- [ ] Railway logs accessible
- [ ] Log level appropriate for production
- [ ] Sensitive data not logged
- [ ] Error logs contain useful context
- [ ] Worker logs separate from API logs

### Alerts (Recommended)
- [ ] Uptime monitoring configured (UptimeRobot, Pingdom)
- [ ] Error tracking integrated (Sentry)
- [ ] Performance monitoring setup
- [ ] Database monitoring enabled
- [ ] Redis monitoring enabled

### Metrics (Optional)
- [ ] Request count tracking
- [ ] Response time monitoring
- [ ] Error rate tracking
- [ ] Worker task metrics
- [ ] Database query performance

## Security Checklist

### Secrets Management
- [ ] `SECRET_KEY` is strong (64+ characters)
- [ ] API keys not committed to git
- [ ] `.env` file in `.gitignore`
- [ ] Environment variables use Railway secrets
- [ ] Database password is strong
- [ ] Redis password configured (if applicable)

### CORS Configuration
- [ ] `ALLOWED_ORIGINS` set to specific domains (not `*`)
- [ ] Frontend domain included
- [ ] API domain included
- [ ] No wildcard in production

### SSL/TLS
- [ ] Railway provides HTTPS automatically
- [ ] All requests use HTTPS
- [ ] HTTP redirects to HTTPS
- [ ] SSL certificate valid

### API Security
- [ ] Authentication required for protected endpoints
- [ ] JWT tokens configured properly
- [ ] Token expiration set appropriately
- [ ] Rate limiting configured (if applicable)
- [ ] Input validation enabled

## Performance Optimization

### API Service
- [ ] Worker count appropriate for load (4 workers)
- [ ] Request timeout configured
- [ ] Connection pooling enabled
- [ ] Static file caching configured

### Celery Workers
- [ ] Concurrency set appropriately (4)
- [ ] Task time limits configured
- [ ] Task result expiration set
- [ ] Dead letter queue configured (optional)

### Database
- [ ] Connection pool size configured
- [ ] Query optimization reviewed
- [ ] Indexes created where needed
- [ ] Database backups configured

### Caching
- [ ] Redis cache enabled
- [ ] TTL values appropriate
- [ ] Cache invalidation strategy defined
- [ ] Cache hit rate monitored

## Backup and Recovery

### Database Backups
- [ ] Railway automatic backups enabled
- [ ] Backup retention policy understood
- [ ] Manual backup tested
- [ ] Recovery procedure documented

### Rollback Strategy
- [ ] Previous deployments accessible
- [ ] Rollback procedure tested
- [ ] Database migration rollback plan
- [ ] Environment variable backup maintained

## Documentation

### Internal Documentation
- [ ] Deployment process documented
- [ ] Environment variables documented
- [ ] Service architecture documented
- [ ] Troubleshooting guide created

### API Documentation
- [ ] OpenAPI/Swagger docs accessible
- [ ] Endpoint examples provided
- [ ] Authentication flow documented
- [ ] Error codes documented

## Cost Management

### Resource Monitoring
- [ ] Railway usage dashboard reviewed
- [ ] Resource limits understood
- [ ] Cost alerts configured
- [ ] Billing reviewed monthly

### Optimization
- [ ] Unused services removed
- [ ] Idle resources minimized
- [ ] Auto-scaling configured (if needed)
- [ ] Resource quotas appropriate

## Compliance and Legal

### Data Protection
- [ ] Privacy policy updated
- [ ] Terms of service updated
- [ ] Data retention policy defined
- [ ] GDPR compliance reviewed (if applicable)

### Licensing
- [ ] All dependencies licensed properly
- [ ] Open source licenses compatible
- [ ] Third-party services terms accepted

## Final Verification

### End-to-End Test
- [ ] User can register/login
- [ ] User can initiate brand analysis
- [ ] Analysis completes successfully
- [ ] Results are displayed correctly
- [ ] Export functionality works
- [ ] Import to En Garde works

### Load Testing (Optional but Recommended)
- [ ] API can handle expected load
- [ ] Workers can process queue
- [ ] Database performs under load
- [ ] Redis handles cache requests

### User Acceptance
- [ ] Stakeholders notified of deployment
- [ ] Demo conducted successfully
- [ ] Feedback collected
- [ ] Issues documented for future sprints

## Sign-Off

### Deployment Team
- [ ] DevOps Engineer: _______________  Date: _______
- [ ] Backend Developer: _____________  Date: _______
- [ ] QA Engineer: __________________  Date: _______

### Stakeholders
- [ ] Product Owner: ________________  Date: _______
- [ ] Project Manager: ______________  Date: _______

---

## Quick Reference

### Essential Commands

**Test Connections:**
```bash
railway run python scripts/test_railway_connections.py
```

**View Logs:**
```bash
# API logs
railway logs --service onside-api --tail

# Worker logs
railway logs --service onside-celery-worker --tail
```

**Deploy New Version:**
```bash
git push origin main
# Railway auto-deploys on push
```

**Rollback:**
```bash
railway rollback --service onside-api
```

**Set Variable:**
```bash
railway variables set KEY=VALUE
```

### Important URLs

- **Production API:** https://onside-production.up.railway.app
- **API Docs:** https://onside-production.up.railway.app/api/docs
- **Health Check:** https://onside-production.up.railway.app/health
- **Railway Dashboard:** https://railway.app/project/[your-project-id]

### Support Contacts

- **Railway Support:** https://help.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Documentation:** See `RAILWAY_DEPLOYMENT_DIAGNOSIS.md`
- **Quick Fix:** See `RAILWAY_QUICK_FIX_GUIDE.md`

---

**Checklist Version:** 1.0
**Last Updated:** 2025-12-24
**Next Review:** After first week of production use
