# En Garde ↔ Onside Integration Plan
## Automated Brand Digital Analysis & Setup Wizard

---

## 🎯 Project Overview

**Goal:** Create middleware that connects the En Garde platform's frontend setup wizard to Onside's web scraping capabilities, enabling automated brand digital footprint analysis and competitive intelligence gathering.

**Two Setup Paths:**
1. **Automated Discovery** - SEO & Content Walker Agent analyzes brand digital footprint
2. **Manual Input** - Traditional user-driven keyword and competitor entry

---

## 📋 Implementation Roadmap

### Phase 1: Setup Wizard UI/UX (Frontend)

#### 1.1 Design Setup Wizard UI with Dual-Path Selection

**Location:** `production-frontend/src/components/SetupWizard/`

**Files to Create:**
```
SetupWizard/
├── index.tsx                    # Main wizard component
├── PathSelectionStep.tsx        # Choose automated vs manual
├── QuestionnaireStep.tsx        # Brand analysis questionnaire
├── AutomatedProgressStep.tsx    # Progress tracking for analysis
├── ResultsReviewStep.tsx        # Review discovered data
├── ManualInputStep.tsx          # Manual keyword/competitor entry
├── ConfirmationStep.tsx         # Final confirmation
└── styles.module.css
```

**Features:**
- Multi-step wizard with progress indicator
- Animated transitions between steps
- Save and resume functionality
- Mobile-responsive design
- Dark mode support

**Key Components:**

```typescript
// PathSelectionStep.tsx
interface SetupPath {
  id: 'automated' | 'manual';
  title: string;
  description: string;
  benefits: string[];
  estimatedTime: string;
}

const setupPaths: SetupPath[] = [
  {
    id: 'automated',
    title: 'Automated Brand Analysis',
    description: 'Let our AI analyze your digital footprint',
    benefits: [
      'Automatic keyword discovery',
      'Competitor identification',
      'Content strategy insights',
      'Market positioning analysis'
    ],
    estimatedTime: '5-10 minutes'
  },
  {
    id: 'manual',
    title: 'Manual Setup',
    description: 'Input your keywords and competitors',
    benefits: [
      'Full control over data',
      'Quick setup for known competitors',
      'Custom keyword selection',
      'Immediate results'
    ],
    estimatedTime: '2-5 minutes'
  }
];
```

---

#### 1.2 Create Questionnaire Schema for Automated Brand Digital Analysis

**Location:** `production-frontend/src/schemas/brandAnalysisQuestionnaire.ts`

**Questionnaire Structure:**

```typescript
interface BrandAnalysisQuestionnaire {
  // Basic Brand Information
  brandName: string;
  primaryWebsite: string;
  industry: string;
  subIndustry?: string;

  // Geographic Focus
  targetMarkets: string[];        // Countries/regions
  primaryLanguage: string;
  additionalLanguages?: string[];

  // Product/Service Information
  primaryOfferings: string[];     // Main products/services
  uniqueValueProposition: string;
  targetAudience: string;

  // Digital Presence
  socialMediaProfiles: {
    platform: string;
    url: string;
  }[];
  existingContent?: {
    blog?: string;
    knowledgeBase?: string;
    youtube?: string;
  };

  // Competitive Landscape (Optional)
  knownCompetitors?: string[];    // URLs or names
  competitorKeywords?: string[];

  // Analysis Preferences
  analysisDepth: 'quick' | 'standard' | 'comprehensive';
  focusAreas: ('seo' | 'content' | 'social' | 'technical')[];

  // Constraints
  excludeDomains?: string[];      // Domains to exclude from analysis
  budgetTier?: 'startup' | 'growth' | 'enterprise';
}
```

**Form Validation:**
- Required fields: brandName, primaryWebsite, industry, targetMarkets
- URL validation for all website inputs
- Industry dropdown with autocomplete
- Multi-select for targetMarkets and focusAreas

---

### Phase 2: Backend Middleware Layer

#### 2.1 Create Middleware Service for En Garde ↔ Onside Communication

**Location:** `Onside/src/services/engarde_integration/`

**Architecture:**

```
src/services/engarde_integration/
├── __init__.py
├── middleware.py              # Main middleware service
├── brand_analyzer.py          # Brand digital footprint analysis
├── keyword_discovery.py       # Automated keyword extraction
├── competitor_finder.py       # Competitor identification
├── data_transformer.py        # Onside → En Garde format conversion
├── scraping_orchestrator.py   # Coordinate scraping tasks
└── validation.py              # Data validation and verification
```

**Middleware API Endpoints:**

```python
# src/api/v1/engarde.py

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from src.services.engarde_integration.middleware import EnGardeMiddleware

router = APIRouter(prefix="/engarde", tags=["En Garde Integration"])

@router.post("/brand-analysis/initiate")
async def initiate_brand_analysis(
    questionnaire: BrandAnalysisQuestionnaire,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Initiate automated brand digital footprint analysis.
    Returns analysis job ID for tracking progress.
    """
    middleware = EnGardeMiddleware(db)
    job_id = await middleware.start_brand_analysis(questionnaire)

    # Add background task for processing
    background_tasks.add_task(
        middleware.process_brand_analysis,
        job_id,
        questionnaire
    )

    return {
        "job_id": job_id,
        "status": "initiated",
        "estimated_completion": "5-10 minutes"
    }

@router.get("/brand-analysis/{job_id}/status")
async def get_analysis_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current status of brand analysis job.
    """
    middleware = EnGardeMiddleware(db)
    return await middleware.get_analysis_status(job_id)

@router.get("/brand-analysis/{job_id}/results")
async def get_analysis_results(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve completed brand analysis results.
    """
    middleware = EnGardeMiddleware(db)
    return await middleware.get_analysis_results(job_id)

@router.post("/brand-analysis/{job_id}/confirm")
async def confirm_analysis_results(
    job_id: str,
    modifications: Optional[Dict] = None,
    db: Session = Depends(get_db)
):
    """
    User confirms analysis results (with optional modifications).
    Creates competitors and keywords in system.
    """
    middleware = EnGardeMiddleware(db)
    return await middleware.confirm_and_import(job_id, modifications)
```

---

#### 2.2 Build SEO & Content Walker Agent Architecture

**Location:** `Onside/src/agents/seo_content_walker.py`

**Agent Responsibilities:**

```python
class SEOContentWalkerAgent:
    """
    Intelligent agent for automated brand digital footprint analysis.

    Capabilities:
    1. Website crawling and content extraction
    2. Keyword extraction from existing content
    3. Backlink analysis
    4. Competitor identification via market positioning
    5. SERP analysis for brand-related queries
    6. Social media presence analysis
    """

    def __init__(self, onside_client):
        self.client = onside_client
        self.scraper = WebScrapingService()
        self.nlp_processor = NLPProcessor()
        self.serp_analyzer = SERPAnalyzer()

    async def analyze_brand(self, questionnaire: BrandAnalysisQuestionnaire):
        """
        Main analysis orchestration method.
        """
        results = {
            "brand_keywords": [],
            "competitors": [],
            "content_themes": [],
            "market_position": {},
            "seo_health": {}
        }

        # Step 1: Crawl brand website
        site_data = await self._crawl_brand_site(questionnaire.primaryWebsite)

        # Step 2: Extract keywords from content
        keywords = await self._extract_keywords(site_data)
        results["brand_keywords"] = keywords

        # Step 3: Analyze SERP for brand keywords
        serp_data = await self._analyze_serp(keywords[:20])  # Top 20 keywords

        # Step 4: Identify competitors from SERP
        competitors = await self._identify_competitors(serp_data, questionnaire)
        results["competitors"] = competitors

        # Step 5: Analyze content themes
        themes = await self._analyze_content_themes(site_data)
        results["content_themes"] = themes

        # Step 6: Determine market position
        position = await self._determine_market_position(
            questionnaire,
            competitors,
            serp_data
        )
        results["market_position"] = position

        # Step 7: SEO health check
        seo_health = await self._check_seo_health(questionnaire.primaryWebsite)
        results["seo_health"] = seo_health

        return results
```

**Key Methods:**

```python
async def _crawl_brand_site(self, url: str) -> Dict:
    """
    Crawl brand website to extract:
    - Page titles and meta descriptions
    - H1-H6 headings
    - Body content
    - Internal linking structure
    - Images and alt text
    """

async def _extract_keywords(self, site_data: Dict) -> List[Keyword]:
    """
    Extract keywords using:
    - TF-IDF analysis
    - Named Entity Recognition (NER)
    - Phrase extraction
    - Topic modeling
    """

async def _analyze_serp(self, keywords: List[str]) -> Dict:
    """
    For each keyword:
    - Get top 100 SERP results
    - Identify ranking domains
    - Extract SERP features
    - Calculate keyword difficulty
    """

async def _identify_competitors(
    self,
    serp_data: Dict,
    questionnaire: BrandAnalysisQuestionnaire
) -> List[Competitor]:
    """
    Identify competitors by:
    - Domain frequency in SERP results
    - Content overlap analysis
    - Same industry classification
    - Exclude known non-competitors
    - Rank by relevance score
    """
```

---

#### 2.3 Implement Onside Web Scraping API Integration Layer

**Location:** `Onside/src/services/web_scraping/`

**Enhanced Scraping Capabilities:**

```python
class EnhancedWebScrapingService:
    """
    Enhanced web scraping service with En Garde integration.
    """

    async def scrape_competitor_profile(self, domain: str) -> CompetitorProfile:
        """
        Comprehensive competitor profile scraping:
        - Homepage content
        - About page
        - Product/service pages
        - Blog posts (latest 20)
        - Team/leadership info
        - Contact information
        """

    async def batch_keyword_serp_analysis(
        self,
        keywords: List[str],
        location: str = "United States"
    ) -> Dict[str, SERPResult]:
        """
        Batch SERP analysis for multiple keywords.
        Returns top 100 results for each keyword.
        """

    async def discover_backlinks(self, domain: str) -> List[Backlink]:
        """
        Discover backlinks to domain using:
        - Common Crawl data
        - Web scraping of referring domains
        - Social media mentions
        """

    async def analyze_content_themes(self, urls: List[str]) -> ContentAnalysis:
        """
        Analyze content themes across multiple URLs:
        - Topic extraction
        - Sentiment analysis
        - Readability metrics
        - Content structure
        """
```

---

### Phase 3: Data Processing & Transformation

#### 3.1 Create Data Transformation Layer (Onside → En Garde Format)

**Location:** `Onside/src/services/engarde_integration/data_transformer.py`

**Transformation Logic:**

```python
class EnGardeDataTransformer:
    """
    Transform Onside data models to En Garde compatible format.
    """

    def transform_keywords(
        self,
        onside_keywords: List[OnsideKeyword]
    ) -> List[EnGardeKeyword]:
        """
        Transform keyword data:

        Onside Format:
        {
            "keyword": "competitive intelligence",
            "search_volume": 5400,
            "difficulty": 45,
            "current_ranking": 8,
            "serp_features": ["featured_snippet"],
            "cpc": 12.50
        }

        En Garde Format:
        {
            "term": "competitive intelligence",
            "monthlySearchVolume": 5400,
            "competitionLevel": "medium",
            "currentPosition": 8,
            "targetPosition": 3,
            "priority": "high",
            "serpFeatures": ["featuredSnippet"],
            "estimatedTraffic": 540,
            "businessValue": "high"
        }
        """

    def transform_competitors(
        self,
        onside_competitors: List[OnsideCompetitor]
    ) -> List[EnGardeCompetitor]:
        """
        Transform competitor data with enrichment:
        - Add market share estimates
        - Calculate competitive threat score
        - Identify strengths and weaknesses
        - Map content strategy
        """

    def transform_content_opportunities(
        self,
        analysis: ContentAnalysis
    ) -> List[ContentOpportunity]:
        """
        Transform content analysis into actionable opportunities:
        - Identify content gaps
        - Suggest topics to cover
        - Recommend content formats
        - Estimate traffic potential
        """
```

---

#### 3.2 Build Brand Digital Footprint Analysis Service

**Location:** `Onside/src/services/engarde_integration/brand_analyzer.py`

```python
class BrandDigitalFootprintAnalyzer:
    """
    Comprehensive brand digital footprint analysis.
    """

    async def analyze_footprint(
        self,
        questionnaire: BrandAnalysisQuestionnaire
    ) -> DigitalFootprint:
        """
        Analyze brand's complete digital presence:

        Returns:
        {
            "website_analysis": {
                "total_pages": 250,
                "indexed_pages": 180,
                "crawl_errors": 5,
                "avg_load_time": 2.3,
                "mobile_friendly": true,
                "https_enabled": true
            },
            "content_inventory": {
                "blog_posts": 45,
                "product_pages": 12,
                "landing_pages": 8,
                "content_freshness": "good",
                "avg_word_count": 850
            },
            "social_presence": {
                "platforms": ["linkedin", "twitter", "facebook"],
                "total_followers": 12500,
                "engagement_rate": 3.2,
                "posting_frequency": "daily"
            },
            "seo_metrics": {
                "domain_authority": 45,
                "page_authority_avg": 38,
                "backlinks_total": 1250,
                "referring_domains": 320,
                "organic_keywords": 450
            },
            "visibility_score": 65.5,
            "digital_maturity": "growing"
        }
        """
```

---

### Phase 4: Progress Tracking & User Experience

#### 4.1 Implement Progress Tracking and Status Updates for Wizard

**WebSocket Integration for Real-Time Updates:**

```typescript
// frontend/src/hooks/useAnalysisProgress.ts

interface AnalysisProgress {
  jobId: string;
  status: 'initiated' | 'crawling' | 'analyzing' | 'processing' | 'completed' | 'failed';
  currentStep: string;
  totalSteps: number;
  completedSteps: number;
  percentage: number;
  estimatedTimeRemaining: number;
  messages: string[];
}

export const useAnalysisProgress = (jobId: string) => {
  const [progress, setProgress] = useState<AnalysisProgress | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket for real-time updates
    const websocket = new WebSocket(
      `ws://localhost:8000/ws/brand-analysis/${jobId}`
    );

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data);
    };

    setWs(websocket);

    return () => websocket.close();
  }, [jobId]);

  return { progress, ws };
};
```

**Progress Messages:**
```
✓ Analyzing brand website...
✓ Extracting keywords from content...
✓ Analyzing search engine results...
✓ Identifying competitors...
✓ Analyzing competitor strategies...
✓ Generating recommendations...
✓ Finalizing results...
```

---

#### 4.2 Create Review and Confirmation UI for Automated Results

**Location:** `production-frontend/src/components/SetupWizard/ResultsReviewStep.tsx`

```typescript
interface AnalysisResults {
  keywords: {
    discovered: Keyword[];
    suggested: Keyword[];
    rejected: Keyword[];
  };
  competitors: {
    primary: Competitor[];
    secondary: Competitor[];
    emerging: Competitor[];
  };
  insights: {
    marketPosition: string;
    strengths: string[];
    opportunities: string[];
    threats: string[];
  };
  contentOpportunities: ContentOpportunity[];
}

const ResultsReviewStep: React.FC = () => {
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [selectedKeywords, setSelectedKeywords] = useState<string[]>([]);
  const [selectedCompetitors, setSelectedCompetitors] = useState<number[]>([]);

  // User can:
  // - Review discovered keywords (select/deselect)
  // - Review identified competitors (select/deselect)
  // - Add additional keywords manually
  // - Add additional competitors manually
  // - Edit keyword priorities
  // - Edit competitor categories

  return (
    <div className="results-review">
      <KeywordsSection
        keywords={results.keywords}
        onSelectionChange={setSelectedKeywords}
      />
      <CompetitorsSection
        competitors={results.competitors}
        onSelectionChange={setSelectedCompetitors}
      />
      <InsightsSection insights={results.insights} />
      <ContentOpportunitiesSection
        opportunities={results.contentOpportunities}
      />
    </div>
  );
};
```

---

### Phase 5: Data Storage & API Contracts

#### 5.1 Database Schema Extensions

**Location:** `Onside/alembic/versions/`

**New Tables:**

```sql
-- Brand Analysis Jobs
CREATE TABLE brand_analysis_jobs (
    id UUID PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    questionnaire JSONB NOT NULL,
    status VARCHAR(50) NOT NULL,
    progress INTEGER DEFAULT 0,
    results JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Discovered Keywords (before confirmation)
CREATE TABLE discovered_keywords (
    id SERIAL PRIMARY KEY,
    job_id UUID REFERENCES brand_analysis_jobs(id),
    keyword TEXT NOT NULL,
    source VARCHAR(100),  -- 'website_content', 'serp_analysis', etc.
    search_volume INTEGER,
    difficulty FLOAT,
    relevance_score FLOAT,
    current_ranking INTEGER,
    confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Identified Competitors (before confirmation)
CREATE TABLE identified_competitors (
    id SERIAL PRIMARY KEY,
    job_id UUID REFERENCES brand_analysis_jobs(id),
    domain VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    relevance_score FLOAT,
    category VARCHAR(50),  -- 'primary', 'secondary', 'emerging'
    overlap_percentage FLOAT,
    confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

#### 5.2 API Contract Documentation

**Location:** `Onside/docs/api/engarde_integration.md`

```markdown
# En Garde Integration API

## Endpoints

### POST /api/v1/engarde/brand-analysis/initiate

**Request:**
```json
{
  "brandName": "Acme Corp",
  "primaryWebsite": "https://acme.com",
  "industry": "SaaS",
  "targetMarkets": ["United States", "Canada"],
  "primaryLanguage": "en",
  "analysisDepth": "standard",
  "focusAreas": ["seo", "content"]
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "initiated",
  "estimated_completion": "5-10 minutes"
}
```

### GET /api/v1/engarde/brand-analysis/{job_id}/status

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "analyzing",
  "progress": 65,
  "current_step": "Identifying competitors",
  "total_steps": 7,
  "completed_steps": 4,
  "estimated_time_remaining": 180
}
```

### GET /api/v1/engarde/brand-analysis/{job_id}/results

**Response:**
```json
{
  "keywords": {
    "discovered": [
      {
        "keyword": "competitive intelligence",
        "searchVolume": 5400,
        "difficulty": 45,
        "currentRanking": 8,
        "source": "website_content",
        "relevanceScore": 0.92
      }
    ],
    "total": 89
  },
  "competitors": {
    "primary": [
      {
        "domain": "competitor1.com",
        "name": "Competitor 1",
        "relevanceScore": 0.95,
        "overlapPercentage": 78.5
      }
    ],
    "total": 12
  },
  "insights": {
    "marketPosition": "mid-market leader",
    "strengths": [
      "Strong content strategy",
      "High domain authority"
    ],
    "opportunities": [
      "Expand keyword coverage in X area",
      "Target competitor weaknesses in Y"
    ]
  }
}
```
```

---

### Phase 6: Error Handling & Validation

#### 6.1 Build Error Handling and Fallback Mechanisms

```python
# src/services/engarde_integration/error_handling.py

class BrandAnalysisError(Exception):
    """Base exception for brand analysis errors."""
    pass

class WebsiteUnreachableError(BrandAnalysisError):
    """Raised when brand website cannot be crawled."""
    pass

class InsufficientDataError(BrandAnalysisError):
    """Raised when insufficient data is found for analysis."""
    pass

class AnalysisTimeoutError(BrandAnalysisError):
    """Raised when analysis exceeds timeout."""
    pass

async def handle_analysis_failure(
    job_id: str,
    error: Exception,
    questionnaire: BrandAnalysisQuestionnaire
):
    """
    Graceful degradation strategy:
    1. If website unreachable → Suggest manual input
    2. If insufficient data → Use industry defaults + manual refinement
    3. If timeout → Return partial results + suggest continuation
    4. If unknown error → Log, notify, offer full manual setup
    """
```

---

### Phase 7: Testing & Deployment

#### 7.1 Create Testing Suite for Wizard Flow and Integrations

**Test Coverage:**

```python
# tests/integration/test_engarde_integration.py

class TestBrandAnalysisFlow:
    """
    Integration tests for complete brand analysis flow.
    """

    async def test_successful_automated_analysis(self):
        """Test complete automated analysis flow."""

    async def test_analysis_with_manual_corrections(self):
        """Test analysis with user modifications."""

    async def test_website_unreachable_fallback(self):
        """Test fallback to manual when website unreachable."""

    async def test_progress_tracking(self):
        """Test real-time progress updates."""

    async def test_data_transformation(self):
        """Test Onside → En Garde data transformation."""

    async def test_concurrent_analyses(self):
        """Test multiple simultaneous brand analyses."""

    async def test_analysis_cancellation(self):
        """Test user cancelling analysis mid-process."""
```

---

## 🎯 Success Metrics

### User Experience Metrics
- **Setup Time Reduction:** 70% faster than manual input (target: 3 min vs 10 min)
- **Data Accuracy:** 85%+ accuracy in keyword and competitor discovery
- **User Satisfaction:** 4.5/5 stars for automated setup experience
- **Completion Rate:** 90%+ of users complete wizard

### Technical Metrics
- **Analysis Speed:** 90% of analyses complete within 10 minutes
- **API Response Time:** < 200ms for status checks
- **Error Rate:** < 2% failure rate for analyses
- **Data Quality:** 80%+ of discovered keywords accepted by users

---

## 🚀 Deployment Strategy

### Phase 1: Internal Testing (Week 1-2)
- Deploy to staging environment
- Internal team testing with 10 test brands
- Gather feedback and iterate

### Phase 2: Beta Release (Week 3-4)
- Invite 50 beta users
- Monitor performance and gather feedback
- Fix critical bugs

### Phase 3: General Availability (Week 5)
- Full production deployment
- Monitoring and optimization
- User onboarding and support

---

## 📚 Additional Resources

### Documentation to Create
1. **User Guide:** "Getting Started with Automated Brand Analysis"
2. **API Documentation:** Complete En Garde integration API docs
3. **Troubleshooting Guide:** Common issues and solutions
4. **Developer Guide:** Extending the SEO & Content Walker Agent

### Training Materials
1. Video tutorial: "Automated vs Manual Setup: Which to Choose?"
2. Interactive demo: Walkthrough of automated analysis
3. FAQ: Addressing common questions

---

## 🔒 Security & Privacy Considerations

1. **Data Privacy:**
   - User consent for web scraping
   - GDPR compliance for data storage
   - Option to delete analysis data

2. **Rate Limiting:**
   - Implement rate limiting for scraping
   - Respect robots.txt
   - Use ethical scraping practices

3. **Authentication:**
   - Secure API authentication between En Garde and Onside
   - JWT tokens with expiration
   - API key rotation

---

## 📝 Next Steps

1. **Review this plan** with stakeholders
2. **Prioritize tasks** based on dependencies
3. **Assign team members** to each component
4. **Set up project tracking** in Jira/Linear
5. **Begin Phase 1** implementation

---

*Document Version: 1.0*
*Last Updated: December 23, 2025*
*Owner: En Garde Development Team*
