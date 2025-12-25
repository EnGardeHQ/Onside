# Import Service Migration Guide

## Overview

This guide helps you integrate the Import Service with the En Garde production database. It provides SQL migrations, configuration steps, and deployment instructions.

## Prerequisites

- En Garde production database credentials
- Onside database access (already configured)
- Understanding of your deployment architecture (single DB vs. microservices)

## Deployment Architectures

### Architecture A: Single Database Deployment

**Scenario:** Onside and En Garde share the same PostgreSQL database

```
┌─────────────────────────────────────┐
│     PostgreSQL Database             │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │ Onside       │  │ En Garde    │ │
│  │ Schema       │  │ Schema      │ │
│  │              │  │             │ │
│  │ - discovered │  │ - keywords  │ │
│  │   _keywords  │  │ - competitors│ │
│  │ - identified │  │ - content   │ │
│  │   _competitors│  │   _ideas   │ │
│  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────┘
```

**Configuration:**
```python
# Use direct database connection
import_service = ImportService(
    onside_db=db_session,  # Same session, different schema
    engarde_db=db_session,  # Same session
    use_api_import=False
)
```

**Pros:** Fast, transactional, simple
**Cons:** Tight coupling between systems

---

### Architecture B: Separate Database Deployment

**Scenario:** Onside and En Garde have separate databases

```
┌──────────────────┐       ┌─────────────────┐
│ Onside Database  │       │ EnGarde Database│
│                  │       │                 │
│ - discovered_    │       │ - keywords      │
│   keywords       │       │ - competitors   │
│ - identified_    │       │ - content_ideas │
│   competitors    │       │                 │
└──────────────────┘       └─────────────────┘
         │                          │
         └──────────┬───────────────┘
                    │
            ┌───────▼────────┐
            │ Import Service │
            │ (2 DB Sessions)│
            └────────────────┘
```

**Configuration:**
```python
# Configure two separate database sessions
onside_engine = create_engine(ONSIDE_DATABASE_URL)
engarde_engine = create_engine(ENGARDE_DATABASE_URL)

OnSideSession = sessionmaker(bind=onside_engine)
EnGardeSession = sessionmaker(bind=engarde_engine)

onside_db = OnSideSession()
engarde_db = EnGardeSession()

import_service = ImportService(
    onside_db=onside_db,
    engarde_db=engarde_db,
    use_api_import=False
)
```

**Pros:** Clean separation, independent scaling
**Cons:** No distributed transactions, more complex

---

### Architecture C: Microservices with API

**Scenario:** En Garde is a separate service with REST API

```
┌──────────────────┐       ┌─────────────────────┐
│ Onside Service   │       │ EnGarde Service     │
│                  │       │                     │
│ - Onside DB      │       │ - EnGarde DB        │
│ - Import Service │◄─────►│ - REST API          │
│                  │ HTTP  │ - Business Logic    │
└──────────────────┘       └─────────────────────┘
```

**Configuration:**
```python
import httpx

# Configure HTTP client for En Garde API
engarde_client = httpx.Client(
    base_url="https://engarde-api.example.com",
    headers={
        "Authorization": f"Bearer {ENGARDE_API_TOKEN}",
        "Content-Type": "application/json"
    },
    timeout=30.0
)

import_service = ImportService(
    onside_db=onside_db,
    use_api_import=True,
    engarde_api_client=engarde_client
)
```

**Pros:** Best separation, independent deployment, scalability
**Cons:** Network latency, API versioning complexity

---

## Database Migrations

### Step 1: Create En Garde Tables (If Not Exist)

If the En Garde production database doesn't have these tables yet, run these migrations:

#### Migration 001: Create Keywords Table

```sql
-- File: migrations/engarde/001_create_keywords_table.sql

CREATE TABLE IF NOT EXISTS keywords (
    id SERIAL PRIMARY KEY,
    tenant_uuid UUID NOT NULL,
    keyword_text VARCHAR(500) NOT NULL,
    search_volume INTEGER,
    competition_score FLOAT CHECK (competition_score >= 0 AND competition_score <= 100),
    cpc_estimate DECIMAL(10,2) CHECK (cpc_estimate >= 0),
    current_position INTEGER CHECK (current_position >= 0),
    target_position INTEGER CHECK (target_position >= 1 AND target_position <= 10),
    priority_level VARCHAR(20) CHECK (priority_level IN ('high', 'medium', 'low')),
    category VARCHAR(100),
    intent_type VARCHAR(50) CHECK (intent_type IN ('informational', 'navigational', 'transactional', 'commercial')),
    metadata JSONB DEFAULT '{}',
    source VARCHAR(100) DEFAULT 'manual',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Unique constraint: one keyword per tenant
    CONSTRAINT unique_keyword_per_tenant UNIQUE(tenant_uuid, keyword_text)
);

-- Indexes for performance
CREATE INDEX idx_keywords_tenant ON keywords(tenant_uuid);
CREATE INDEX idx_keywords_text_gin ON keywords USING gin(to_tsvector('english', keyword_text));
CREATE INDEX idx_keywords_priority ON keywords(priority_level);
CREATE INDEX idx_keywords_source ON keywords(source);
CREATE INDEX idx_keywords_created ON keywords(created_at DESC);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_keywords_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER keywords_updated_at_trigger
    BEFORE UPDATE ON keywords
    FOR EACH ROW
    EXECUTE FUNCTION update_keywords_updated_at();

-- Comments for documentation
COMMENT ON TABLE keywords IS 'Keyword tracking for SEO campaigns';
COMMENT ON COLUMN keywords.tenant_uuid IS 'Multi-tenant isolation';
COMMENT ON COLUMN keywords.keyword_text IS 'The actual keyword phrase';
COMMENT ON COLUMN keywords.search_volume IS 'Estimated monthly search volume';
COMMENT ON COLUMN keywords.competition_score IS 'SEO difficulty (0-100)';
COMMENT ON COLUMN keywords.intent_type IS 'Search intent classification';
COMMENT ON COLUMN keywords.source IS 'Origin of keyword (onside_analysis, manual, api, etc.)';
```

#### Migration 002: Create Competitors Table

```sql
-- File: migrations/engarde/002_create_competitors_table.sql

CREATE TABLE IF NOT EXISTS competitors (
    id SERIAL PRIMARY KEY,
    tenant_uuid UUID NOT NULL,
    competitor_name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    competitor_type VARCHAR(50) CHECK (competitor_type IN ('direct', 'indirect', 'aspirational', 'emerging')),
    market_share FLOAT CHECK (market_share >= 0 AND market_share <= 100),
    strength_score FLOAT CHECK (strength_score >= 0 AND strength_score <= 100),
    keyword_overlap_count INTEGER CHECK (keyword_overlap_count >= 0),
    shared_keywords TEXT[] DEFAULT '{}',
    competitive_advantages TEXT[] DEFAULT '{}',
    weaknesses TEXT[] DEFAULT '{}',
    monitoring_enabled BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    source VARCHAR(100) DEFAULT 'manual',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Unique constraint: one competitor domain per tenant
    CONSTRAINT unique_competitor_per_tenant UNIQUE(tenant_uuid, domain)
);

-- Indexes for performance
CREATE INDEX idx_competitors_tenant ON competitors(tenant_uuid);
CREATE INDEX idx_competitors_domain ON competitors(domain);
CREATE INDEX idx_competitors_type ON competitors(competitor_type);
CREATE INDEX idx_competitors_monitoring ON competitors(monitoring_enabled) WHERE monitoring_enabled = TRUE;
CREATE INDEX idx_competitors_source ON competitors(source);
CREATE INDEX idx_competitors_created ON competitors(created_at DESC);

-- Trigger for updated_at
CREATE TRIGGER competitors_updated_at_trigger
    BEFORE UPDATE ON competitors
    FOR EACH ROW
    EXECUTE FUNCTION update_keywords_updated_at();

-- Comments for documentation
COMMENT ON TABLE competitors IS 'Competitor tracking for competitive analysis';
COMMENT ON COLUMN competitors.tenant_uuid IS 'Multi-tenant isolation';
COMMENT ON COLUMN competitors.domain IS 'Primary competitor domain';
COMMENT ON COLUMN competitors.competitor_type IS 'Classification of competitor relationship';
COMMENT ON COLUMN competitors.strength_score IS 'Overall competitive strength (0-100)';
COMMENT ON COLUMN competitors.monitoring_enabled IS 'Whether to actively monitor this competitor';
COMMENT ON COLUMN competitors.source IS 'Origin of competitor (onside_analysis, manual, api, etc.)';
```

#### Migration 003: Create Content Ideas Table

```sql
-- File: migrations/engarde/003_create_content_ideas_table.sql

CREATE TABLE IF NOT EXISTS content_ideas (
    id SERIAL PRIMARY KEY,
    tenant_uuid UUID NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    content_type VARCHAR(100) CHECK (content_type IN ('blog_post', 'guide', 'video', 'infographic', 'case_study', 'whitepaper')),
    priority VARCHAR(20) CHECK (priority IN ('high', 'medium', 'low')),
    estimated_traffic INTEGER CHECK (estimated_traffic >= 0),
    difficulty_score FLOAT CHECK (difficulty_score >= 0 AND difficulty_score <= 100),
    target_keywords TEXT[] DEFAULT '{}',
    target_audience VARCHAR(255),
    content_gap VARCHAR(100) CHECK (content_gap IN ('missing_content', 'weak_content', 'competitor_strength')),
    competitor_coverage BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) CHECK (status IN ('idea', 'planned', 'in_progress', 'published', 'archived')) DEFAULT 'idea',
    metadata JSONB DEFAULT '{}',
    source VARCHAR(100) DEFAULT 'manual',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_content_ideas_tenant ON content_ideas(tenant_uuid);
CREATE INDEX idx_content_ideas_status ON content_ideas(status);
CREATE INDEX idx_content_ideas_priority ON content_ideas(priority);
CREATE INDEX idx_content_ideas_type ON content_ideas(content_type);
CREATE INDEX idx_content_ideas_source ON content_ideas(source);
CREATE INDEX idx_content_ideas_created ON content_ideas(created_at DESC);

-- Trigger for updated_at
CREATE TRIGGER content_ideas_updated_at_trigger
    BEFORE UPDATE ON content_ideas
    FOR EACH ROW
    EXECUTE FUNCTION update_keywords_updated_at();

-- Comments for documentation
COMMENT ON TABLE content_ideas IS 'Content opportunity tracking';
COMMENT ON COLUMN content_ideas.tenant_uuid IS 'Multi-tenant isolation';
COMMENT ON COLUMN content_ideas.title IS 'Content idea title/topic';
COMMENT ON COLUMN content_ideas.content_gap IS 'Type of content gap identified';
COMMENT ON COLUMN content_ideas.status IS 'Current status in content pipeline';
COMMENT ON COLUMN content_ideas.source IS 'Origin of idea (onside_analysis, manual, api, etc.)';
```

#### Migration 004: Create Import Batches Table (Optional)

```sql
-- File: migrations/engarde/004_create_import_batches_table.sql

CREATE TABLE IF NOT EXISTS import_batches (
    batch_id UUID PRIMARY KEY,
    job_id UUID NOT NULL,
    tenant_uuid UUID,
    user_id INTEGER NOT NULL,
    status VARCHAR(50) CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'rolled_back')) NOT NULL,
    keywords_imported INTEGER DEFAULT 0,
    competitors_imported INTEGER DEFAULT 0,
    opportunities_imported INTEGER DEFAULT 0,
    duplicates_detected INTEGER DEFAULT 0,
    duplicates_skipped INTEGER DEFAULT 0,
    errors TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_import_batches_job ON import_batches(job_id);
CREATE INDEX idx_import_batches_tenant ON import_batches(tenant_uuid);
CREATE INDEX idx_import_batches_user ON import_batches(user_id);
CREATE INDEX idx_import_batches_status ON import_batches(status);
CREATE INDEX idx_import_batches_created ON import_batches(created_at DESC);

-- Comments
COMMENT ON TABLE import_batches IS 'Audit trail for import operations';
COMMENT ON COLUMN import_batches.batch_id IS 'Unique identifier for import batch';
COMMENT ON COLUMN import_batches.job_id IS 'Onside brand analysis job ID';
COMMENT ON COLUMN import_batches.status IS 'Current status of import batch';
```

---

### Step 2: Configure Database Connection

#### For Single Database (Architecture A)

```python
# config/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Single database with schemas
DATABASE_URL = "postgresql://user:password@localhost:5432/engarde_app"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### For Separate Databases (Architecture B)

```python
# config/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Onside database
ONSIDE_DATABASE_URL = "postgresql://user:password@localhost:5432/onside"
onside_engine = create_engine(ONSIDE_DATABASE_URL)
OnSideSession = sessionmaker(autocommit=False, autoflush=False, bind=onside_engine)

# En Garde database
ENGARDE_DATABASE_URL = "postgresql://user:password@localhost:5432/engarde"
engarde_engine = create_engine(ENGARDE_DATABASE_URL)
EnGardeSession = sessionmaker(autocommit=False, autoflush=False, bind=engarde_engine)

def get_onside_db():
    db = OnSideSession()
    try:
        yield db
    finally:
        db.close()

def get_engarde_db():
    db = EnGardeSession()
    try:
        yield db
    finally:
        db.close()
```

#### For API-Based (Architecture C)

```python
# config/engarde_client.py

import httpx
from functools import lru_cache

@lru_cache()
def get_engarde_client():
    """Get configured En Garde API client."""
    return httpx.Client(
        base_url=ENGARDE_API_URL,
        headers={
            "Authorization": f"Bearer {ENGARDE_API_TOKEN}",
            "Content-Type": "application/json"
        },
        timeout=httpx.Timeout(30.0, read=60.0)
    )
```

---

### Step 3: Update Import Service Initialization

#### Modify engarde.py endpoint

```python
# src/api/v1/engarde.py

from src.services.engarde_integration.import_service import ImportService
from src.config.database import get_engarde_db  # Add this

@router.post("/brand-analysis/{job_id}/confirm")
def confirm_brand_analysis(
    job_id: str,
    confirmation: BrandAnalysisConfirmRequest,
    onside_db: Session = Depends(get_db),  # Rename for clarity
    engarde_db: Session = Depends(get_engarde_db),  # Add En Garde DB
    current_user: User = Depends(get_current_user)
):
    # Initialize with both databases
    import_service = ImportService(
        onside_db=onside_db,
        engarde_db=engarde_db,
        use_api_import=False  # Now using direct DB
    )

    # Rest of the endpoint logic...
```

---

### Step 4: Create En Garde Database Models (If Direct DB Mode)

If using direct database access, create SQLAlchemy models:

```python
# File: src/models/engarde.py (NEW FILE)

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, DECIMAL
from sqlalchemy.sql import func
from src.database import Base

class EnGardeKeyword(Base):
    """En Garde keyword model."""
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(UUID(as_uuid=True), nullable=False)
    keyword_text = Column(String(500), nullable=False)
    search_volume = Column(Integer)
    competition_score = Column(Float)
    cpc_estimate = Column(DECIMAL(10, 2))
    current_position = Column(Integer)
    target_position = Column(Integer)
    priority_level = Column(String(20))
    category = Column(String(100))
    intent_type = Column(String(50))
    metadata = Column(JSONB, default={})
    source = Column(String(100), default="manual")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class EnGardeCompetitor(Base):
    """En Garde competitor model."""
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(UUID(as_uuid=True), nullable=False)
    competitor_name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False)
    competitor_type = Column(String(50))
    market_share = Column(Float)
    strength_score = Column(Float)
    keyword_overlap_count = Column(Integer)
    shared_keywords = Column(ARRAY(Text), default=[])
    competitive_advantages = Column(ARRAY(Text), default=[])
    weaknesses = Column(ARRAY(Text), default=[])
    monitoring_enabled = Column(Boolean, default=True)
    metadata = Column(JSONB, default={})
    source = Column(String(100), default="manual")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class EnGardeContentIdea(Base):
    """En Garde content idea model."""
    __tablename__ = "content_ideas"

    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    content_type = Column(String(100))
    priority = Column(String(20))
    estimated_traffic = Column(Integer)
    difficulty_score = Column(Float)
    target_keywords = Column(ARRAY(Text), default=[])
    target_audience = Column(String(255))
    content_gap = Column(String(100))
    competitor_coverage = Column(Boolean, default=False)
    status = Column(String(50), default="idea")
    metadata = Column(JSONB, default={})
    source = Column(String(100), default="manual")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
```

---

### Step 5: Update Import Service Implementation

If using direct database mode, update the placeholder import methods:

```python
# src/services/engarde_integration/import_service.py

from src.models.engarde import EnGardeKeyword, EnGardeCompetitor, EnGardeContentIdea

def _import_keyword(self, keyword, tenant_uuid, batch_id, is_duplicate, strategy):
    """Import keyword via direct database insert."""

    engarde_keyword = EnGardeKeyword(
        tenant_uuid=tenant_uuid,
        keyword_text=keyword.keyword_text,
        search_volume=keyword.search_volume,
        competition_score=keyword.competition_score,
        cpc_estimate=keyword.cpc_estimate,
        current_position=keyword.current_position,
        target_position=keyword.target_position,
        priority_level=keyword.priority_level,
        category=keyword.category,
        intent_type=keyword.intent_type,
        metadata={
            **keyword.metadata,
            "import_batch_id": batch_id
        },
        source=keyword.source
    )

    self.engarde_db.add(engarde_keyword)
    self.engarde_db.flush()

# Similar updates for _import_competitor and _import_content_idea
```

---

## Testing the Migration

### Test 1: Verify Table Creation

```sql
-- Check tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('keywords', 'competitors', 'content_ideas', 'import_batches');

-- Check indexes
SELECT indexname
FROM pg_indexes
WHERE tablename IN ('keywords', 'competitors', 'content_ideas');
```

### Test 2: Test Import Service

```python
# Run test import
pytest tests/services/test_import_service.py -v

# Or manual test
from src.services.engarde_integration.import_service import ImportService

service = ImportService(onside_db=db, engarde_db=engarde_db, use_api_import=False)
stats = service.import_confirmed_results(...)

print(f"Imported: {stats.successfully_imported}")
```

### Test 3: Verify Data in En Garde DB

```sql
-- Check imported keywords
SELECT * FROM keywords WHERE source = 'onside_analysis' LIMIT 10;

-- Check imported competitors
SELECT * FROM competitors WHERE source = 'onside_analysis' LIMIT 10;

-- Check import batches audit trail
SELECT * FROM import_batches ORDER BY created_at DESC LIMIT 10;
```

---

## Rollback Procedure

If migration fails or needs to be reversed:

```sql
-- Rollback Migration (in reverse order)
DROP TABLE IF EXISTS import_batches CASCADE;
DROP TABLE IF EXISTS content_ideas CASCADE;
DROP TABLE IF EXISTS competitors CASCADE;
DROP TABLE IF EXISTS keywords CASCADE;
DROP FUNCTION IF EXISTS update_keywords_updated_at CASCADE;
```

---

## Production Deployment Checklist

- [ ] Backup En Garde database before migration
- [ ] Run migrations in staging environment first
- [ ] Test import with sample data
- [ ] Verify indexes created correctly
- [ ] Update environment variables with DB credentials
- [ ] Test rollback procedure
- [ ] Monitor import performance (query times, batch duration)
- [ ] Set up alerts for failed imports
- [ ] Document tenant_uuid mapping for production tenants
- [ ] Train support team on import troubleshooting

---

## Support

For migration issues:
1. Check PostgreSQL logs for constraint violations
2. Verify database user has CREATE TABLE permissions
3. Ensure UUID extension is enabled: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`
4. Check for name conflicts with existing tables
