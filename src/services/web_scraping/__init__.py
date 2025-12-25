"""Web scraping services for En Garde ↔ Onside integration.

This package provides enhanced web scraping capabilities including:
- JavaScript rendering with Playwright
- Batch scraping with concurrency control
- Comprehensive competitor profile scraping
- Backlink discovery via Common Crawl
- Content analysis with NLP (sentiment, readability, themes)
- Retry logic with exponential backoff
- Rate limiting and robots.txt compliance
- Circuit breaker pattern for reliability
"""

from .enhanced_scraper import (
    EnhancedWebScrapingService,
    ScrapingConfig,
    ScrapedPage,
    CompetitorProfile,
    BacklinkData,
    ContentAnalysis,
    CircuitBreakerError,
    ScrapingError,
)

__all__ = [
    'EnhancedWebScrapingService',
    'ScrapingConfig',
    'ScrapedPage',
    'CompetitorProfile',
    'BacklinkData',
    'ContentAnalysis',
    'CircuitBreakerError',
    'ScrapingError',
]
