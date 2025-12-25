# Docker Setup Guide

This guide explains how to run OnSide using Docker containers.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

1. Clone the repository and set up environment:
   ```bash
   git clone https://github.com/Open-Cap-Stack/OnSide.git
   cd OnSide
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

2. Start all services:
   ```bash
   docker-compose up -d
   ```

3. Verify the services are running:
   ```bash
   docker-compose ps
   ```

4. Access the API:
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - MinIO Console: http://localhost:9001

## Docker Services

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| onside-api | onside-api | 8000 | FastAPI application |
| onside-db | onside-db | 5432 | PostgreSQL database |
| onside-redis | onside-redis | 6379 | Redis cache |
| onside-minio | onside-minio | 9000, 9001 | MinIO object storage |

## Common Commands

```bash
# Start all services
docker-compose up -d

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f onside-api

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Rebuild and start (after code changes)
docker-compose up -d --build

# Run database migrations
docker-compose exec onside-api alembic upgrade head

# Access database shell
docker-compose exec onside-db psql -U postgres -d onside

# Run tests in container
docker-compose exec onside-api pytest tests/ -v

# Access API container shell
docker-compose exec onside-api /bin/bash
```

## Production Deployment

For production, use the production compose file:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Production Differences

- Uses production Dockerfile target (no dev tools)
- Resource limits configured for each service
- Stricter restart policies (always)
- JSON file logging with rotation
- No port exposure for database (internal only)

### Production Environment Variables

Make sure to set these in your .env file for production:

```bash
DATABASE_URL=postgresql://user:password@onside-db:5432/onside
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_secure_password
SECRET_KEY=your_production_secret_key
MINIO_ACCESS_KEY=your_minio_access_key
MINIO_SECRET_KEY=your_minio_secret_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

## Health Checks

All services include health checks:

- **API**: `curl http://localhost:8000/health`
- **PostgreSQL**: `pg_isready -U postgres -d onside`
- **Redis**: `redis-cli ping`
- **MinIO**: `curl http://localhost:9000/minio/health/live`

## Troubleshooting

### Container fails to start
```bash
docker-compose logs onside-api
```

### Database connection issues
```bash
docker-compose exec onside-db psql -U postgres -d onside -c "SELECT 1"
```

### Reset everything
```bash
docker-compose down -v
docker-compose up -d --build
```

### Rebuild single service
```bash
docker-compose up -d --build onside-api
```

