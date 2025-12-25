# Quick Start: En Garde ↔ Onside Integration

## 🎯 Overview

This integration enables **automated brand digital analysis** by connecting the En Garde frontend setup wizard to Onside's web scraping and competitive intelligence capabilities.

---

## 📦 Deliverables Created

### ✅ Documentation
1. **EN_GARDE_ONSIDE_INTEGRATION_PLAN.md** - Complete implementation plan
2. **INTEGRATION_ARCHITECTURE.md** - System architecture and data flows
3. **This file** - Quick start guide

### ✅ TODO List
18 structured tasks tracked in the project todo system

---

## 🚀 Recommended Implementation Order

### Sprint 1: Foundation (Week 1-2)

#### Backend Core
1. **Create database schema**
   ```bash
   cd Onside
   alembic revision -m "Add En Garde integration tables"
   # Add tables: brand_analysis_jobs, discovered_keywords, identified_competitors
   alembic upgrade head
   ```

2. **Build middleware API endpoints**
   - File: `src/api/v1/engarde.py`
   - Endpoints: initiate, status, results, confirm
   - Test with Postman/curl

3. **Implement basic SEO Walker Agent**
   - File: `src/agents/seo_content_walker.py`
   - Start with simple website crawling
   - Add keyword extraction (TF-IDF)

#### Frontend Core
4. **Create Setup Wizard components**
   ```bash
   cd production-frontend/src/components
   mkdir SetupWizard
   # Create: index.tsx, PathSelectionStep.tsx, QuestionnaireStep.tsx
   ```

5. **Build questionnaire form**
   - Implement BrandAnalysisQuestionnaire schema
   - Add validation with Zod
   - Create responsive UI

---

### Sprint 2: Automation (Week 3-4)

#### Backend Intelligence
6. **Implement SERP analysis**
   - Integrate with Google SERP API or scraping
   - Extract top 100 results per keyword
   - Identify ranking domains

7. **Build competitor identification**
   - Analyze domain frequency in SERP
   - Calculate relevance scores
   - Categorize competitors (primary/secondary/emerging)

8. **Create data transformation layer**
   - File: `src/services/engarde_integration/data_transformer.py`
   - Transform Onside → En Garde formats
   - Implement validation rules

#### Frontend Progress
9. **Implement WebSocket progress tracking**
   ```typescript
   // useAnalysisProgress.ts
   const ws = new WebSocket(`ws://localhost:8000/ws/brand-analysis/${jobId}`);
   ```

10. **Build progress visualization**
    - Step-by-step progress bar
    - Real-time status messages
    - Estimated time remaining

---

### Sprint 3: Review & Refinement (Week 5-6)

#### Frontend Review UI
11. **Create results review interface**
    - Display discovered keywords
    - Show identified competitors
    - Allow user refinement (select/deselect/add)

12. **Build confirmation flow**
    - Batch import approved items
    - Show success confirmation
    - Navigate to dashboard

#### Backend Processing
13. **Implement batch import**
    - File: `src/services/engarde_integration/middleware.py`
    - Method: `confirm_and_import()`
    - Create competitors and keywords in bulk

14. **Add error handling**
    - Graceful degradation strategies
    - Fallback to manual input
    - User-friendly error messages

---

### Sprint 4: Polish & Testing (Week 7)

15. **Add caching layer**
    - Redis for SERP results (24h TTL)
    - Cache crawled websites (1h TTL)

16. **Implement testing suite**
    - Unit tests for transformations
    - Integration tests for API flow
    - E2E tests for wizard

17. **Performance optimization**
    - Parallel processing for keywords
    - Database query optimization
    - Frontend bundle optimization

18. **Documentation & deployment**
    - API documentation
    - User guide
    - Deploy to staging → production

---

## 🔧 Development Setup

### Prerequisites

```bash
# Backend
Python 3.11+
PostgreSQL 15+
Redis 7+
Docker & Docker Compose

# Frontend
Node.js 18+
npm or yarn
```

### Backend Setup

```bash
cd Onside

# Install dependencies
pip install -r requirements.txt

# Add new dependencies for En Garde integration
pip install beautifulsoup4 scrapy playwright selenium
pip install nltk spacy scikit-learn  # For NLP
pip install websockets  # For real-time updates

# Run migrations
alembic upgrade head

# Start services
docker-compose up -d
```

### Frontend Setup

```bash
cd production-frontend

# Install dependencies
npm install

# Add new dependencies
npm install @tanstack/react-query zustand zod
npm install react-hook-form @hookform/resolvers
npm install lucide-react  # Icons

# Start dev server
npm run dev
```

---

## 📝 Key Code Snippets

### 1. Initiate Brand Analysis (Frontend)

```typescript
// src/hooks/useBrandAnalysis.ts
export const useBrandAnalysis = () => {
  const initiate = async (questionnaire: BrandAnalysisQuestionnaire) => {
    const response = await apiClient.post(
      '/api/v1/engarde/brand-analysis/initiate',
      questionnaire
    );
    return response.data.job_id;
  };

  const getStatus = async (jobId: string) => {
    const response = await apiClient.get(
      `/api/v1/engarde/brand-analysis/${jobId}/status`
    );
    return response.data;
  };

  return { initiate, getStatus };
};
```

### 2. SEO Walker Agent (Backend)

```python
# src/agents/seo_content_walker.py
class SEOContentWalkerAgent:
    async def analyze_brand(self, questionnaire):
        # Step 1: Crawl website
        site_data = await self.crawl_website(questionnaire.primaryWebsite)

        # Step 2: Extract keywords
        keywords = await self.extract_keywords(site_data)

        # Step 3: Analyze SERP
        serp_data = await self.analyze_serp(keywords[:20])

        # Step 4: Identify competitors
        competitors = await self.identify_competitors(serp_data)

        return {
            "keywords": keywords,
            "competitors": competitors,
            "insights": self.generate_insights(site_data, serp_data)
        }
```

### 3. Middleware API (Backend)

```python
# src/api/v1/engarde.py
@router.post("/brand-analysis/initiate")
async def initiate_analysis(
    questionnaire: BrandAnalysisQuestionnaire,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Create job
    job = BrandAnalysisJob(
        user_id=current_user.id,
        questionnaire=questionnaire.dict(),
        status="initiated"
    )
    db.add(job)
    db.commit()

    # Start background processing
    background_tasks.add_task(
        process_brand_analysis,
        job.id,
        questionnaire
    )

    return {
        "job_id": str(job.id),
        "status": "initiated"
    }
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/test_keyword_extraction.py
def test_extract_keywords_from_content():
    content = "Sample website content about competitive intelligence..."
    keywords = extract_keywords(content)

    assert len(keywords) > 0
    assert "competitive intelligence" in [kw.keyword for kw in keywords]
    assert all(0 <= kw.relevance_score <= 1 for kw in keywords)
```

### Integration Tests

```python
# tests/integration/test_brand_analysis_flow.py
async def test_complete_brand_analysis():
    questionnaire = BrandAnalysisQuestionnaire(
        brandName="Test Corp",
        primaryWebsite="https://testcorp.com",
        industry="SaaS"
    )

    # Initiate
    job_id = await middleware.start_brand_analysis(questionnaire)
    assert job_id is not None

    # Process
    await middleware.process_brand_analysis(job_id, questionnaire)

    # Verify results
    results = await middleware.get_analysis_results(job_id)
    assert len(results.keywords) > 0
    assert len(results.competitors) > 0
```

### E2E Tests

```typescript
// e2e/setup-wizard.spec.ts
describe('Setup Wizard - Automated Analysis', () => {
  it('completes automated brand analysis', async () => {
    // Navigate to wizard
    await page.goto('/setup-wizard');

    // Select automated path
    await page.click('[data-testid="automated-path"]');

    // Fill questionnaire
    await page.fill('[name="brandName"]', 'Test Corp');
    await page.fill('[name="primaryWebsite"]', 'https://testcorp.com');
    await page.selectOption('[name="industry"]', 'SaaS');

    // Submit
    await page.click('[data-testid="submit-questionnaire"]');

    // Wait for completion
    await page.waitForSelector('[data-testid="results-ready"]');

    // Verify results shown
    expect(await page.locator('[data-testid="keywords-found"]').count()).toBeGreaterThan(0);
  });
});
```

---

## 📊 Success Criteria

### Functional Requirements
- ✅ User can choose between automated and manual setup
- ✅ Automated analysis completes in < 10 minutes
- ✅ At least 80% keyword discovery accuracy
- ✅ At least 3 relevant competitors identified
- ✅ User can review and modify results before confirmation
- ✅ Batch import works for 100+ keywords/competitors

### Non-Functional Requirements
- ✅ API response time < 200ms
- ✅ WebSocket updates every 2-5 seconds
- ✅ Mobile-responsive wizard UI
- ✅ Graceful error handling with fallbacks
- ✅ GDPR compliant data handling

---

## 🐛 Common Issues & Solutions

### Issue: Website crawling fails
**Solution:** Implement retry logic with exponential backoff
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def crawl_website(url):
    # Crawling logic
```

### Issue: SERP API rate limits
**Solution:** Implement caching and request throttling
```python
@cached(ttl=86400)  # 24 hours
async def get_serp_results(keyword):
    await asyncio.sleep(1)  # Rate limit
    # API call
```

### Issue: Analysis takes too long
**Solution:** Implement parallel processing
```python
results = await asyncio.gather(
    analyze_keywords(keywords),
    identify_competitors(serp_data),
    analyze_content(site_data)
)
```

---

## 📚 Additional Resources

### Required Reading
1. **Integration Plan** - Full implementation details
2. **Architecture Doc** - System design and data flows
3. **Onside API Docs** - http://localhost:8000/docs

### Helpful Libraries
- **Web Scraping:** BeautifulSoup, Scrapy, Playwright
- **NLP:** spaCy, NLTK, scikit-learn
- **SERP APIs:** SerpAPI, SEMrush API, Ahrefs API
- **Frontend:** React Query, Zustand, React Hook Form

### External APIs to Consider
1. **SERP Data:** SerpAPI, DataForSEO
2. **Keyword Research:** SEMrush, Ahrefs
3. **Domain Analysis:** Moz API, Majestic API
4. **Content Analysis:** OpenAI API for NLP

---

## 🚦 Next Steps

1. **Review Documentation**
   - Read the full integration plan
   - Understand the architecture
   - Familiarize with API contracts

2. **Set Up Development Environment**
   - Clone repositories
   - Install dependencies
   - Run local development servers

3. **Start with Sprint 1**
   - Create database migrations
   - Build basic API endpoints
   - Create wizard components

4. **Daily Standups**
   - Track progress against todo list
   - Identify blockers early
   - Adjust timeline as needed

5. **Weekly Demos**
   - Show progress to stakeholders
   - Gather feedback
   - Iterate on UX/design

---

## 💡 Pro Tips

1. **Start Simple**
   - Build the happy path first
   - Add complexity incrementally
   - Test early and often

2. **Use Mocks**
   - Mock external APIs during development
   - Create sample analysis results
   - Speed up frontend development

3. **Log Everything**
   - Detailed logs for debugging
   - Track user actions in wizard
   - Monitor API performance

4. **User Feedback**
   - Beta test with real users
   - A/B test automated vs manual
   - Iterate based on data

---

## 📞 Support

- **Technical Questions:** Check Integration Plan docs
- **Architecture Questions:** Review Architecture diagram
- **Implementation Help:** Refer to code snippets above
- **Bugs/Issues:** Create GitHub issues with detailed descriptions

---

**Ready to build?** Start with Sprint 1 and follow the implementation order. Good luck! 🚀

---

*Last Updated: December 23, 2025*
*Version: 1.0*
