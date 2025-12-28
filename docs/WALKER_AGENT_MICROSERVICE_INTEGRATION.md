# Walker Agent Microservice Integration Guide

## Overview

This document describes how OnSide integrates with En Garde's Walker Agent microservices using Airflow as the ETL processing engine, MinIO for object storage, and PostgreSQL as the data lakehouse database.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    En Garde Production                      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │               Walker Agents                          │  │
│  │  • Paid Ads Agent                                    │  │
│  │  • SEO Agent                                         │  │
│  │  • Content Generation Agent                          │  │
│  │  • Audience Intelligence Agent                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         │ API Requests                      │
│                         ▼                                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ HTTP/REST
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    OnSide Microservice                      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            FastAPI Application                       │  │
│  │  • REST API Endpoints (/api/v1/*)                    │  │
│  │  • Authentication (JWT)                              │  │
│  │  • Request Validation                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Apache Airflow (ETL Engine)                  │  │
│  │  • Data Ingestion DAGs                               │  │
│  │  • Analytics Pipeline DAGs                           │  │
│  │  • SEO Pipeline DAG (Walker Agent)                   │  │
│  │  • Task Scheduling & Orchestration                   │  │
│  └──────────────────────────────────────────────────────┘  │
│           │                  │                  │           │
│           ▼                  ▼                  ▼           │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
│  │   MinIO     │   │ PostgreSQL  │   │   Redis     │      │
│  │  (Object    │   │  (Lakehouse │   │  (Cache &   │      │
│  │   Storage)  │   │    & DB)    │   │   Queue)    │      │
│  └─────────────┘   └─────────────┘   └─────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

### ETL Processing: Apache Airflow
- **DAG-based workflow orchestration**
- **Scheduled task execution**
- **Retry logic and error handling**
- **Task dependency management**
- **XCom for inter-task communication**

### Object Storage: MinIO
- **S3-compatible object storage**
- **Bucket organization by data type**
- **JSON data storage for ETL intermediates**
- **Report storage and archival**

### Database: PostgreSQL
- **Data lakehouse for structured analytics**
- **Time-series SEO metrics**
- **Aggregated reporting tables**
- **Historical trend data**

### Task Queue: Celery + Redis
- **Asynchronous task processing**
- **Background job execution**
- **API request queuing**

## Configuration

### Environment Variables

OnSide requires the following environment variables for Walker Agent integration:

```bash
# Airflow Configuration (Implicit - DAGs in dags/ directory)
# Airflow reads DAGs from the dags/ directory automatically

# MinIO Object Storage
MINIO_ENDPOINT=onside-minio:9000
MINIO_ACCESS_KEY=your-minio-access-key
MINIO_SECRET_KEY=your-minio-secret-key

# PostgreSQL Lakehouse
DATABASE_URL=postgresql://postgres:password@onside-db:5432/onside

# Redis (Task Queue & Caching)
REDIS_URL=redis://onside-redis:6379/0
CELERY_BROKER_URL=redis://onside-redis:6379/0
CELERY_RESULT_BACKEND=redis://onside-redis:6379/0

# EnGarde Production Backend Integration
ENGARDE_API_URL=https://api.engarde.com
ENGARDE_API_KEY=your-engarde-api-key
ENGARDE_TENANT_UUID=your-tenant-uuid
ENGARDE_API_TIMEOUT=30
```

### Docker Compose Services

OnSide microservice runs with the following services:

```yaml
services:
  onside-api:         # FastAPI application (port 8000)
  onside-db:          # PostgreSQL database (port 5432)
  onside-redis:       # Redis cache/queue (port 6379)
  onside-minio:       # MinIO object storage (ports 9000, 9001)
  onside-celery-worker:   # Celery worker for async tasks
  onside-celery-beat:     # Celery scheduler
  onside-flower:      # Celery monitoring UI (port 5555)
```

## Airflow DAG Structure

### Existing DAGs

1. **`data_ingestion_dag.py`** - Daily data ingestion from external APIs
   - Schedule: `0 3 * * *` (3 AM daily)
   - Sources: Google Analytics, Meltwater, WhoAPI, GNews
   - Output: Raw data to MinIO buckets

2. **`analytics_pipeline_dag.py`** - Daily analytics processing
   - Schedule: `0 4 * * *` (4 AM daily, after ingestion)
   - Tasks: Content processing, engagement metrics, trend analysis
   - Output: Analytics tables in PostgreSQL

3. **`seo_pipeline_dag.py`** - SEO Walker Agent pipeline (NEW)
   - Schedule: `0 5 * * *` (5 AM daily, after analytics)
   - Tasks: SERP data, PageSpeed metrics, WHOIS, competitor analysis
   - Output: SEO scores, recommendations, Walker Agent notifications

### Creating Additional Walker Agent DAGs

To create DAGs for other Walker Agents (Paid Ads, Content, Audience Intelligence), follow this pattern:

```python
"""
{Walker Agent Name} Pipeline DAG

This DAG processes {description} for the Walker Agent {type} microservice:
- Data collection from relevant APIs
- Metrics calculation and analysis
- Data storage to MinIO buckets
- Results stored in PostgreSQL lakehouse
- Walker Agent notifications
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.task_group import TaskGroup

# 1. Define data collection functions
def collect_primary_data(**context):
    """Collect primary data from external APIs"""
    # Implementation here
    pass

# 2. Define analysis functions
def analyze_metrics(**context):
    """Analyze collected metrics"""
    # Implementation here
    pass

# 3. Define aggregation function
def aggregate_results(**context):
    """Aggregate results for storage"""
    # Implementation here
    pass

# 4. Define Walker Agent notification function
def notify_walker_agent(**context):
    """Send insights to Walker Agent channels"""
    # Implementation here
    pass

# 5. Configure DAG
default_args = {
    'owner': 'walker-agent',
    'depends_on_past': True,
    'start_date': datetime(2025, 1, 1),
    'email': ['{agent-type}-walker@engarde.media'],
    'email_on_failure': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

dag = DAG(
    '{agent_type}_walker_agent_pipeline',
    default_args=default_args,
    description='{Agent Type} Walker Agent pipeline',
    schedule_interval='0 {hour} * * *',  # Schedule appropriately
    catchup=False,
    tags=['walker-agent', '{agent-type}', 'microservice'],
    max_active_runs=1,
)

# 6. Define task dependencies
start >> data_collection_group >> analysis >> aggregate >> notify >> end
```

## MinIO Bucket Organization

OnSide uses MinIO buckets to organize data by Walker Agent type:

```
minio://
├── seo-data/                    # SEO Walker Agent
│   ├── serp/
│   │   └── YYYYMMDD/
│   │       └── rankings.json
│   ├── pagespeed/
│   │   └── YYYYMMDD/
│   │       └── metrics.json
│   └── whois/
│       └── YYYYMMDD/
│           └── domains.json
├── seo-reports/                 # SEO reports
│   └── YYYYMMDD/
│       └── daily_report.json
├── paid-ads-data/               # Paid Ads Walker Agent
│   ├── google-ads/
│   ├── meta-ads/
│   └── linkedin-ads/
├── content-data/                # Content Generation Walker Agent
│   ├── generated-content/
│   └── performance-metrics/
└── audience-data/               # Audience Intelligence Walker Agent
    ├── behavior-analysis/
    └── segmentation/
```

### MinIO Python Client Example

```python
from minio import Minio
import json
import os

class MinIOService:
    def __init__(self):
        self.client = Minio(
            endpoint=os.getenv('MINIO_ENDPOINT'),
            access_key=os.getenv('MINIO_ACCESS_KEY'),
            secret_key=os.getenv('MINIO_SECRET_KEY'),
            secure=False  # Set True for HTTPS
        )

    def ensure_bucket(self, bucket_name: str):
        """Create bucket if it doesn't exist"""
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def upload_json(self, bucket: str, object_name: str, data: dict):
        """Upload JSON data to MinIO"""
        self.ensure_bucket(bucket)
        json_bytes = json.dumps(data).encode('utf-8')
        self.client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=io.BytesIO(json_bytes),
            length=len(json_bytes),
            content_type='application/json'
        )

    def get_json(self, bucket: str, object_name: str) -> dict:
        """Retrieve JSON data from MinIO"""
        response = self.client.get_object(bucket, object_name)
        return json.loads(response.read())
```

## PostgreSQL Lakehouse Schema

### SEO Walker Agent Tables

```sql
-- SEO scores over time
CREATE TABLE seo_scores (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    domain VARCHAR(255) NOT NULL,
    visibility_score DECIMAL(5, 2),
    performance_score DECIMAL(5, 2),
    authority_score DECIMAL(5, 2),
    overall_score DECIMAL(5, 2),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, domain)
);

CREATE INDEX idx_seo_scores_date ON seo_scores(date);
CREATE INDEX idx_seo_scores_domain ON seo_scores(domain);

-- SEO recommendations
CREATE TABLE seo_recommendations (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    domain VARCHAR(255) NOT NULL,
    opportunity_type VARCHAR(100),
    priority VARCHAR(20),  -- 'high', 'medium', 'low'
    recommendation TEXT,
    expected_impact VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_seo_recommendations_date ON seo_recommendations(date);
CREATE INDEX idx_seo_recommendations_status ON seo_recommendations(status);

-- Keyword rankings
CREATE TABLE keyword_rankings (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    keyword VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    position INTEGER,
    search_volume INTEGER,
    serp_features JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, keyword, domain)
);

CREATE INDEX idx_keyword_rankings_date ON keyword_rankings(date);
CREATE INDEX idx_keyword_rankings_keyword ON keyword_rankings(keyword);

-- Competitor analysis
CREATE TABLE competitor_seo_analysis (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    competitor_domain VARCHAR(255) NOT NULL,
    our_domain VARCHAR(255) NOT NULL,
    visibility_gap DECIMAL(5, 2),
    keyword_overlap JSONB,
    content_gaps JSONB,
    backlink_comparison JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, competitor_domain, our_domain)
);

CREATE INDEX idx_competitor_analysis_date ON competitor_seo_analysis(date);
```

### Creating Tables for Other Walker Agents

Follow this pattern for Paid Ads, Content, and Audience Intelligence agents:

```sql
-- {Walker Agent Type} metrics
CREATE TABLE {agent_type}_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    entity_id VARCHAR(255) NOT NULL,  -- campaign_id, content_id, segment_id
    metric_type VARCHAR(100),
    metric_value DECIMAL(15, 2),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, entity_id, metric_type)
);

-- {Walker Agent Type} recommendations
CREATE TABLE {agent_type}_recommendations (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    recommendation_type VARCHAR(100),
    priority VARCHAR(20),
    recommendation TEXT,
    expected_impact VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Walker Agent Notification Integration

### Notification Flow

1. **DAG Completion**: Airflow DAG completes analysis tasks
2. **Aggregation**: Results aggregated and stored in MinIO/PostgreSQL
3. **Notification Task**: Final DAG task triggers Walker Agent notification
4. **En Garde API Call**: OnSide calls En Garde backend API
5. **Walker Agent Channels**: En Garde routes to configured channels (WhatsApp, Email)

### Implementation Pattern

```python
import requests
import os

class WalkerAgentNotificationService:
    def __init__(self):
        self.api_url = os.getenv('ENGARDE_API_URL')
        self.api_key = os.getenv('ENGARDE_API_KEY')
        self.tenant_uuid = os.getenv('ENGARDE_TENANT_UUID')

    def send_daily_insights(self, agent_type: str, report: dict, execution_date):
        """Send daily insights to Walker Agent"""

        # Format insights for human-readable message
        message = self._format_insights_message(report)

        # Call En Garde API to send notification
        response = requests.post(
            f'{self.api_url}/v1/walker-agents/{agent_type}/notify',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'X-Tenant-UUID': self.tenant_uuid
            },
            json={
                'notification_type': 'daily_insights',
                'message': message,
                'report_data': report,
                'execution_date': execution_date.isoformat()
            }
        )

        return response.json()

    def send_alerts(self, agent_type: str, critical_issues: list):
        """Send critical alerts to Walker Agent"""

        for issue in critical_issues:
            requests.post(
                f'{self.api_url}/v1/walker-agents/{agent_type}/alert',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'X-Tenant-UUID': self.tenant_uuid
                },
                json={
                    'alert_type': issue['type'],
                    'severity': 'critical',
                    'message': issue['message'],
                    'metadata': issue.get('metadata', {})
                }
            )
```

## API Endpoints for Walker Agents

OnSide exposes these endpoints for En Garde Walker Agents:

```
GET  /api/v1/seo/rankings/{domain}
GET  /api/v1/seo/scores/{domain}
GET  /api/v1/seo/recommendations/{domain}
GET  /api/v1/seo/competitors/{domain}

POST /api/v1/seo/track-keyword
POST /api/v1/seo/track-competitor

# Similar patterns for other agents:
# /api/v1/paid-ads/*
# /api/v1/content/*
# /api/v1/audience/*
```

## Deployment Checklist

### Initial Setup

- [ ] Configure environment variables in `.env`
- [ ] Start Docker Compose services: `docker-compose up -d`
- [ ] Verify PostgreSQL is running: `docker exec onside-db pg_isready`
- [ ] Verify MinIO is accessible: `curl http://localhost:9001`
- [ ] Verify Redis is running: `docker exec onside-redis redis-cli ping`

### Airflow Setup

- [ ] Access Airflow UI (if running): Usually configured separately
- [ ] Place DAG files in `dags/` directory
- [ ] Verify DAGs are detected: Check Airflow UI or logs
- [ ] Enable DAGs for Walker Agents
- [ ] Configure DAG schedules and dependencies

### Database Setup

- [ ] Run Alembic migrations: `alembic upgrade head`
- [ ] Create Walker Agent tables (see schema above)
- [ ] Verify table creation: `docker exec onside-db psql -U postgres -d onside -c "\dt"`

### MinIO Setup

- [ ] Access MinIO Console: `http://localhost:9001`
- [ ] Login with MINIO_ROOT_USER/MINIO_ROOT_PASSWORD
- [ ] Create buckets for each Walker Agent
- [ ] Configure bucket policies if needed

### Testing

- [ ] Test OnSide API endpoints: `curl http://localhost:8000/health`
- [ ] Manually trigger test DAG run
- [ ] Verify data written to MinIO buckets
- [ ] Verify data written to PostgreSQL tables
- [ ] Test Walker Agent notification integration

## Monitoring and Maintenance

### Key Metrics to Monitor

1. **Airflow DAG Success Rate**
   - Monitor failed DAG runs
   - Check task retry patterns
   - Review execution times

2. **MinIO Storage Usage**
   - Monitor bucket sizes
   - Implement data retention policies
   - Archive old data

3. **PostgreSQL Performance**
   - Query performance
   - Table sizes
   - Index usage

4. **API Response Times**
   - OnSide API latency
   - External API rate limits
   - Error rates

### Maintenance Tasks

- **Daily**: Monitor DAG execution logs
- **Weekly**: Review MinIO storage usage, archive old data
- **Monthly**: Optimize PostgreSQL indexes, vacuum tables
- **Quarterly**: Review and update data retention policies

## Troubleshooting

### Common Issues

**Issue**: DAG not appearing in Airflow
- **Solution**: Verify DAG file syntax, check Airflow logs, ensure file in `dags/` directory

**Issue**: MinIO connection refused
- **Solution**: Check MinIO service status, verify endpoint configuration, check network connectivity

**Issue**: PostgreSQL connection timeout
- **Solution**: Verify database service running, check DATABASE_URL format, verify credentials

**Issue**: Walker Agent notifications not sending
- **Solution**: Verify ENGARDE_API_URL, check API key validity, review notification service logs

## References

- [OnSide Architecture Documentation](./architecture.md)
- [SEO Service Implementation Plan](./seo_service_implementation_plan.md)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [MinIO Python Client Documentation](https://min.io/docs/minio/linux/developers/python/minio-py.html)
- [En Garde Walker Agent Integration Guide](/Users/cope/EnGardeHQ/production-frontend/docs/WALKER_AGENT_AD_BUDGET_INTEGRATION.md)
