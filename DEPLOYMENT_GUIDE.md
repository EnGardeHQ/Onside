# OnSide Deployment Guide

Complete guide for deploying the OnSide Competitive Intelligence Platform to production.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Pre-Deployment Setup](#pre-deployment-setup)
- [Deployment Process](#deployment-process)
- [Post-Deployment](#post-deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)

## Overview

OnSide is deployed using Docker Compose with the following services:

- **Frontend**: React application served by Nginx
- **Backend API**: FastAPI application with Uvicorn
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Object Storage**: MinIO
- **Task Queue**: Celery with Flower monitoring
- **Web Scraping**: Playwright

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Load Balancer                        │
│                      (nginx / Cloudflare)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴───────────┐
        │                        │
┌───────▼────────┐      ┌───────▼────────┐
│   Frontend     │      │   Backend API   │
│   (Nginx)      │      │   (FastAPI)     │
│   Port 80/443  │      │   Port 8000     │
└────────────────┘      └───────┬─────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
        │  PostgreSQL  │ │   Redis   │ │    MinIO    │
        │  Port 5432   │ │ Port 6379 │ │  Port 9000  │
        └──────────────┘ └───────────┘ └─────────────┘
                                │
                        ┌───────┴────────┐
                        │                │
                ┌───────▼───────┐ ┌─────▼─────┐
                │ Celery Worker │ │   Flower  │
                │  (Background) │ │ Port 5555 │
                └───────────────┘ └───────────┘
```

## Prerequisites

### System Requirements

**Minimum Production Requirements:**
- CPU: 4 cores
- RAM: 16 GB
- Storage: 100 GB SSD
- OS: Ubuntu 20.04+ / Debian 11+ / RHEL 8+

**Recommended Production Requirements:**
- CPU: 8 cores
- RAM: 32 GB
- Storage: 500 GB SSD
- OS: Ubuntu 22.04 LTS

### Software Requirements

1. **Docker** (version 20.10+)
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

2. **Docker Compose** (version 2.0+)
   ```bash
   sudo apt-get update
   sudo apt-get install docker-compose-plugin
   ```

3. **Git**
   ```bash
   sudo apt-get install git
   ```

4. **SSL Certificates** (for HTTPS)
   - Use Let's Encrypt with certbot
   - Or provide your own certificates

### Network Requirements

Open the following ports in your firewall:

- **80** (HTTP) - Frontend
- **443** (HTTPS) - Frontend (SSL)
- **8000** (Optional) - API direct access
- **5555** (Optional) - Flower monitoring
- **9001** (Optional) - MinIO console

## Pre-Deployment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/onside.git
cd onside
```

### 2. Configure Environment Variables

```bash
# Copy production environment template
cp .env.production.example .env.production

# Edit with your production values
nano .env.production
```

**Critical Variables to Update:**

```bash
# Database
POSTGRES_PASSWORD=<strong-random-password>

# Redis
REDIS_PASSWORD=<strong-random-password>

# JWT Secret (generate with: openssl rand -hex 32)
SECRET_KEY=<64-character-hex-string>

# MinIO
MINIO_ACCESS_KEY=<20-character-access-key>
MINIO_SECRET_KEY=<40-character-secret-key>

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Domain Configuration
VITE_API_URL=https://api.your-domain.com
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

### 3. SSL Certificate Setup

#### Option A: Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy to project
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
sudo chown -R $USER:$USER nginx/ssl
```

#### Option B: Self-Signed (Development/Testing Only)

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem
```

### 4. Update Nginx Configuration

Edit `frontend/nginx.conf` to enable HTTPS:

```nginx
# Uncomment the HTTPS server block
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... rest of configuration
}
```

### 5. Database Initialization

The database will be automatically initialized on first run. Migrations will be applied automatically.

## Deployment Process

### Quick Deployment

Use the automated deployment script:

```bash
cd scripts/deployment
./deploy.sh production
```

The script will:
1. Run pre-flight checks
2. Create database backup
3. Pull/build Docker images
4. Start all services
5. Run database migrations
6. Perform health checks

### Manual Deployment

If you prefer manual control:

#### 1. Build Images

```bash
docker-compose -f docker-compose.prod.yml --env-file .env.production build
```

#### 2. Start Services

```bash
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
```

#### 3. Run Migrations

```bash
docker-compose -f docker-compose.prod.yml --env-file .env.production exec onside-api-prod \
  alembic upgrade head
```

#### 4. Verify Health

```bash
./scripts/deployment/health-check.sh production
```

## Post-Deployment

### 1. Verify Services

Check all services are running:

```bash
docker-compose -f docker-compose.prod.yml ps
```

Expected output:
```
NAME                    STATUS          PORTS
onside-api-prod         Up (healthy)    0.0.0.0:8000->8000/tcp
onside-celery-beat      Up              
onside-celery-worker    Up              
onside-db-prod          Up (healthy)    0.0.0.0:5432->5432/tcp
onside-flower           Up              0.0.0.0:5555->5555/tcp
onside-frontend         Up (healthy)    0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
onside-minio-prod       Up (healthy)    0.0.0.0:9000-9001->9000-9001/tcp
onside-redis-prod       Up (healthy)    0.0.0.0:6379->6379/tcp
```

### 2. Test Endpoints

```bash
# Frontend
curl -I http://localhost/

# API Health
curl http://localhost:8000/health

# API Docs
curl http://localhost:8000/docs

# Flower
curl http://localhost:5555/
```

### 3. Create Admin User

```bash
docker-compose -f docker-compose.prod.yml exec onside-api-prod \
  python -m src.scripts.create_admin_user
```

### 4. Configure Monitoring

#### Flower (Celery Monitoring)

Access at: `http://your-domain.com:5555`

Username/Password: Set in `FLOWER_BASIC_AUTH` environment variable

#### MinIO Console

Access at: `http://your-domain.com:9001`

Username: `MINIO_ACCESS_KEY`
Password: `MINIO_SECRET_KEY`

### 5. Setup Automated Backups

Configure cron job for daily backups:

```bash
crontab -e
```

Add:
```cron
# Daily backup at 2 AM
0 2 * * * /path/to/onside/scripts/deployment/backup.sh production full >> /var/log/onside-backup.log 2>&1
```

## Monitoring & Maintenance

### Logs

View logs for specific services:

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f onside-api-prod

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 onside-api-prod
```

### Resource Monitoring

```bash
# Container resource usage
docker stats

# Disk usage
docker system df
```

### Database Maintenance

```bash
# Vacuum database
docker-compose -f docker-compose.prod.yml exec onside-db-prod \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM ANALYZE;"

# Check database size
docker-compose -f docker-compose.prod.yml exec onside-db-prod \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT pg_size_pretty(pg_database_size('$POSTGRES_DB'));"
```

### Updates

To update to a new version:

```bash
# Pull latest code
git pull origin main

# Backup before update
./scripts/deployment/backup.sh production full

# Rebuild and restart
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d --build

# Run new migrations
docker-compose -f docker-compose.prod.yml exec onside-api-prod alembic upgrade head

# Verify health
./scripts/deployment/health-check.sh production
```

### Rollback

If something goes wrong:

```bash
# List available backups
ls -lht backups/

# Rollback to specific backup
./scripts/deployment/rollback.sh production backups/20231223-120000
```

## Performance Tuning

### PostgreSQL Optimization

Edit `docker-compose.prod.yml` PostgreSQL command section to adjust:
- `shared_buffers`: 25% of total RAM
- `effective_cache_size`: 50-75% of total RAM
- `work_mem`: Adjust based on concurrent queries

### Redis Optimization

Adjust `maxmemory` in Redis command:
```yaml
command: >
  sh -c "redis-server
  --maxmemory 4gb  # Adjust based on available RAM
  --maxmemory-policy allkeys-lru"
```

### Celery Workers

Scale workers based on load:
```yaml
deploy:
  replicas: 4  # Increase number of workers
```

Or adjust concurrency:
```bash
CELERY_WORKER_CONCURRENCY=8  # In .env.production
```

## Security Checklist

- [ ] Strong passwords for all services
- [ ] SSL/TLS certificates configured
- [ ] Firewall rules configured
- [ ] CORS origins properly set
- [ ] API rate limiting enabled
- [ ] Regular security updates
- [ ] Backups encrypted and stored securely
- [ ] Access logs reviewed regularly
- [ ] Secret keys rotated periodically

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting guide.

## Support

For issues or questions:
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review logs: `docker-compose logs`
- Contact: support@your-domain.com

## Additional Resources

- [Production Checklist](PRODUCTION_CHECKLIST.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [API Documentation](http://localhost:8000/docs)
- [Architecture Overview](ARCHITECTURE.md)
