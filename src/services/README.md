# OnSide Services

This directory contains the core services that power the OnSide platform.

## Sprint 3 Services

The following services were added in Sprint 3:

### Web Scraper Service

The `web_scraper` service is responsible for:
- Scraping content from discovered links
- Processing domain scrapes
- Creating snapshots of web content for analysis
- Extracting metadata from HTML content
- Taking screenshots of web pages

**API Endpoints**: `/api/v1/web-scraper/*`

### Link Search Service

The `link_search` service is responsible for:
- Searching for links associated with domains and companies
- Handling keyword searches
- Managing link creation and metadata
- Providing structured link data with metadata

**API Endpoints**: `/api/v1/link-search/*`

### Engagement Extraction Service

The `engagement_extraction` service is responsible for:
- Extracting engagement metrics from scraped content
- Analyzing content for social signals and engagement indicators
- Calculating engagement scores based on multiple factors
- Providing engagement summaries for domains and companies

**API Endpoints**: `/api/v1/engagement-extraction/*`

## Testing

Each service has corresponding unit tests in the `tests/unit/` directory:
- `tests/unit/test_web_scraper/`
- `tests/unit/test_link_search/`
- `tests/unit/test_engagement_extraction/`

Integration tests for the Sprint 3 workflow are available in `tests/integration/test_sprint3_workflow.py`.

## Usage

These services are designed to be used through their API endpoints, but can also be imported and used directly in Python code:

```python
from src.services.web_scraper.web_scraper import WebScraperService
from src.services.link_search.link_search import LinkSearchService
from src.services.engagement_extraction.engagement_extraction import EngagementExtractionService

# Example usage with a database session
async def example_workflow(session):
    # Search for links
    link_search = LinkSearchService(session)
    links, errors = await link_search.search_links_for_domain(domain_id=1)
    
    # Scrape links
    web_scraper = WebScraperService(session)
    for link in links:
        result = await web_scraper.scrape_link(link.id)
    
    # Extract engagement metrics
    engagement = EngagementExtractionService(session)
    for link in links:
        metrics = await engagement.extract_engagement_metrics(link.id)
```
