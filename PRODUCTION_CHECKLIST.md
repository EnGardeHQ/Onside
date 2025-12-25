# OnSide Production Deployment Checklist

Use this checklist before deploying to production to ensure all requirements are met.

## Pre-Deployment Checklist

### Infrastructure Setup

- [ ] Server provisioned with minimum requirements
  - [ ] 8 CPU cores
  - [ ] 32 GB RAM
  - [ ] 500 GB SSD storage
  - [ ] Ubuntu 22.04 LTS or equivalent

- [ ] Docker installed (version 20.10+)
  ```bash
  docker --version
  ```

- [ ] Docker Compose installed (version 2.0+)
  ```bash
  docker-compose --version
  ```

- [ ] Firewall configured
  - [ ] Port 80 (HTTP) open
  - [ ] Port 443 (HTTPS) open
  - [ ] Unnecessary ports blocked

### Domain & DNS Configuration

- [ ] Domain name registered
- [ ] DNS A records configured
  - [ ] `your-domain.com` → Server IP
  - [ ] `www.your-domain.com` → Server IP
  - [ ] `api.your-domain.com` → Server IP (if separate)

- [ ] SSL certificates obtained
  - [ ] Let's Encrypt certificates generated
  - [ ] Certificates copied to `nginx/ssl/`
  - [ ] Certificate expiry monitoring setup

### Environment Configuration

- [ ] `.env.production` file created from template
- [ ] All placeholder values replaced
- [ ] Strong passwords generated for:
  - [ ] `POSTGRES_PASSWORD` (32+ characters)
  - [ ] `REDIS_PASSWORD` (32+ characters)
  - [ ] `SECRET_KEY` (64+ characters, hex)
  - [ ] `MINIO_ACCESS_KEY` (20+ characters)
  - [ ] `MINIO_SECRET_KEY` (40+ characters)
  - [ ] `FLOWER_BASIC_AUTH`

- [ ] External API keys configured:
  - [ ] `OPENAI_API_KEY`
  - [ ] `ANTHROPIC_API_KEY`
  - [ ] `GOOGLE_API_KEY`
  - [ ] `YOUTUBE_API_KEY`
  - [ ] Other service API keys

- [ ] Domain URLs updated:
  - [ ] `VITE_API_URL`
  - [ ] `VITE_WS_URL`
  - [ ] `CORS_ORIGINS`
  - [ ] `ALLOWED_HOSTS`

### Security Configuration

- [ ] HTTPS/SSL enabled
  - [ ] Nginx HTTPS configuration uncommented
  - [ ] SSL certificates valid
  - [ ] HTTP to HTTPS redirect configured

- [ ] Security headers configured
  - [ ] `X-Frame-Options`
  - [ ] `X-Content-Type-Options`
  - [ ] `X-XSS-Protection`
  - [ ] `Referrer-Policy`

- [ ] Rate limiting enabled
  - [ ] `RATE_LIMIT_ENABLED=true`
  - [ ] Appropriate limits set

- [ ] CORS properly configured
  - [ ] Only production domains in `CORS_ORIGINS`
  - [ ] No wildcards (*) in production

- [ ] Session security enabled
  - [ ] `SESSION_COOKIE_SECURE=true`
  - [ ] `SESSION_COOKIE_HTTPONLY=true`
  - [ ] `SESSION_COOKIE_SAMESITE=strict`

### Database Setup

- [ ] Database credentials secured
- [ ] PostgreSQL configured for production
  - [ ] Connection pooling enabled
  - [ ] Backup retention configured
  - [ ] Performance tuning applied

- [ ] Initial migration tested
  ```bash
  docker-compose exec onside-api-prod alembic upgrade head
  ```

### Storage Configuration

- [ ] MinIO buckets created
  - [ ] Campaign assets bucket
  - [ ] User uploads bucket
  - [ ] Exports bucket

- [ ] MinIO access policies configured
- [ ] Backup storage configured
  - [ ] S3 bucket created (if using S3 backups)
  - [ ] AWS credentials configured

### Application Configuration

- [ ] Frontend build tested
  ```bash
  cd frontend
  npm run build
  ```

- [ ] Backend health endpoint working
  ```bash
  curl http://localhost:8000/health
  ```

- [ ] All environment variables validated
- [ ] Feature flags set appropriately for production
  - [ ] `ENABLE_SWAGGER_DOCS=false` (or protect with auth)
  - [ ] `APP_DEBUG=false`
  - [ ] `VITE_ENABLE_DEBUG=false`

### Monitoring & Logging

- [ ] Log aggregation configured
  - [ ] Log rotation enabled
  - [ ] `LOG_MAX_SIZE_MB` set
  - [ ] `LOG_BACKUP_COUNT` set

- [ ] Error tracking configured
  - [ ] Sentry DSN configured (if using)
  - [ ] `SENTRY_ENVIRONMENT=production`

- [ ] Metrics collection enabled
  - [ ] Prometheus metrics enabled (if using)
  - [ ] Monitoring dashboard configured

- [ ] Flower monitoring accessible
  - [ ] Protected with authentication
  - [ ] Not exposed to public internet

### Backup Strategy

- [ ] Backup script tested
  ```bash
  ./scripts/deployment/backup.sh production full
  ```

- [ ] Automated backups configured
  - [ ] Cron job created
  - [ ] Backup retention policy set
  - [ ] Backup verification process defined

- [ ] Backup restoration tested
  ```bash
  ./scripts/deployment/rollback.sh production <backup-dir>
  ```

- [ ] Off-site backup storage configured
  - [ ] S3 sync enabled (if using)
  - [ ] Backup encryption configured

### Performance Optimization

- [ ] Resource limits configured in `docker-compose.prod.yml`
  - [ ] CPU limits appropriate
  - [ ] Memory limits appropriate
  - [ ] No resource starvation

- [ ] PostgreSQL tuned for production
  - [ ] `shared_buffers` optimized
  - [ ] `effective_cache_size` optimized
  - [ ] `max_connections` appropriate

- [ ] Redis cache configured
  - [ ] `maxmemory` set appropriately
  - [ ] Eviction policy configured

- [ ] Celery workers scaled appropriately
  - [ ] Worker count matches workload
  - [ ] Queue priorities configured

### Testing

- [ ] Health checks passing
  ```bash
  ./scripts/deployment/health-check.sh production
  ```

- [ ] All services responding
  - [ ] Frontend loads successfully
  - [ ] API endpoints accessible
  - [ ] WebSocket connections work
  - [ ] Celery tasks execute

- [ ] End-to-end tests passed
  - [ ] User registration/login
  - [ ] Campaign creation
  - [ ] Report generation
  - [ ] File uploads
  - [ ] API integrations

- [ ] Load testing completed (optional but recommended)
  - [ ] Application handles expected traffic
  - [ ] No memory leaks
  - [ ] Response times acceptable

## Deployment Checklist

### Pre-Deployment

- [ ] All pre-deployment checks passed
- [ ] Deployment scheduled during low-traffic window
- [ ] Team notified of deployment
- [ ] Rollback plan reviewed

### During Deployment

- [ ] Current state backed up
  ```bash
  ./scripts/deployment/backup.sh production full
  ```

- [ ] Deployment executed
  ```bash
  ./scripts/deployment/deploy.sh production
  ```

- [ ] All services started successfully
- [ ] Database migrations completed
- [ ] Health checks passing

### Post-Deployment

- [ ] Application accessible via domain
  - [ ] `https://your-domain.com` loads
  - [ ] `https://api.your-domain.com` responds

- [ ] SSL certificate valid
  ```bash
  curl -I https://your-domain.com
  ```

- [ ] All critical features tested
  - [ ] User authentication
  - [ ] Dashboard loads
  - [ ] Reports generate
  - [ ] Uploads work

- [ ] Monitoring dashboards updated
  - [ ] Metrics flowing
  - [ ] No errors in logs
  - [ ] Queue processing normally

- [ ] Documentation updated
  - [ ] Deployment notes recorded
  - [ ] Known issues documented
  - [ ] Runbook updated

## Post-Launch Checklist (Week 1)

### Daily Monitoring

- [ ] Check application logs for errors
  ```bash
  docker-compose -f docker-compose.prod.yml logs --tail=100 onside-api-prod
  ```

- [ ] Monitor resource usage
  ```bash
  docker stats
  ```

- [ ] Verify backups completing successfully
- [ ] Check Celery queue lengths
- [ ] Review error tracking dashboard

### Weekly Tasks

- [ ] Review application performance
  - [ ] Response times
  - [ ] Error rates
  - [ ] Resource utilization

- [ ] Check disk space usage
  ```bash
  df -h
  docker system df
  ```

- [ ] Verify SSL certificate expiry
  ```bash
  openssl x509 -enddate -noout -in nginx/ssl/cert.pem
  ```

- [ ] Review security logs
- [ ] Update dependencies if needed

## Ongoing Maintenance Checklist

### Monthly

- [ ] Review and rotate logs
- [ ] Clean up old Docker images
  ```bash
  docker image prune -a
  ```

- [ ] Verify backup restoration
- [ ] Update security patches
- [ ] Review API usage and costs
- [ ] Performance optimization review

### Quarterly

- [ ] Security audit
- [ ] Dependency updates
- [ ] Disaster recovery drill
- [ ] Capacity planning review
- [ ] Documentation review

## Emergency Contacts

- **DevOps Lead**: [Name, Phone, Email]
- **Backend Lead**: [Name, Phone, Email]
- **Database Admin**: [Name, Phone, Email]
- **On-Call Engineer**: [Rotation Schedule]

## Rollback Procedure

If issues are detected:

1. **Immediate**:
   ```bash
   # Stop services
   docker-compose -f docker-compose.prod.yml down
   ```

2. **Restore from backup**:
   ```bash
   ./scripts/deployment/rollback.sh production <backup-directory>
   ```

3. **Verify restoration**:
   ```bash
   ./scripts/deployment/health-check.sh production
   ```

4. **Notify stakeholders**

## Sign-Off

- [ ] Deployment completed by: _________________ Date: _______
- [ ] Verified by: _________________ Date: _______
- [ ] Approved for production by: _________________ Date: _______

## Notes

_Use this section for deployment-specific notes, issues encountered, or special considerations._

---

**Last Updated**: [Date]
**Version**: 1.0.0
