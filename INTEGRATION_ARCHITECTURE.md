# En Garde ↔ Onside Integration Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         EN GARDE FRONTEND                                │
│                     (production-frontend)                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS/WSS
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      SETUP WIZARD COMPONENT                              │
│  ┌─────────────────────┐         ┌──────────────────────┐              │
│  │  Path Selection     │         │   Manual Input       │              │
│  │  - Automated        │────────▶│   - Keywords         │              │
│  │  - Manual           │         │   - Competitors      │              │
│  └─────────────────────┘         └──────────────────────┘              │
│            │                                                             │
│            ▼                                                             │
│  ┌─────────────────────┐                                                │
│  │  Questionnaire      │                                                │
│  │  - Brand Info       │                                                │
│  │  - Industry         │                                                │
│  │  - Target Markets   │                                                │
│  └─────────────────────┘                                                │
│            │                                                             │
│            ▼                                                             │
│  ┌─────────────────────┐                                                │
│  │  Progress Tracker   │◀──── WebSocket (Real-time Updates)            │
│  │  - Current Step     │                                                │
│  │  - % Complete       │                                                │
│  │  - Status Messages  │                                                │
│  └─────────────────────┘                                                │
│            │                                                             │
│            ▼                                                             │
│  ┌─────────────────────┐                                                │
│  │  Results Review     │                                                │
│  │  - Keywords Found   │                                                │
│  │  - Competitors      │                                                │
│  │  - User Refinement  │                                                │
│  └─────────────────────┘                                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ REST API
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    ONSIDE MIDDLEWARE LAYER                               │
│                         (FastAPI)                                        │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │              En Garde Integration Service                         │ │
│  │                                                                   │ │
│  │  /api/v1/engarde/brand-analysis/initiate   (POST)               │ │
│  │  /api/v1/engarde/brand-analysis/{id}/status (GET)               │ │
│  │  /api/v1/engarde/brand-analysis/{id}/results (GET)              │ │
│  │  /api/v1/engarde/brand-analysis/{id}/confirm (POST)             │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                    ┌───────────────┼───────────────┐                    │
│                    ▼               ▼               ▼                    │
│  ┌──────────────────┐  ┌─────────────────┐  ┌───────────────────┐    │
│  │ Brand Analyzer   │  │ Data Transformer│  │ Validation Engine │    │
│  │ - Footprint      │  │ - Onside → EG   │  │ - Quality Checks  │    │
│  │ - Market Pos.    │  │ - Format Conv.  │  │ - Deduplication   │    │
│  └──────────────────┘  └─────────────────┘  └───────────────────┘    │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │            SEO & CONTENT WALKER AGENT                           │  │
│  │                                                                 │  │
│  │  ┌────────────────┐  ┌──────────────┐  ┌───────────────────┐ │  │
│  │  │ Website Crawler│  │ SERP Analyzer│  │ Competitor Finder │ │  │
│  │  └────────────────┘  └──────────────┘  └───────────────────┘ │  │
│  │                                                                 │  │
│  │  ┌────────────────┐  ┌──────────────┐  ┌───────────────────┐ │  │
│  │  │ Keyword Extract│  │ NLP Processor│  │ Content Analyzer  │ │  │
│  │  └────────────────┘  └──────────────┘  └───────────────────┘ │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌──────────────────────┐  ┌─────────────────┐  ┌──────────────────────┐
│  Web Scraping Engine │  │ SERP API Service│  │  Content Database    │
│  - Selenium/Scrapy   │  │ - Google SERP   │  │  - PostgreSQL        │
│  - BeautifulSoup     │  │ - Bing SERP     │  │  - Redis Cache       │
│  - Playwright        │  │ - SEMrush API   │  │  - MinIO Storage     │
└──────────────────────┘  └─────────────────┘  └──────────────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
                    ┌───────────────────────────────┐
                    │    Celery Task Queue          │
                    │  - Async Processing           │
                    │  - Background Jobs            │
                    │  - Scheduled Tasks            │
                    └───────────────────────────────┘
```

---

## Data Flow: Automated Brand Analysis

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           STEP 1: INITIATION                             │
└──────────────────────────────────────────────────────────────────────────┘

User fills questionnaire → POST /brand-analysis/initiate
                            ↓
                      Job ID created (UUID)
                            ↓
                      Job status: "initiated"
                            ↓
                      Return job_id to frontend
                            ↓
                      Background task starts


┌──────────────────────────────────────────────────────────────────────────┐
│                        STEP 2: CRAWLING PHASE                            │
└──────────────────────────────────────────────────────────────────────────┘

SEO Walker Agent receives job → Status: "crawling" (10%)
                    ↓
        Crawl brand website
                    ↓
    Extract: pages, content, metadata
                    ↓
        Store raw data in cache
                    ↓
            Status: "crawling" (30%)


┌──────────────────────────────────────────────────────────────────────────┐
│                       STEP 3: ANALYSIS PHASE                             │
└──────────────────────────────────────────────────────────────────────────┘

Status: "analyzing" (40%)
            ↓
┌───────────────────────────────┐
│ Parallel Processing:          │
│  - Keyword extraction         │──┐
│  - SERP analysis              │  │
│  - Competitor identification  │  │
└───────────────────────────────┘  │
            ↓                       │
    NLP Processing on content      │
            ↓                       │
    Extract keywords via TF-IDF    │
            ↓                       │
    Analyze top 50 keywords        │← Combine
            ↓                       │  Results
    Identify ranking domains       │
            ↓                       │
    Score competitor relevance     │
            ↓                       │
    Categorize competitors        ─┘
            ↓
    Status: "analyzing" (70%)


┌──────────────────────────────────────────────────────────────────────────┐
│                      STEP 4: PROCESSING PHASE                            │
└──────────────────────────────────────────────────────────────────────────┘

Status: "processing" (80%)
            ↓
    Data transformation
    (Onside → En Garde format)
            ↓
    Quality validation
            ↓
    Deduplication
            ↓
    Relevance scoring
            ↓
    Generate insights
            ↓
    Status: "processing" (95%)


┌──────────────────────────────────────────────────────────────────────────┐
│                      STEP 5: COMPLETION                                  │
└──────────────────────────────────────────────────────────────────────────┘

Status: "completed" (100%)
            ↓
    Store results in database
            ↓
    Send WebSocket notification
            ↓
    Frontend fetches results
            ↓
    User reviews & confirms
            ↓
    POST /brand-analysis/{id}/confirm
            ↓
    Import to production tables
```

---

## Component Interaction Matrix

| Component                  | Interacts With                           | Communication Method |
|----------------------------|------------------------------------------|----------------------|
| Setup Wizard (Frontend)    | En Garde Middleware API                  | REST + WebSocket     |
| En Garde Middleware        | SEO Walker Agent                         | Direct Function Call |
| SEO Walker Agent           | Web Scraping Engine                      | Async Task Queue     |
| SEO Walker Agent           | SERP API Service                         | HTTP API Calls       |
| SEO Walker Agent           | NLP Processor                            | Direct Function Call |
| Data Transformer           | Onside Database                          | SQLAlchemy ORM       |
| Data Transformer           | En Garde API                             | REST API             |
| Web Scraping Engine        | Target Websites                          | HTTP/HTTPS           |
| SERP API Service           | Google/Bing/SEMrush                      | API Keys + REST      |
| Background Tasks           | Celery Workers                           | Redis Message Queue  |
| Progress Tracker           | Frontend                                 | WebSocket            |

---

## Database Schema

```sql
-- Analysis Jobs
brand_analysis_jobs
├── id (UUID, PK)
├── user_id (FK → users)
├── questionnaire (JSONB)
├── status (ENUM: initiated, crawling, analyzing, processing, completed, failed)
├── progress (INT 0-100)
├── results (JSONB)
├── error_message (TEXT)
├── created_at
├── updated_at
└── completed_at

-- Discovered Keywords (Staging)
discovered_keywords
├── id (SERIAL, PK)
├── job_id (FK → brand_analysis_jobs)
├── keyword (TEXT)
├── source (VARCHAR: website_content, serp_analysis, nlp_extraction)
├── search_volume (INT)
├── difficulty (FLOAT 0-100)
├── relevance_score (FLOAT 0-1)
├── current_ranking (INT)
├── serp_features (JSONB)
├── confirmed (BOOLEAN)
└── created_at

-- Identified Competitors (Staging)
identified_competitors
├── id (SERIAL, PK)
├── job_id (FK → brand_analysis_jobs)
├── domain (VARCHAR)
├── name (VARCHAR)
├── relevance_score (FLOAT 0-1)
├── category (ENUM: primary, secondary, emerging, niche)
├── overlap_percentage (FLOAT)
├── keyword_overlap (JSONB)
├── content_similarity (FLOAT)
├── confirmed (BOOLEAN)
└── created_at

-- Content Opportunities (Insights)
content_opportunities
├── id (SERIAL, PK)
├── job_id (FK → brand_analysis_jobs)
├── topic (TEXT)
├── gap_type (ENUM: missing_content, weak_content, competitor_strength)
├── traffic_potential (INT)
├── difficulty (FLOAT)
├── priority (ENUM: high, medium, low)
├── recommended_format (VARCHAR: blog, guide, video, infographic)
└── created_at
```

---

## API Endpoint Sequence

### Automated Analysis Flow

```
1. POST /api/v1/engarde/brand-analysis/initiate
   └─► Returns: { job_id, status: "initiated" }

2. WS /ws/brand-analysis/{job_id}
   └─► Continuous updates: { status, progress, current_step }

3. GET /api/v1/engarde/brand-analysis/{job_id}/status
   └─► Returns: { status, progress, messages[] }

4. GET /api/v1/engarde/brand-analysis/{job_id}/results
   └─► Returns: { keywords[], competitors[], insights{} }

5. POST /api/v1/engarde/brand-analysis/{job_id}/confirm
   └─► Body: { selected_keywords[], selected_competitors[], modifications }
   └─► Returns: { imported: true, keywords_count, competitors_count }
```

### Manual Setup Flow

```
1. POST /api/v1/competitors/bulk
   └─► Body: [{ name, domain, ... }]
   └─► Returns: { created: 5, failed: 0 }

2. POST /api/v1/seo-analytics/keywords/bulk
   └─► Body: [{ keyword, target_position, ... }]
   └─► Returns: { created: 25, failed: 0 }
```

---

## Error Handling Strategy

```
┌─────────────────────────────────────────┐
│         Error Occurs                    │
└─────────────────────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Error Type?    │
         └────────────────┘
        /        |         \
       /         |          \
      ▼          ▼           ▼
┌──────────┐ ┌────────┐ ┌───────────┐
│Website   │ │Timeout │ │Insufficient│
│Unreachable│ │Error   │ │Data       │
└──────────┘ └────────┘ └───────────┘
      │          │           │
      ▼          ▼           ▼
┌────────────────────────────────────┐
│     Graceful Degradation           │
│                                    │
│  1. Log error details              │
│  2. Update job status to "failed"  │
│  3. Store partial results (if any) │
│  4. Notify user via WebSocket      │
│  5. Suggest fallback action        │
└────────────────────────────────────┘
      │
      ▼
┌────────────────────────────────────┐
│    Fallback Options:               │
│                                    │
│  - Manual setup wizard             │
│  - Retry with adjusted params      │
│  - Use industry defaults           │
│  - Contact support                 │
└────────────────────────────────────┘
```

---

## Performance Optimization

### Caching Strategy

```
┌─────────────────────────────────────────┐
│           Cache Layers                  │
└─────────────────────────────────────────┘

1. Redis (In-Memory)
   - SERP results (TTL: 24 hours)
   - Keyword search volumes (TTL: 7 days)
   - Website crawl data (TTL: 1 hour)

2. Database Query Cache
   - Competitor profiles (TTL: 1 day)
   - Industry averages (TTL: 7 days)

3. CDN/Static Assets
   - Frontend components
   - Static analysis templates
```

### Parallel Processing

```python
# Example: Parallel keyword analysis
async def analyze_keywords_parallel(keywords: List[str]):
    tasks = [
        analyze_single_keyword(kw)
        for kw in keywords
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

---

## Security Considerations

1. **API Authentication**
   - JWT tokens for En Garde ↔ Onside communication
   - API key rotation every 30 days
   - Rate limiting: 100 requests/minute per user

2. **Data Privacy**
   - Encrypt sensitive questionnaire data
   - GDPR compliance for data storage
   - User consent for web scraping
   - Option to delete analysis data

3. **Scraping Ethics**
   - Respect robots.txt
   - Rate limit requests (1 req/sec per domain)
   - User-agent identification
   - No scraping behind authentication

---

## Monitoring & Observability

### Metrics to Track

```
Business Metrics:
- Analysis completion rate
- Average analysis time
- User satisfaction (confirmed/total)
- Keyword discovery accuracy

Technical Metrics:
- API response times
- WebSocket connection stability
- Scraping success rate
- Error rates by type

Performance Metrics:
- Database query times
- Cache hit rates
- Background job queue length
- Memory usage
```

### Alerts

```
Critical:
- Analysis failure rate > 5%
- API error rate > 2%
- Database connection issues

Warning:
- Analysis time > 15 minutes
- Cache hit rate < 70%
- Queue backlog > 100 jobs
```

---

*Architecture Version: 1.0*
*Last Updated: December 23, 2025*
