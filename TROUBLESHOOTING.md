# OnSide Troubleshooting Guide

Common issues and their solutions for the OnSide platform.

## Table of Contents

- [General Debugging](#general-debugging)
- [Service-Specific Issues](#service-specific-issues)
- [Database Issues](#database-issues)
- [Network Issues](#network-issues)
- [Performance Issues](#performance-issues)
- [Common Error Messages](#common-error-messages)

## General Debugging

### Check Service Status

```bash
# View all service statuses
docker-compose -f docker-compose.prod.yml ps

# Check health status
docker-compose -f docker-compose.prod.yml ps | grep healthy
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f onside-api-prod

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 onside-api-prod

# Filter by time
docker-compose -f docker-compose.prod.yml logs --since 30m onside-api-prod
```

### Check Resource Usage

```bash
# Container resources
docker stats

# Disk usage
docker system df
df -h

# Memory usage
free -h
```

## Service-Specific Issues

### Frontend (Nginx) Issues

#### Issue: Frontend not accessible

**Symptoms**: Cannot access application via browser

**Diagnosis**:
```bash
# Check if container is running
docker ps | grep onside-frontend

# Check nginx logs
docker-compose -f docker-compose.prod.yml logs onside-frontend

# Test nginx configuration
docker-compose -f docker-compose.prod.yml exec onside-frontend nginx -t
```

**Solutions**:

1. **Container not running**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d onside-frontend
   ```

2. **Configuration error**:
   ```bash
   # Fix nginx.conf and reload
   docker-compose -f docker-compose.prod.yml exec onside-frontend nginx -s reload
   ```

3. **Port conflict**:
   ```bash
   # Check what's using port 80
   sudo lsof -i :80
   # Kill conflicting process or change port in docker-compose
   ```

#### Issue: 502 Bad Gateway

**Symptoms**: Nginx returns 502 error

**Diagnosis**:
```bash
# Check if backend is running
docker ps | grep onside-api-prod

# Check backend health
curl http://localhost:8000/health
```

**Solutions**:
1. Backend service is down - restart it
2. Backend is overloaded - scale workers
3. Network issue between containers - check Docker network

#### Issue: Static files not loading

**Symptoms**: CSS/JS files return 404

**Diagnosis**:
```bash
# Check if files exist in container
docker-compose -f docker-compose.prod.yml exec onside-frontend ls -la /usr/share/nginx/html

# Check nginx cache
docker-compose -f docker-compose.prod.yml exec onside-frontend ls -la /var/cache/nginx
```

**Solutions**:
```bash
# Rebuild frontend
docker-compose -f docker-compose.prod.yml build --no-cache onside-frontend
docker-compose -f docker-compose.prod.yml up -d onside-frontend

# Clear browser cache
```

### Backend API Issues

#### Issue: API not responding

**Symptoms**: Health endpoint returns error or times out

**Diagnosis**:
```bash
# Check if container is running
docker ps | grep onside-api-prod

# Check API logs
docker-compose -f docker-compose.prod.yml logs --tail=100 onside-api-prod

# Test health endpoint
curl -v http://localhost:8000/health
```

**Solutions**:

1. **Database connection issue**:
   ```bash
   # Verify database is accessible
   docker-compose -f docker-compose.prod.yml exec onside-db-prod pg_isready
   
   # Check DATABASE_URL in .env.production
   # Restart API service
   docker-compose -f docker-compose.prod.yml restart onside-api-prod
   ```

2. **Migration pending**:
   ```bash
   docker-compose -f docker-compose.prod.yml exec onside-api-prod alembic upgrade head
   ```

3. **Out of memory**:
   ```bash
   # Check memory usage
   docker stats onside-api-prod
   
   # Increase memory limit in docker-compose.prod.yml
   # Restart service
   ```

#### Issue: Slow API responses

**Symptoms**: Requests take 5+ seconds

**Diagnosis**:
```bash
# Check database connections
docker-compose -f docker-compose.prod.yml exec onside-db-prod psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT count(*) FROM pg_stat_activity;"

# Check slow queries
docker-compose -f docker-compose.prod.yml exec onside-db-prod psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

**Solutions**:
1. Add database indexes
2. Optimize queries
3. Increase database connection pool size
4. Enable Redis caching
5. Scale API workers

#### Issue: Import errors

**Symptoms**: `ModuleNotFoundError` in logs

**Solutions**:
```bash
# Rebuild with no cache
docker-compose -f docker-compose.prod.yml build --no-cache onside-api-prod

# Verify requirements installed
docker-compose -f docker-compose.prod.yml exec onside-api-prod pip list

# Check PYTHONPATH
docker-compose -f docker-compose.prod.yml exec onside-api-prod env | grep PYTHON
```

### Database Issues

#### Issue: Database connection refused

**Symptoms**: `FATAL: password authentication failed` or `connection refused`

**Diagnosis**:
```bash
# Check if database is running
docker ps | grep onside-db-prod

# Check database logs
docker-compose -f docker-compose.prod.yml logs onside-db-prod

# Test connection
docker-compose -f docker-compose.prod.yml exec onside-db-prod pg_isready -U $POSTGRES_USER
```

**Solutions**:

1. **Wrong credentials**:
   - Verify `POSTGRES_PASSWORD` in `.env.production`
   - Match with `DATABASE_URL`

2. **Database not initialized**:
   ```bash
   # Check if database exists
   docker-compose -f docker-compose.prod.yml exec onside-db-prod psql -U $POSTGRES_USER -c "\l"
   
   # Create database if missing
   docker-compose -f docker-compose.prod.yml exec onside-db-prod psql -U $POSTGRES_USER -c "CREATE DATABASE $POSTGRES_DB;"
   ```

3. **Container unhealthy**:
   ```bash
   # Restart database
   docker-compose -f docker-compose.prod.yml restart onside-db-prod
   
   # If that fails, recreate
   docker-compose -f docker-compose.prod.yml up -d --force-recreate onside-db-prod
   ```

#### Issue: Migration failures

**Symptoms**: `alembic upgrade head` fails

**Diagnosis**:
```bash
# Check current migration version
docker-compose -f docker-compose.prod.yml exec onside-api-prod alembic current

# Check migration history
docker-compose -f docker-compose.prod.yml exec onside-api-prod alembic history
```

**Solutions**:

1. **Dirty database state**:
   ```bash
   # Stamp current version
   docker-compose -f docker-compose.prod.yml exec onside-api-prod alembic stamp head
   
   # Or downgrade and retry
   docker-compose -f docker-compose.prod.yml exec onside-api-prod alembic downgrade -1
   docker-compose -f docker-compose.prod.yml exec onside-api-prod alembic upgrade head
   ```

2. **Schema conflict**:
   - Review migration file
   - Fix conflicts manually
   - Create new migration if needed

#### Issue: Database disk full

**Symptoms**: `ERROR: could not extend file` or `No space left on device`

**Diagnosis**:
```bash
# Check disk usage
df -h
docker system df

# Check database size
docker-compose -f docker-compose.prod.yml exec onside-db-prod psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT pg_size_pretty(pg_database_size('$POSTGRES_DB'));"
```

**Solutions**:
```bash
# Vacuum database
docker-compose -f docker-compose.prod.yml exec onside-db-prod psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM FULL;"

# Clean Docker
docker system prune -a

# Expand disk (cloud provider)
# Then resize filesystem
```

### Redis Issues

#### Issue: Redis not responding

**Symptoms**: `Error connecting to Redis` in logs

**Diagnosis**:
```bash
# Check if Redis is running
docker ps | grep onside-redis-prod

# Test Redis
docker-compose -f docker-compose.prod.yml exec onside-redis-prod redis-cli ping

# Check Redis logs
docker-compose -f docker-compose.prod.yml logs onside-redis-prod
```

**Solutions**:

1. **Password authentication issue**:
   ```bash
   # Test with password
   docker-compose -f docker-compose.prod.yml exec onside-redis-prod redis-cli -a $REDIS_PASSWORD ping
   
   # Verify REDIS_PASSWORD in .env.production
   ```

2. **Memory limit reached**:
   ```bash
   # Check memory usage
   docker-compose -f docker-compose.prod.yml exec onside-redis-prod redis-cli INFO memory
   
   # Increase maxmemory in docker-compose.prod.yml
   # Or clear cache
   docker-compose -f docker-compose.prod.yml exec onside-redis-prod redis-cli FLUSHALL
   ```

3. **Corrupted data**:
   ```bash
   # Stop Redis
   docker-compose -f docker-compose.prod.yml stop onside-redis-prod
   
   # Remove volume
   docker volume rm onside-redis-data-prod
   
   # Restart
   docker-compose -f docker-compose.prod.yml up -d onside-redis-prod
   ```

### Celery Issues

#### Issue: Tasks not processing

**Symptoms**: Tasks stuck in queue, not executing

**Diagnosis**:
```bash
# Check worker status
docker ps | grep celery-worker

# Check worker logs
docker-compose -f docker-compose.prod.yml logs onside-celery-worker

# Check Flower
curl http://localhost:5555/api/workers
```

**Solutions**:

1. **Worker not running**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d onside-celery-worker
   ```

2. **Worker overloaded**:
   ```bash
   # Scale workers
   docker-compose -f docker-compose.prod.yml up -d --scale onside-celery-worker=4
   ```

3. **Redis connection issue**:
   - Check Redis is running
   - Verify `CELERY_BROKER_URL`

4. **Task timeout**:
   ```bash
   # Increase timeout in .env.production
   CELERY_TASK_TIME_LIMIT=3600
   CELERY_TASK_SOFT_TIME_LIMIT=3000
   
   # Restart workers
   docker-compose -f docker-compose.prod.yml restart onside-celery-worker
   ```

#### Issue: Celery Beat not scheduling

**Symptoms**: Scheduled tasks not running

**Diagnosis**:
```bash
# Check beat status
docker ps | grep celery-beat

# Check beat logs
docker-compose -f docker-compose.prod.yml logs onside-celery-beat
```

**Solutions**:
```bash
# Remove beat schedule file and restart
docker-compose -f docker-compose.prod.yml stop onside-celery-beat
docker volume rm onside-celery-beat-data
docker-compose -f docker-compose.prod.yml up -d onside-celery-beat
```

### MinIO Issues

#### Issue: Cannot upload files

**Symptoms**: Upload fails with 403 or 500 error

**Diagnosis**:
```bash
# Check MinIO status
docker ps | grep onside-minio-prod

# Check MinIO logs
docker-compose -f docker-compose.prod.yml logs onside-minio-prod

# Test MinIO health
curl http://localhost:9000/minio/health/live
```

**Solutions**:

1. **Bucket doesn't exist**:
   ```bash
   # Access MinIO console: http://localhost:9001
   # Create required buckets
   ```

2. **Permission issue**:
   - Check bucket policies in MinIO console
   - Verify `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY`

3. **Disk full**:
   ```bash
   # Check MinIO volume
   docker system df -v | grep minio
   ```

## Network Issues

### Issue: Services can't communicate

**Symptoms**: `Connection refused` between containers

**Diagnosis**:
```bash
# Check Docker network
docker network ls
docker network inspect onside-network-prod

# Test connectivity
docker-compose -f docker-compose.prod.yml exec onside-api-prod ping onside-db-prod
```

**Solutions**:
```bash
# Recreate network
docker-compose -f docker-compose.prod.yml down
docker network prune
docker-compose -f docker-compose.prod.yml up -d
```

### Issue: Cannot access from external network

**Symptoms**: Can access locally but not from internet

**Diagnosis**:
```bash
# Check firewall
sudo ufw status

# Check port binding
sudo netstat -tulpn | grep :80
```

**Solutions**:
```bash
# Open firewall ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Verify Docker port mapping
docker-compose -f docker-compose.prod.yml ps
```

## Performance Issues

### Issue: High CPU usage

**Diagnosis**:
```bash
# Check container CPU
docker stats

# Check processes
docker-compose -f docker-compose.prod.yml exec onside-api-prod top
```

**Solutions**:
1. Scale services horizontally
2. Optimize database queries
3. Add caching
4. Review CPU limits in docker-compose

### Issue: High memory usage

**Diagnosis**:
```bash
# Check memory
docker stats
free -h

# Check for memory leaks
docker-compose -f docker-compose.prod.yml logs | grep -i "memory"
```

**Solutions**:
1. Increase memory limits
2. Add swap space
3. Investigate memory leaks
4. Restart services periodically

### Issue: Slow disk I/O

**Diagnosis**:
```bash
# Check I/O wait
iostat -x 1

# Check slow queries
docker-compose -f docker-compose.prod.yml exec onside-db-prod psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

**Solutions**:
1. Move to faster storage (SSD)
2. Optimize database
3. Add read replicas
4. Use caching

## Common Error Messages

### "FATAL: too many connections"

**Cause**: PostgreSQL connection limit reached

**Solution**:
```bash
# Increase max_connections in docker-compose.prod.yml
# Or reduce connection pool size in application
```

### "OSError: [Errno 24] Too many open files"

**Cause**: File descriptor limit reached

**Solution**:
```bash
# Increase limit
ulimit -n 65536

# Make permanent in /etc/security/limits.conf
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
```

### "ERROR: for onside-api-prod Cannot create container"

**Cause**: Port already in use or volume conflict

**Solution**:
```bash
# Stop conflicting services
docker-compose -f docker-compose.prod.yml down

# Remove volumes if needed
docker volume rm onside-postgres-data-prod

# Restart
docker-compose -f docker-compose.prod.yml up -d
```

### "ModuleNotFoundError: No module named 'src'"

**Cause**: PYTHONPATH not set or package not installed

**Solution**:
```bash
# Rebuild image
docker-compose -f docker-compose.prod.yml build --no-cache onside-api-prod

# Verify PYTHONPATH
docker-compose -f docker-compose.prod.yml exec onside-api-prod env | grep PYTHONPATH
```

## Getting Help

If you're still experiencing issues:

1. **Collect information**:
   ```bash
   # Save all logs
   docker-compose -f docker-compose.prod.yml logs > debug-logs.txt
   
   # System info
   docker info > docker-info.txt
   docker-compose -f docker-compose.prod.yml ps > services-status.txt
   ```

2. **Check documentation**:
   - [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
   - [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)

3. **Contact support**:
   - Email: support@your-domain.com
   - Include: Error messages, logs, steps to reproduce

## Emergency Procedures

### Complete System Restart

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Clean up
docker system prune -f

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify
./scripts/deployment/health-check.sh production
```

### Restore from Backup

```bash
# Use rollback script
./scripts/deployment/rollback.sh production backups/YYYYMMDD-HHMMSS
```

### Nuclear Option (Last Resort)

```bash
# WARNING: This will delete ALL data!

# Stop everything
docker-compose -f docker-compose.prod.yml down -v

# Remove all Docker resources
docker system prune -a --volumes -f

# Redeploy from scratch
./scripts/deployment/deploy.sh production
```

---

**Last Updated**: [Date]
**Version**: 1.0.0
