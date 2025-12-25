# OnSide Architecture Reference

## System Overview

OnSide is an AI-driven competitive intelligence platform that generates comprehensive reports with market analysis, competitor insights, and audience intelligence.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+, FastAPI |
| **Database** | PostgreSQL (production), SQLite (development) |
| **ORM** | SQLAlchemy with async support |
| **Caching** | Redis |
| **Task Queue** | Celery |
| **Object Storage** | MinIO |
| **Containerization** | Docker, Docker Compose |
| **AI/LLM** | OpenAI, Anthropic (with fallback) |

## Directory Structure

```
OnSide/
├── .claude/                 # Claude Code configuration & rules
├── alembic/                 # Database migrations
│   └── versions/            # Migration scripts
├── config/                  # Application configuration
├── dags/                    # Airflow DAG definitions
├── docs/                    # Project documentation
├── scripts/                 # Utility scripts
├── src/                     # Source code
│   ├── api/                 # API layer
│   │   ├── routes/          # Legacy routes
│   │   └── v1/              # Versioned API endpoints
│   ├── auth/                # Authentication services
│   ├── config/              # Configuration management
│   ├── core/                # Core utilities
│   ├── database/            # Database connections
│   ├── middleware/          # Request middleware
│   ├── models/              # SQLAlchemy models
│   ├── repositories/        # Data access layer
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   │   ├── ai/              # AI/ML services
│   │   ├── analytics/       # Analytics services
│   │   ├── audience/        # Audience analysis
│   │   ├── content/         # Content services
│   │   ├── data/            # Data processing
│   │   ├── engagement/      # Engagement tracking
│   │   ├── external_api/    # External API adapters
│   │   ├── llm_provider/    # LLM integration
│   │   ├── seo/             # SEO services
│   │   └── web_scraper/     # Web scraping
│   └── utils/               # Utility functions
└── tests/                   # Test suites
    ├── api/                 # API tests
    ├── integration/         # Integration tests
    ├── models/              # Model tests
    ├── performance/         # Performance tests
    ├── services/            # Service tests
    └── unit/                # Unit tests
```

## Core Components

### 1. API Layer (`src/api/v1/`)
- RESTful endpoints using FastAPI
- Versioned under `/api/v1/`
- Pydantic models for request/response validation
- OpenAPI documentation auto-generated

### 2. Service Layer (`src/services/`)
Business logic organized by domain:

| Service | Purpose |
|---------|---------|
| `analytics/` | Market and competitive analysis |
| `external_api/` | GNews, IPInfo, WhoAPI adapters |
| `llm_provider/` | LLM integration with fallback |
| `seo/` | SEO scoring and trend analysis |
| `web_scraper/` | Competitor data collection |

### 3. Data Layer (`src/repositories/`)
Repository pattern for data access:
- `gnews_repository.py` - News article storage
- `ipinfo_repository.py` - IP geolocation data
- `whoapi_repository.py` - WHOIS data
- `api_usage_repository.py` - API quota tracking
- `competitor_repository.py` - Competitor data
- `domain_repository.py` - Domain information

### 4. Models (`src/models/`)
SQLAlchemy models:
- `external_api.py` - GNewsArticle, IPInfoRecord, WhoisRecord, APIUsageRecord
- `competitor.py` - Competitor, CompetitorContent
- `domain.py` - Domain information
- `report.py` - Report generation tracking
- `user.py` - User management

## Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Client    │────▶│  FastAPI     │────▶│   Services      │
│   Request   │     │  Router      │     │   Layer         │
└─────────────┘     └──────────────┘     └─────────────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────────────┐
                    │                             │                             │
                    ▼                             ▼                             ▼
            ┌───────────────┐            ┌───────────────┐            ┌───────────────┐
            │  External     │            │  Repository   │            │    LLM        │
            │  APIs         │            │  Layer        │            │  Providers    │
            │ (GNews, etc)  │            │               │            │               │
            └───────────────┘            └───────────────┘            └───────────────┘
                                                  │
                                                  ▼
                                         ┌───────────────┐
                                         │  PostgreSQL   │
                                         │  Database     │
                                         └───────────────┘
```

## External API Integrations

### Implemented

| API | Service | Purpose |
|-----|---------|---------|
| GNews | `gnews_service.py` | News monitoring, competitor mentions |
| IPInfo | `ipinfo_service.py` | IP geolocation, regional analysis |
| WhoAPI | `whoapi_service.py` | WHOIS, SSL, DNS, tech stack |
| Google Analytics | `google_analytics.py` | Web analytics |
| Google Search Console | `google_search_console.py` | SEO metrics |

### Configuration
All API keys stored in environment variables:
- `GNEWS_API_KEY`
- `IPINFO_API_KEY`
- `WHOAPI_API_KEY`
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

## AI/LLM Architecture

### Provider Hierarchy
1. **Primary**: OpenAI (GPT-4)
2. **Fallback 1**: Anthropic (Claude)
3. **Fallback 2**: Cohere
4. **Fallback 3**: HuggingFace

### Chain-of-Thought Reasoning
All AI services implement:
- Step-by-step reasoning capture
- Confidence scoring
- Transparent decision logging

### Fallback System
Located in `src/services/llm_provider/`:
- `fallback_manager.py` - Orchestrates provider fallback
- `enhanced_recovery.py` - Advanced recovery strategies

## Database Schema

### Key Tables
- `users` - User accounts
- `companies` - Company profiles
- `competitors` - Competitor data
- `domains` - Domain information
- `gnews_articles` - News articles
- `ipinfo_records` - IP geolocation
- `whois_records` - WHOIS data
- `api_usage_records` - API quota tracking
- `reports` - Generated reports

### Migrations
Use Alembic for all schema changes:
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Caching Strategy

### Redis Cache
- API response caching
- Session storage
- Rate limit tracking

### TTL Configuration
| Data Type | TTL |
|-----------|-----|
| WHOIS data | 24 hours |
| IP info | 24 hours |
| News articles | 1 hour |
| DNS records | 1 hour |

## Error Handling

### Standard Pattern
```python
try:
    result = await service.operation()
except ServiceSpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.exception("Unexpected error")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Retry Logic
External API calls use exponential backoff:
- Max retries: 3
- Base delay: 1 second
- Max delay: 30 seconds

## Performance Considerations

### Async Operations
- All database operations use async SQLAlchemy
- External API calls use httpx async client
- Concurrent processing with `asyncio.gather`

### Batch Processing
- Competitor analysis batched (5 at a time)
- News fetching parallelized
- Report generation uses thread pool for PDF

### Monitoring
- APM configuration in `src/monitoring/apm_config.py`
- Performance telemetry for all services
- API usage tracking and quota management
