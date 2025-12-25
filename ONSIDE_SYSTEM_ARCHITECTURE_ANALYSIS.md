# Onside Platform - System Architecture Analysis

## Executive Summary

The Onside platform is a **microservices-based competitive intelligence and SEO analytics system** that integrates with the broader En Garde AI Agent Marketing Suite ecosystem. The architecture employs "Walker Agents" as intelligent orchestration layers that coordinate between services to automate complex workflows like brand analysis, competitor research, and content optimization.

**Architecture Pattern:** Microservices with Agent-Based Orchestration
**Primary Language:** Python (FastAPI)
**Message Queue:** Celery + Redis
**Database:** PostgreSQL
**Cache Layer:** Redis
**Object Storage:** MinIO
**Frontend:** React (separate repository)

---

## 1. System Architecture Overview

### 1.1 Microservices Ecosystem

The Onside platform is part of a larger microservices constellation:

```
┌─────────────────────────────────────────────────────────────────┐
│                    EN GARDE ECOSYSTEM                            │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ production-  │    │   ONSIDE     │    │   SANKORE    │
│  frontend    │───▶│ (Analytics)  │◀───│ (Paid Ads)   │
│ (Next.js)    │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        │            ┌────────┼────────┐           │
        │            ▼        ▼        ▼           │
        │      ┌─────────┬────────┬─────────┐     │
        │      │ Celery  │ Redis  │ MinIO   │     │
        │      │ Workers │ Cache  │ Storage │     │
        │      └─────────┴────────┴─────────┘     │
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                    ┌──────────────┐
                    │  PostgreSQL  │
                    │   Database   │
                    └──────────────┘
```

### 1.2 Identified Microservices

Based on architecture analysis, the ecosystem consists of:

| Service | Purpose | Technology | Port |
|---------|---------|------------|------|
| **production-frontend** | En Garde main UI | Next.js/React | 3000 |
| **production-backend** | En Garde API gateway | FastAPI | 8000 |
| **Onside** | Competitive intelligence engine | FastAPI | 8000 |
| **Sankore** | Paid ads intelligence | FastAPI | 8000 |
| **onside-api** | Main API service | FastAPI | 8000 |
| **onside-celery-worker** | Background task processor | Celery | N/A |
| **onside-celery-beat** | Task scheduler | Celery Beat | N/A |
| **onside-flower** | Celery monitoring | Flower | 5555 |
| **onside-db** | PostgreSQL database | PostgreSQL 15 | 5432 |
| **onside-redis** | Cache & message broker | Redis 7 | 6379 |
| **onside-minio** | Object storage | MinIO | 9000/9001 |

---

## 2. What Are "Walker Agents"?

### 2.1 Definition

**Walker Agents** are intelligent orchestration components that "walk through" complex multi-step workflows by:
- Coordinating multiple services
- Managing state across async operations
- Broadcasting progress via WebSockets
- Handling error recovery and fallbacks
- Transforming data between service formats

### 2.2 Current Walker Agents

#### SEOContentWalkerAgent
**Location:** `/Users/cope/EnGardeHQ/Onside/src/agents/seo_content_walker.py`

**Purpose:** Automated brand digital footprint analysis

**Capabilities:**
1. Website crawling and content extraction
2. Keyword extraction using TF-IDF and NLP
3. SERP (Search Engine Results Page) analysis
4. Competitor identification from SERP data
5. Content opportunity generation
6. Backlink discovery
7. Market positioning analysis

**Workflow Steps:**
```python
async def analyze_brand(job_id, questionnaire):
    # Step 1: Crawl website (10-30% progress)
    site_data = await crawl_website()

    # Step 2: Extract keywords (40-50% progress)
    keywords = await extract_keywords(site_data)

    # Step 3: Analyze SERP (55-70% progress)
    serp_data = await analyze_serp(keywords)

    # Step 4: Identify competitors (75-85% progress)
    competitors = await identify_competitors(serp_data)

    # Step 5: Generate content opportunities (90% progress)
    opportunities = await generate_content_opportunities()

    # Step 6: Compile and save results (95-100% progress)
    await save_results()
```

**Key Features:**
- **Real-time progress tracking** via WebSocket broadcasts
- **Caching integration** for performance optimization
- **Graceful degradation** with fallback mechanisms
- **Parallel processing** of keyword analysis
- **Database persistence** of intermediate results

### 2.3 Agent Architecture Pattern

```
┌────────────────────────────────────────────────────────┐
│              Walker Agent (Orchestrator)               │
│  ┌──────────────────────────────────────────────────┐ │
│  │  1. Receive questionnaire/job parameters         │ │
│  │  2. Create job record with UUID                  │ │
│  │  3. Execute workflow steps sequentially          │ │
│  │  4. Broadcast progress updates (WebSocket)       │ │
│  │  5. Store intermediate results (cache/DB)        │ │
│  │  6. Transform data for target service            │ │
│  │  7. Handle errors with fallback strategies       │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Web Scraping │  │ SERP Analyzer│  │ NLP Processor│
│   Service    │  │   Service    │  │   Service    │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                ┌─────────────────┐
                │ Cache + Database│
                └─────────────────┘
```

---

## 3. Service Communication Patterns

### 3.1 Communication Methods

The Onside platform uses **multiple communication patterns**:

| Pattern | Used For | Technology | Example |
|---------|----------|------------|---------|
| **REST API** | Synchronous requests | FastAPI | Frontend → Backend API calls |
| **WebSockets** | Real-time updates | FastAPI WebSocket | Progress tracking, live notifications |
| **Message Queue** | Async background tasks | Celery + Redis | Report generation, bulk scraping |
| **Direct Function Calls** | Within-service orchestration | Python async/await | Walker agent → service modules |
| **Database Shared State** | Cross-service data access | PostgreSQL | Job status, results storage |
| **Cache Layer** | Performance optimization | Redis | SERP results, crawl data |

### 3.2 Data Flow Example: Brand Analysis

```
┌──────────────────────────────────────────────────────────────┐
│  User fills questionnaire in Frontend                        │
└──────────────────────────────────────────────────────────────┘
                         │ HTTP POST
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  POST /api/v1/engarde/brand-analysis/initiate                │
│  - Create job record with UUID                               │
│  - Queue background task                                     │
│  - Return job_id to frontend                                 │
└──────────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ WebSocket   │  │ Celery Task │  │ Database    │
│ Connection  │  │ Queue       │  │ Job Record  │
└─────────────┘  └─────────────┘  └─────────────┘
        │                │
        │                ▼
        │      ┌──────────────────┐
        │      │ Celery Worker    │
        │      │ Executes:        │
        │      │ SEOWalkerAgent   │
        │      └──────────────────┘
        │                │
        │                ▼
        │      ┌──────────────────┐
        │      │ Service Calls:   │
        │      │ - Web Scraper    │
        │      │ - SERP Analyzer  │
        │      │ - NLP Processor  │
        │      └──────────────────┘
        │                │
        ◄────────────────┘
        │ Progress broadcasts
        ▼
┌─────────────┐
│ Frontend    │
│ Updates UI  │
└─────────────┘
```

### 3.3 API Gateway vs Direct Service Communication

**Current Architecture:** Hybrid approach

- **Production-frontend** ↔ **Onside API**: Direct REST calls
- **Onside API** ↔ **Sankore**: REST API integration
- **Walker Agents** ↔ **Internal Services**: Direct function calls (in-process)
- **Background Tasks**: Celery message queue

**No traditional API gateway identified** - Each service exposes its own FastAPI application

---

## 4. Architectural Documentation Review

### 4.1 Documentation Found

| Document | Location | Purpose |
|----------|----------|---------|
| `INTEGRATION_ARCHITECTURE.md` | `/Onside/` | En Garde ↔ Onside integration design |
| `FRONTEND_ARCHITECTURE.md` | `/Onside/` | Frontend component structure |
| `EN_GARDE_ONSIDE_INTEGRATION_PLAN.md` | `/Onside/` | Detailed integration roadmap |
| `README.md` (Onside) | `/Onside/` | API components overview |
| `README.md` (Sankore) | `/Sankore/` | Paid ads intelligence service |
| `docker-compose.yml` | `/Onside/` | Service definitions and dependencies |

### 4.2 Architecture Diagrams

The documentation includes **excellent ASCII architecture diagrams** showing:
- System component interactions
- Data flow sequences
- WebSocket progress tracking
- Error handling strategies
- Cache layers
- Database schema

**Quality Assessment:** ✅ Well-documented for a microservices project

---

## 5. Request Flow Analysis

### 5.1 Expected Flow: Automated Brand Analysis

```
1. User Initiates Analysis
   Frontend → POST /api/v1/engarde/brand-analysis/initiate
   ↓
2. API Creates Job
   - Generate UUID
   - Save questionnaire to DB
   - Return job_id
   ↓
3. Background Task Starts
   Celery worker picks up task
   ↓
4. SEOContentWalkerAgent Executes
   Step 1: Crawl website (broadcast progress: 10-30%)
   Step 2: Extract keywords (broadcast progress: 40-50%)
   Step 3: Analyze SERP (broadcast progress: 55-70%)
   Step 4: Identify competitors (broadcast progress: 75-85%)
   Step 5: Generate opportunities (broadcast progress: 90-95%)
   Step 6: Save results (broadcast progress: 100%)
   ↓
5. Results Stored
   - Database: Job results, discovered keywords, competitors
   - Cache: Intermediate data
   ↓
6. User Reviews Results
   GET /api/v1/engarde/brand-analysis/{job_id}/results
   ↓
7. User Confirms
   POST /api/v1/engarde/brand-analysis/{job_id}/confirm
   → Data imported to production tables
```

### 5.2 Actual Behavior vs Expected

Based on code analysis, the architecture is **mostly implemented** with some gaps:

**✅ Implemented:**
- Walker agent base structure (`SEOContentWalkerAgent`)
- WebSocket progress broadcasting
- Database models for job tracking
- Celery task queues
- Cache integration
- Service modules (web scraping, SERP analysis, NLP)

**⚠️ Potential Issues:**
- Walker agents may not be fully integrated with Celery tasks
- Some documentation references features not yet in codebase
- Frontend setup wizard component may not exist yet
- Cross-service authentication not clearly defined

---

## 6. Architectural Issues Identified

### 6.1 Service Coupling

**Issue:** Moderate coupling between services

**Symptoms:**
- Walker agents make direct database calls (not service-to-service APIs)
- Services share same database schema
- No clear service boundaries for some modules

**Impact:** Difficulty scaling individual services independently

**Recommendation:**
```python
# Instead of direct DB access in agents:
job = self.db.query(BrandAnalysisJob).filter(id == job_id).first()

# Use service API:
job_status = await job_service.get_status(job_id)
```

### 6.2 Single Point of Failure Risks

**Identified SPOFs:**

1. **PostgreSQL Database**
   - All services depend on single PostgreSQL instance
   - No read replicas mentioned
   - **Mitigation:** Add read replicas, implement connection pooling

2. **Redis Cache/Broker**
   - Both Celery and cache use same Redis instance
   - Redis failure breaks both caching AND task queue
   - **Mitigation:** Separate Redis instances for cache vs. broker

3. **Celery Workers**
   - Single worker configuration in docker-compose
   - Worker failure stops all background processing
   - **Mitigation:** Scale to multiple workers with load balancing

### 6.3 Agent Configuration Issues

**Problem:** Walker agents are not externally configurable

**Current State:**
```python
class SEOContentWalkerAgent:
    def __init__(self, db: Session, cache: Optional[AsyncCacheService] = None):
        self.max_pages_per_domain = 10  # Hardcoded
        self.max_keywords = 50          # Hardcoded
        self.max_competitors = 15       # Hardcoded
```

**Recommended:**
```python
class SEOContentWalkerAgent:
    def __init__(self, db: Session, cache: Optional[AsyncCacheService] = None, config: AgentConfig = None):
        config = config or AgentConfig.from_env()
        self.max_pages_per_domain = config.MAX_PAGES_PER_DOMAIN
        self.max_keywords = config.MAX_KEYWORDS
        self.max_competitors = config.MAX_COMPETITORS
```

### 6.4 Error Recovery and Circuit Breakers

**Issue:** Limited circuit breaker implementation for external APIs

**Current State:**
- Basic try/catch error handling
- Retry decorators exist (`@retry_with_backoff`)
- No circuit breaker pattern for SERP API calls

**Risk:** SERP API failures can cause cascading failures

**Recommendation:**
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def analyze_serp(self, keywords: List[str]) -> Dict:
    # SERP analysis with circuit breaker protection
    pass
```

### 6.5 Service Discovery

**Issue:** No service discovery mechanism

**Current State:**
- Services communicate via hardcoded URLs
- Docker compose service names used for networking
- Environment variables for service endpoints

**Scaling Limitation:**
- Cannot dynamically add/remove service instances
- Manual configuration required for new deployments

**Recommendation:**
- Consider Consul, etcd, or Kubernetes service discovery
- Or implement lightweight DNS-based discovery

### 6.6 Authentication Between Services

**Issue:** Inter-service authentication not clearly defined

**Found in code:**
- JWT authentication for user-facing APIs
- No clear authentication for Onside ↔ Sankore communication
- No service-to-service API key rotation mentioned

**Security Risk:** Medium - services may trust each other implicitly

**Recommendation:**
```python
# Implement service-to-service auth
class ServiceAuthMiddleware:
    async def __call__(self, request: Request):
        service_token = request.headers.get("X-Service-Token")
        if not self.verify_service_token(service_token):
            raise HTTPException(401, "Invalid service token")
```

---

## 7. Architectural Strengths

### 7.1 Well-Designed Patterns

✅ **Agent-Based Orchestration**
- Walker agents provide clean abstraction for complex workflows
- Separation of concerns between orchestration and execution
- Reusable components (SERP analyzer, web scraper, NLP processor)

✅ **Async/Await Architecture**
- Proper use of Python asyncio throughout
- Non-blocking I/O for web scraping and API calls
- Efficient handling of concurrent operations

✅ **Message Queue for Background Tasks**
- Celery provides robust task execution
- Multiple queues with priorities
- Beat scheduler for periodic tasks
- Flower monitoring dashboard

✅ **Caching Strategy**
- Redis cache with TTL for expensive operations
- Cache keys using MD5 hashing
- Category-based cache organization

✅ **WebSocket Real-Time Updates**
- Progress tracking during long-running operations
- User experience enhancement
- Proper state management

### 7.2 Scalability Considerations

**Current Scalability:**
- Horizontal scaling possible for Celery workers ✅
- Stateless API design allows multiple API instances ✅
- Cache layer reduces database load ✅

**Scalability Limitations:**
- Single PostgreSQL instance (vertical scaling only) ⚠️
- No database sharding strategy ⚠️
- No API rate limiting across instances ⚠️

---

## 8. Data Consistency and State Management

### 8.1 Database Schema Design

**Job State Management:**
```sql
brand_analysis_jobs
├── id (UUID, PK)
├── status (ENUM: initiated, crawling, analyzing, processing, completed, failed)
├── progress (INT 0-100)
├── results (JSONB)
├── error_message (TEXT)
├── created_at, updated_at, completed_at
```

**Staging Tables:**
- `discovered_keywords` - before user confirmation
- `identified_competitors` - before user confirmation
- `content_opportunities` - insights from analysis

**Pattern:** Two-phase commit
1. Walker agent saves to staging tables
2. User confirms → data copied to production tables

**Strength:** Allows user review before committing changes

### 8.2 State Synchronization

**Challenge:** Keeping WebSocket clients in sync with backend state

**Current Approach:**
```python
# Agent broadcasts progress
await broadcast_progress(job_id, "crawling", 30, "Crawling website...")

# Frontend receives via WebSocket
websocket.onmessage = (event) => {
    const progress = JSON.parse(event.data);
    updateUI(progress);
}
```

**Potential Issue:** WebSocket disconnection could lose progress updates

**Recommendation:**
- Implement polling fallback
- Store progress milestones in database
- Frontend can reconcile on reconnection

---

## 9. Performance Optimization Opportunities

### 9.1 Current Optimizations

✅ **Implemented:**
- Redis caching for SERP results (24h TTL)
- Redis caching for website crawls (1h TTL)
- Parallel keyword analysis using `asyncio.gather`
- Database query result caching
- Connection pooling (SQLAlchemy)

### 9.2 Recommended Optimizations

**1. Batch Processing**
```python
# Instead of:
for keyword in keywords:
    result = await analyze_keyword(keyword)

# Use batch processing:
results = await batch_analyze_keywords(keywords, batch_size=10)
```

**2. Database Query Optimization**
- Add indexes on frequently queried fields:
  - `brand_analysis_jobs.status`
  - `brand_analysis_jobs.user_id`
  - `discovered_keywords.job_id`
  - `identified_competitors.job_id`

**3. Lazy Loading for Large Results**
```python
# Instead of loading all keywords:
GET /results → {keywords: [...100 items]}

# Use pagination:
GET /results?page=1&limit=20
```

**4. CDN for Static Assets**
- Offload frontend static files to CDN
- Reduce API server load

---

## 10. Deployment Architecture

### 10.1 Current Deployment (Docker Compose)

**Services Defined:**
```yaml
services:
  onside-api          # Main FastAPI application
  onside-db           # PostgreSQL 15
  onside-redis        # Redis 7 (cache + broker)
  onside-minio        # MinIO object storage
  onside-celery-worker # Background task processor
  onside-celery-beat  # Task scheduler
  onside-flower       # Celery monitoring UI
```

**Networking:**
- All services on `onside-network` bridge network
- Inter-service communication via service names
- Health checks defined for critical services

**Volumes:**
- `postgres-data` - persistent database storage
- `redis-data` - persistent cache/queue data
- `minio-data` - persistent object storage

### 10.2 Production Deployment Considerations

**Recommended Changes for Production:**

1. **Database:**
   - Managed PostgreSQL (AWS RDS, Google Cloud SQL)
   - Read replicas for scaling
   - Automated backups

2. **Redis:**
   - Separate instances for cache vs. message broker
   - Redis Sentinel for high availability
   - Or managed Redis (AWS ElastiCache)

3. **Object Storage:**
   - Replace MinIO with AWS S3, Google Cloud Storage
   - Or keep MinIO with replication

4. **Monitoring:**
   - Add Prometheus + Grafana
   - Centralized logging (ELK stack or CloudWatch)
   - APM tools (DataDog, New Relic)

5. **Security:**
   - TLS/SSL for all inter-service communication
   - Secrets management (Vault, AWS Secrets Manager)
   - Network policies and firewalls

---

## 11. Recommended Architectural Fixes

### Priority 1: Critical

1. **Implement Circuit Breakers for External APIs**
   ```python
   # Protect SERP API calls from cascading failures
   @circuit(failure_threshold=5, recovery_timeout=60)
   async def get_serp_results(keyword: str):
       # SERP API call
   ```

2. **Add Service-to-Service Authentication**
   ```python
   # JWT tokens for inter-service communication
   SERVICE_API_KEY = settings.ONSIDE_SERVICE_KEY
   headers = {"X-Service-Token": SERVICE_API_KEY}
   ```

3. **Separate Redis Instances**
   ```yaml
   onside-redis-cache:    # For caching only
   onside-redis-broker:   # For Celery only
   ```

### Priority 2: Important

4. **Implement Database Read Replicas**
   - Separate read queries from write queries
   - Reduce load on primary database

5. **Add API Rate Limiting**
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)

   @app.get("/api/v1/analysis")
   @limiter.limit("10/minute")
   async def get_analysis():
       pass
   ```

6. **Externalize Agent Configuration**
   ```python
   # .env file
   WALKER_AGENT_MAX_PAGES=10
   WALKER_AGENT_MAX_KEYWORDS=50

   # Agent initialization
   config = AgentConfig.from_env()
   agent = SEOContentWalkerAgent(db, cache, config)
   ```

### Priority 3: Enhancement

7. **Implement Health Check Endpoints**
   ```python
   @app.get("/health/live")
   def liveness_probe():
       return {"status": "alive"}

   @app.get("/health/ready")
   async def readiness_probe():
       # Check database connection
       # Check Redis connection
       # Check external API availability
       return {"status": "ready"}
   ```

8. **Add Request Tracing**
   ```python
   # OpenTelemetry for distributed tracing
   from opentelemetry import trace

   tracer = trace.get_tracer(__name__)

   @app.post("/analysis")
   async def start_analysis():
       with tracer.start_as_current_span("start_analysis"):
           # Trace the entire request flow
   ```

9. **Implement Graceful Shutdown**
   ```python
   @asynccontextmanager
   async def lifespan(app: FastAPI):
       # Startup
       yield
       # Shutdown - close connections gracefully
       await cache.close()
       await db.close()
   ```

---

## 12. Summary: What's Broken and Why

### 12.1 Not Broken, But Can Be Improved

The Onside architecture is **fundamentally sound** with good design patterns:
- Walker agents provide clean orchestration
- Microservices separation is logical
- Async architecture is well-implemented
- Documentation is comprehensive

### 12.2 Key Issues

| Issue | Severity | Impact |
|-------|----------|--------|
| No circuit breakers for external APIs | High | Cascading failures possible |
| Single Redis for cache + broker | Medium | Single point of failure |
| Hardcoded agent configuration | Medium | Difficult to tune in production |
| No service-to-service auth | Medium | Security risk |
| Single PostgreSQL instance | Medium | Scalability limitation |
| No API rate limiting | Low | Resource exhaustion possible |

### 12.3 Expected vs Actual

**Expected (from documentation):**
- Full setup wizard in frontend ❌ (not found in codebase)
- En Garde ↔ Onside integration endpoints ✅ (implemented)
- Walker agent ✅ (implemented)
- WebSocket progress tracking ✅ (implemented)
- Background task processing ✅ (implemented)

**Gap:** Frontend setup wizard appears to be documented but not implemented yet

---

## 13. Conclusion

The Onside platform demonstrates **solid microservices architecture** with innovative use of "Walker Agents" for orchestrating complex workflows. The agent-based pattern is a strength that provides:

- Clean separation of orchestration logic from service logic
- Reusable components across different workflows
- Easy monitoring and debugging via progress broadcasts
- Flexible error handling and fallback strategies

**Primary architectural recommendation:** Focus on **resilience and scalability** by implementing circuit breakers, separating cache from message broker, and adding service-to-service authentication.

The architecture is **production-ready with minor improvements** needed for high-scale deployments.

---

## File Locations Reference

**Core Architecture Files:**
- Main app: `/Users/cope/EnGardeHQ/Onside/src/main.py`
- Walker agent: `/Users/cope/EnGardeHQ/Onside/src/agents/seo_content_walker.py`
- Celery config: `/Users/cope/EnGardeHQ/Onside/src/celery_app.py`
- Docker compose: `/Users/cope/EnGardeHQ/Onside/docker-compose.yml`
- API routes: `/Users/cope/EnGardeHQ/Onside/src/api/v1/`
- Services: `/Users/cope/EnGardeHQ/Onside/src/services/`

**Documentation:**
- Integration plan: `/Users/cope/EnGardeHQ/Onside/EN_GARDE_ONSIDE_INTEGRATION_PLAN.md`
- Architecture docs: `/Users/cope/EnGardeHQ/Onside/INTEGRATION_ARCHITECTURE.md`
- Frontend arch: `/Users/cope/EnGardeHQ/Onside/FRONTEND_ARCHITECTURE.md`

---

*Analysis Date: December 24, 2024*
*Analyst: Claude (System Architect)*
*Version: 1.0*
