# Enhanced Web Scraping Service

## Overview

The Enhanced Web Scraping Service provides comprehensive web scraping capabilities for the En Garde ↔ Onside integration, enabling advanced competitor analysis, content discovery, and digital footprint tracking.

## Features

### 1. JavaScript Rendering with Playwright

Scrape JavaScript-heavy websites with full rendering support:

```python
from src.services.web_scraping import EnhancedWebScrapingService, ScrapingConfig

config = ScrapingConfig(use_playwright=True)
scraper = EnhancedWebScrapingService(config)

# Scrape with JavaScript rendering
page = await scraper.scrape_with_javascript(
    url="https://example.com",
    wait_for_selector=".dynamic-content",
    wait_for_timeout=5000
)

print(f"Title: {page.title}")
print(f"Headings: {page.headings}")
print(f"Links: {len(page.links)}")
```

### 2. Batch Scraping with Concurrency Control

Scrape multiple URLs in parallel with configurable concurrency:

```python
urls = [
    "https://competitor1.com",
    "https://competitor2.com",
    "https://competitor3.com",
]

# Scrape with max 5 concurrent requests
results = await scraper.batch_scrape(
    urls,
    max_concurrent=5,
    use_javascript=False  # Use lightweight scraping
)

for page in results:
    if page.error:
        print(f"Failed: {page.url} - {page.error}")
    else:
        print(f"Success: {page.url} ({page.status_code})")
```

### 3. Comprehensive Competitor Profiling

Scrape complete competitor profiles including homepage, about page, blog posts, and social links:

```python
profile = await scraper.scrape_competitor_profile(
    domain="competitor.com",
    max_blog_posts=5
)

print(f"Homepage: {profile.homepage_data.title}")
print(f"About: {profile.about_page_data.url if profile.about_page_data else 'Not found'}")
print(f"Blog posts: {len(profile.blog_posts)}")
print(f"Social links: {profile.social_links}")
print(f"Contact: {profile.contact_info}")
print(f"Technologies: {profile.technologies}")
```

### 4. Backlink Discovery

Discover backlinks using Common Crawl data:

```python
backlinks = await scraper.discover_backlinks(
    domain="example.com",
    limit=100
)

for backlink in backlinks:
    print(f"From: {backlink.referring_domain}")
    print(f"URL: {backlink.referring_url}")
    print(f"Anchor: {backlink.anchor_text}")
```

**Note:** Current implementation uses placeholder data. In production, integrate with:
- Common Crawl Index API
- Ahrefs API
- Moz Link Explorer API
- SEMrush Backlink API

### 5. Content Analysis with NLP

Analyze content themes, sentiment, and readability:

```python
analyses = await scraper.analyze_content_themes([
    "https://competitor.com",
    "https://competitor.com/blog/post1",
    "https://competitor.com/blog/post2",
])

for analysis in analyses:
    print(f"URL: {analysis.url}")
    print(f"Topics: {analysis.topics[:5]}")
    print(f"Sentiment: {analysis.sentiment_polarity:.2f}")
    print(f"Readability: {analysis.readability_score:.1f}")
    print(f"Word count: {analysis.word_count}")
    print(f"Keyword density: {analysis.keyword_density}")
```

## Configuration

### Environment Variables

Configure scraping behavior via environment variables:

```bash
# General settings
SCRAPER_DEFAULT_TIMEOUT=30          # Request timeout (seconds)
SCRAPER_MAX_RETRIES=3                # Max retry attempts
SCRAPER_RESPECT_ROBOTS=true          # Respect robots.txt
SCRAPER_THROTTLE_DELAY=1.0           # Delay between requests (seconds)

# JavaScript rendering
SCRAPER_USE_PLAYWRIGHT=false         # Enable Playwright by default
SCRAPER_PLAYWRIGHT_TIMEOUT=30000     # Page load timeout (ms)
SCRAPER_WAIT_FOR_TIMEOUT=5000        # Selector wait timeout (ms)

# Batch scraping
SCRAPER_MAX_CONCURRENT=5             # Max concurrent requests
SCRAPER_BATCH_DELAY=0.5              # Delay between batches (seconds)

# Circuit breaker
SCRAPER_CIRCUIT_BREAKER_ENABLED=true # Enable circuit breaker
SCRAPER_FAILURE_THRESHOLD=5          # Failures before circuit opens
SCRAPER_RECOVERY_TIMEOUT=60          # Recovery timeout (seconds)
SCRAPER_HALF_OPEN_MAX_CALLS=3        # Max calls in half-open state

# User agents
SCRAPER_ROTATE_USER_AGENTS=true      # Rotate user agents
SCRAPER_CUSTOM_USER_AGENTS=""        # Comma-separated custom UAs

# Content analysis
SCRAPER_ENABLE_NLP=true              # Enable NLP analysis
SCRAPER_MIN_CONTENT_LENGTH=100       # Min content length (chars)

# Competitor analysis
SCRAPER_MAX_BLOG_POSTS=5             # Max blog posts per competitor
SCRAPER_MAX_PRODUCT_PAGES=10         # Max product pages per competitor

# Backlink discovery
SCRAPER_BACKLINK_DISCOVERY=true      # Enable backlink discovery
SCRAPER_MAX_BACKLINKS=100            # Max backlinks per domain
COMMON_CRAWL_API_URL=http://index.commoncrawl.org/CC-MAIN-2024-10-index

# Rate limiting
SCRAPER_GLOBAL_RATE_LIMIT=100        # Global requests/minute
SCRAPER_DOMAIN_RATE_LIMIT=30         # Per-domain requests/minute
```

### Programmatic Configuration

```python
from src.services.web_scraping import ScrapingConfig

config = ScrapingConfig(
    default_timeout=30,
    max_retries=3,
    respect_robots_txt=True,
    throttle_delay=1.0,
    use_playwright=False,
    max_concurrent=5,
    enable_nlp=True,
    failure_threshold=5,
    recovery_timeout=60,
    rotate_user_agents=True,
    custom_user_agents=[
        "MyBot/1.0 (+https://example.com/bot)",
    ]
)

scraper = EnhancedWebScrapingService(config=config)
```

## Retry Logic

Automatic retry with exponential backoff:

- **Max retries:** Configurable (default: 3)
- **Strategy:** Exponential backoff with jitter
- **Backoff multiplier:** 1 second
- **Min wait:** 2 seconds
- **Max wait:** 10 seconds

Retries are triggered for:
- Network errors
- Timeout errors
- 5xx server errors

## Rate Limiting

### Domain-Level Throttling

Respects configurable delay between requests to same domain:

```python
# Will wait 1 second between requests to same domain
await scraper.scrape_with_javascript("https://example.com/page1")
await scraper.scrape_with_javascript("https://example.com/page2")  # Waits 1s
```

### Robots.txt Compliance

Automatically fetches and respects robots.txt:

```python
# Checks robots.txt before scraping
config = ScrapingConfig(respect_robots_txt=True)
scraper = EnhancedWebScrapingService(config)

# Raises RobotsDisallowedError if disallowed
await scraper.scrape_with_javascript("https://example.com/admin")
```

Robots.txt responses are cached for 24 hours per domain.

### User Agent Rotation

Rotates through multiple user agents to avoid detection:

```python
# Uses random user agent from pool
page = await scraper.scrape_with_javascript("https://example.com")
```

Default user agents include:
- Chrome on Windows
- Chrome on macOS
- Firefox on Windows
- Safari on macOS
- Chrome on Linux

## Circuit Breaker Pattern

Prevents overwhelming failing domains:

### States

1. **CLOSED** (Normal operation)
   - Requests proceed normally
   - Failures are counted
   - Opens after threshold failures

2. **OPEN** (Failing)
   - Requests fail immediately with CircuitBreakerError
   - No requests sent to domain
   - After recovery timeout, transitions to HALF_OPEN

3. **HALF_OPEN** (Testing recovery)
   - Limited requests allowed
   - Success → CLOSED
   - Failure → OPEN

### Configuration

```python
config = ScrapingConfig(
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60,      # Wait 60s before testing
    half_open_max_calls=3,    # Allow 3 test calls
)
```

### Usage

```python
try:
    page = await scraper.scrape_with_javascript("https://failing-site.com")
except CircuitBreakerError as e:
    print(f"Circuit open: {e}")
    # Handle gracefully - domain is having issues
```

## Error Handling

### Exception Hierarchy

```
ScrapingError (base)
├── RobotsDisallowedError
└── CircuitBreakerError
```

### Error Response

Failed scrapes return `ScrapedPage` with error information:

```python
page = await scraper.scrape_with_javascript("https://invalid-url.com")

if page.error:
    print(f"Scraping failed: {page.error}")
    print(f"Response time: {page.response_time_ms}ms")
else:
    print(f"Success: {page.title}")
```

## Integration with SEOContentWalkerAgent

The enhanced scraper is integrated into the SEO Content Walker Agent:

```python
from src.agents.seo_content_walker import SEOContentWalkerAgent

agent = SEOContentWalkerAgent(db=db_session, cache=cache_service)

# Scrape competitor profiles
profiles = await agent.scrape_competitor_profiles(
    competitor_domains=["competitor1.com", "competitor2.com"],
    max_blog_posts=5
)

# Analyze competitor content
content_analyses = await agent.analyze_competitor_content(
    competitor_domains=["competitor1.com", "competitor2.com"]
)

# Discover backlinks
backlinks = await agent.discover_competitor_backlinks(
    competitor_domains=["competitor1.com"],
    limit_per_domain=50
)
```

## Performance Optimizations

### 1. Connection Pooling

Uses aiohttp connection pooling for efficient HTTP requests:

```python
# Reuses connections across requests
connector = aiohttp.TCPConnector(limit_per_host=5)
session = aiohttp.ClientSession(connector=connector)
```

### 2. Batch Processing

Processes multiple URLs concurrently with semaphore-based concurrency control:

```python
# Scrapes 100 URLs with max 10 concurrent
results = await scraper.batch_scrape(urls, max_concurrent=10)
```

### 3. Resource Cleanup

Automatic cleanup with async context manager:

```python
async with EnhancedWebScrapingService(config) as scraper:
    # Scraping operations
    page = await scraper.scrape_with_javascript("https://example.com")
# Resources automatically cleaned up
```

## Limitations and Future Work

### Current Limitations

1. **Backlink Discovery**
   - Currently uses placeholder data
   - Needs integration with actual Common Crawl Index API or commercial APIs

2. **JavaScript Detection**
   - Basic technology detection based on HTML signatures
   - Could be enhanced with more sophisticated fingerprinting

3. **NLP Features**
   - Requires NLTK and TextBlob to be installed
   - Topic extraction is basic (word frequency)
   - Could integrate more advanced NLP models

4. **Rate Limiting**
   - Domain-level throttling is basic
   - Could add more sophisticated rate limiting with token bucket algorithm

### Future Enhancements

1. **Advanced Backlink Analysis**
   - Integrate with Ahrefs API
   - Integrate with Moz Link Explorer
   - Implement custom link graph crawling

2. **Enhanced NLP**
   - Use transformer models for topic modeling
   - Add named entity recognition
   - Implement content classification

3. **Performance**
   - Add distributed scraping with Celery
   - Implement persistent caching with Redis
   - Add scraping job queuing

4. **Monitoring**
   - Add metrics collection (Prometheus)
   - Add distributed tracing (OpenTelemetry)
   - Add alerting for circuit breaker events

5. **JavaScript Rendering**
   - Add screenshot comparison for change detection
   - Support for authenticated scraping
   - Support for form submission and interaction

## Testing

Run comprehensive tests:

```bash
# Run all tests
pytest tests/services/test_enhanced_web_scraper.py -v

# Run specific test class
pytest tests/services/test_enhanced_web_scraper.py::TestBatchScraping -v

# Run with coverage
pytest tests/services/test_enhanced_web_scraper.py --cov=src.services.web_scraping
```

## Dependencies

Required packages (added to `requirements.txt`):

```
# Core
aiohttp>=3.11.11
playwright>=1.40.0
beautifulsoup4==4.13.4
tenacity>=8.2.0

# NLP (optional but recommended)
textblob==0.19.0
nltk==3.9.1
scikit-learn>=1.3.0

# Testing
pytest==8.3.4
pytest-asyncio==0.25.3
pytest-mock==3.14.0
```

Install Playwright browsers:

```bash
playwright install chromium
```

Download NLTK data (for NLP features):

```python
import nltk
nltk.download('punkt')
```

## License

Part of the En Garde ↔ Onside integration platform.

## Support

For issues or questions:
- Check the test suite for usage examples
- Review configuration options in `src/config/scraping_config.py`
- See integration examples in `src/agents/seo_content_walker.py`
