# OnSide Infrastructure Quick Start Guide

This guide will help you quickly get started with the newly implemented infrastructure.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+
- AWS CLI configured (for cloud deployment)
- Terraform installed (for infrastructure deployment)

## Local Development Setup

### 1. Install Dependencies

```bash
cd /Users/cope/EnGardeHQ/Onside
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your local configuration
# For local development, the defaults should work
```

### 3. Start Infrastructure Services

```bash
# Start all services (API, PostgreSQL, Redis, MinIO, Celery, Flower)
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Access Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Flower (Celery Monitor)**: http://localhost:5555 (admin/admin)
- **MinIO Console**: http://localhost:9001 (minio-access-key/minio-secret-key)
- **PostgreSQL**: localhost:5432 (postgres/onside-dev-password)
- **Redis**: localhost:6379

### 5. Test Celery Tasks

```python
from src.tasks.report_tasks import generate_report_task

# Queue a test report generation task
result = generate_report_task.delay(
    tenant_id="test_tenant",
    report_type="competitor",
    report_config={"period": "weekly"}
)

# Check task status
print(f"Task ID: {result.id}")
print(f"Task State: {result.state}")

# Get result (blocking)
report = result.get(timeout=60)
print(report)
```

### 6. Monitor Tasks in Flower

1. Open http://localhost:5555
2. Login with admin/admin
3. View tasks, workers, and queues

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## CI/CD Setup

### 1. Configure GitHub Secrets

Go to GitHub Repository → Settings → Secrets and variables → Actions

Add the following secrets:

```
# AWS Credentials
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION

# Application Secrets
SECRET_KEY
MINIO_ACCESS_KEY
MINIO_SECRET_KEY

# Database (for staging/production)
DATABASE_URL

# Notifications
ALARM_EMAIL

# Optional: Railway (if using Railway instead of AWS)
RAILWAY_TOKEN
```

### 2. Enable GitHub Actions

GitHub Actions workflows are already configured in `.github/workflows/`

- CI runs automatically on push/PR
- Staging deployment runs on push to `develop` branch
- Production deployment runs on release creation

### 3. Create First Release

```bash
# Tag a release
git tag -a v1.0.0 -m "First production release"
git push origin v1.0.0

# Or create release via GitHub UI
```

## AWS Deployment

### 1. Prepare Terraform Backend

```bash
# Create S3 bucket for Terraform state
aws s3 mb s3://onside-terraform-state-$(aws sts get-caller-identity --query Account --output text)

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name onside-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### 2. Configure Environment

```bash
cd terraform/environments/dev

# Create backend.hcl
cat > backend.hcl << EOF
bucket         = "onside-terraform-state-ACCOUNT_ID"
key            = "onside/dev/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "onside-terraform-locks"
encrypt        = true
EOF

# Create terraform.tfvars
cat > terraform.tfvars << EOF
environment = "dev"
aws_region  = "us-east-1"

# VPC
vpc_cidr = "10.0.0.0/16"

# RDS
rds_instance_class = "db.t3.micro"
rds_allocated_storage = 20
rds_multi_az = false

# Redis
redis_node_type = "cache.t3.micro"
redis_num_cache_nodes = 1

# ECS
ecs_task_cpu = "512"
ecs_task_memory = "1024"
ecs_desired_count = 2

# Secrets (use environment variables instead)
alarm_email = "alerts@yourcompany.com"
EOF
```

### 3. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init -backend-config=backend.hcl

# Review planned changes
terraform plan -var-file=terraform.tfvars

# Apply infrastructure
terraform apply -var-file=terraform.tfvars

# Note the outputs
terraform output
```

### 4. Deploy Application

After infrastructure is created, deploy the application:

```bash
# Build and push Docker image
docker build -t onside-api:latest .
docker tag onside-api:latest ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/onside-api:latest
docker push ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/onside-api:latest

# Update ECS service
aws ecs update-service \
  --cluster onside-dev \
  --service onside-api \
  --force-new-deployment
```

## Airflow Setup

### 1. Install Airflow (Local)

```bash
# Install Airflow
pip install apache-airflow==2.7.0

# Initialize Airflow database
airflow db init

# Create admin user
airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password admin

# Start Airflow webserver
airflow webserver --port 8080

# In another terminal, start scheduler
airflow scheduler
```

### 2. Access Airflow UI

- URL: http://localhost:8080
- Username: admin
- Password: admin

### 3. Enable DAGs

1. Copy DAGs to Airflow folder:
   ```bash
   cp dags/*.py ~/airflow/dags/
   ```

2. Refresh DAGs in UI or wait for auto-refresh

3. Enable the DAGs:
   - data_ingestion_pipeline
   - analytics_pipeline
   - weekly_report_generation

## MinIO/S3 Storage Setup

### Local (MinIO)

MinIO is already configured in docker-compose.yml

Access console at http://localhost:9001

### Production (AWS S3)

S3 buckets are created automatically by Terraform

Update application configuration to use S3:

```python
# In .env or environment variables
MINIO_ENDPOINT=s3.us-east-1.amazonaws.com
MINIO_ACCESS_KEY=AWS_ACCESS_KEY_ID
MINIO_SECRET_KEY=AWS_SECRET_ACCESS_KEY
MINIO_SECURE=true
```

## GraphDB Setup

### 1. Install Neo4j (Local)

```bash
# Add Neo4j to docker-compose.yml or run standalone
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.15.0
```

### 2. Access Neo4j Browser

- URL: http://localhost:7474
- Username: neo4j
- Password: password

### 3. Initialize Schema

```python
from src.services.graphdb_service import GraphDBService, initialize_schema

# Connect to Neo4j
graphdb = GraphDBService(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password"
)

# Initialize schema
initialize_schema(graphdb)
```

### 4. Test GraphDB

```python
# Create test company
company = graphdb.create_company(
    tenant_id="test",
    company_id="test_company",
    name="Test Company",
    domain="test.com"
)

# Create competitor
competitor = graphdb.create_competitor(
    tenant_id="test",
    competitor_id="test_competitor",
    name="Competitor Co",
    domain="competitor.com"
)

# Create relationship
graphdb.create_relationship(
    from_id="test_company",
    to_id="test_competitor",
    relationship_type="COMPETES_WITH"
)

# Query competitors
competitors = graphdb.find_competitors(
    tenant_id="test",
    company_id="test_company"
)
print(competitors)
```

## Monitoring and Debugging

### View Logs

```bash
# API logs
docker-compose logs -f onside-api

# Celery worker logs
docker-compose logs -f onside-celery-worker

# Celery beat logs
docker-compose logs -f onside-celery-beat

# All services
docker-compose logs -f
```

### Monitor Resources

```bash
# Docker stats
docker stats

# Specific service
docker stats onside-api
```

### Debug Celery Tasks

1. Open Flower: http://localhost:5555
2. Click on "Tasks"
3. Find your task by ID or name
4. View execution details, arguments, and traceback

### Check Redis

```bash
# Connect to Redis CLI
docker exec -it onside-redis redis-cli

# Check queue lengths
LLEN celery

# Monitor commands
MONITOR
```

### Check PostgreSQL

```bash
# Connect to PostgreSQL
docker exec -it onside-db psql -U postgres -d onside

# List tables
\dt

# Query data
SELECT * FROM users LIMIT 10;
```

## Common Tasks

### Run Database Migrations

```bash
# Run migrations
docker-compose exec onside-api alembic upgrade head

# Create new migration
docker-compose exec onside-api alembic revision --autogenerate -m "description"
```

### Trigger Celery Task Manually

```python
from src.tasks.report_tasks import generate_weekly_reports

# Trigger immediate execution
result = generate_weekly_reports.delay()
print(f"Task ID: {result.id}")
```

### Clear Cache

```python
from src.core.cache import cache

# Clear all cache
cache.clear()

# Clear specific pattern
cache.clear(pattern="user:*")
```

### Backup Database

```bash
# Create backup
docker exec onside-db pg_dump -U postgres onside > backup_$(date +%Y%m%d).sql

# Restore backup
cat backup_20250122.sql | docker exec -i onside-db psql -U postgres -d onside
```

## Troubleshooting

### Celery Workers Not Starting

```bash
# Check Redis connection
docker exec -it onside-redis redis-cli ping

# Check worker logs
docker-compose logs onside-celery-worker

# Restart workers
docker-compose restart onside-celery-worker
```

### Tasks Stuck in Pending

```bash
# Check if workers are running
docker-compose ps | grep celery

# Check queue in Redis
docker exec -it onside-redis redis-cli LLEN celery

# Purge queue (caution!)
docker-compose exec onside-api celery -A src.celery_app purge
```

### MinIO Connection Issues

```bash
# Check MinIO is running
curl http://localhost:9000/minio/health/live

# Test from Python
from src.services.storage_service import storage_service
result = storage_service.list_files("onside-reports")
print(result)
```

### Terraform Apply Fails

```bash
# Check AWS credentials
aws sts get-caller-identity

# Refresh Terraform state
terraform refresh

# Targeted apply
terraform apply -target=module.vpc
```

## Next Steps

1. **Implement Business Logic**: Replace placeholder functions in tasks
2. **Configure External APIs**: Add API keys for Google Analytics, Meltwater, etc.
3. **Set Up Monitoring**: Configure CloudWatch alarms and dashboards
4. **Performance Testing**: Load test the application
5. **Security Audit**: Review and harden security configurations
6. **Documentation**: Create user guides and API documentation

## Support

For issues or questions:
- Check logs: `docker-compose logs`
- Review documentation: `INFRASTRUCTURE_IMPLEMENTATION_REPORT.md`
- Check Terraform docs: `terraform/README.md`
- Open GitHub issue for bugs

## Resources

- [Celery Documentation](https://docs.celeryq.dev/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [MinIO Documentation](https://min.io/docs/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [Airflow Documentation](https://airflow.apache.org/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
