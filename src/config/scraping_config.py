"""Configuration for enhanced web scraping service.

This module provides configuration settings for the enhanced web scraping
service used in the En Garde ↔ Onside integration.
"""

import os
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class WebScrapingConfig:
    """Configuration for web scraping service."""

    # General scraping settings
    default_timeout: int = int(os.getenv("SCRAPER_DEFAULT_TIMEOUT", "30"))
    max_retries: int = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
    respect_robots_txt: bool = os.getenv("SCRAPER_RESPECT_ROBOTS", "true").lower() == "true"
    throttle_delay: float = float(os.getenv("SCRAPER_THROTTLE_DELAY", "1.0"))

    # JavaScript rendering settings
    use_playwright_default: bool = os.getenv("SCRAPER_USE_PLAYWRIGHT", "false").lower() == "true"
    playwright_timeout: int = int(os.getenv("SCRAPER_PLAYWRIGHT_TIMEOUT", "30000"))
    wait_for_timeout: int = int(os.getenv("SCRAPER_WAIT_FOR_TIMEOUT", "5000"))

    # Batch scraping settings
    max_concurrent: int = int(os.getenv("SCRAPER_MAX_CONCURRENT", "5"))
    batch_delay: float = float(os.getenv("SCRAPER_BATCH_DELAY", "0.5"))

    # Circuit breaker settings
    circuit_breaker_enabled: bool = os.getenv("SCRAPER_CIRCUIT_BREAKER_ENABLED", "true").lower() == "true"
    failure_threshold: int = int(os.getenv("SCRAPER_FAILURE_THRESHOLD", "5"))
    recovery_timeout: int = int(os.getenv("SCRAPER_RECOVERY_TIMEOUT", "60"))
    half_open_max_calls: int = int(os.getenv("SCRAPER_HALF_OPEN_MAX_CALLS", "3"))

    # User agent settings
    rotate_user_agents: bool = os.getenv("SCRAPER_ROTATE_USER_AGENTS", "true").lower() == "true"
    custom_user_agents: List[str] = field(default_factory=lambda: [
        ua.strip() for ua in os.getenv("SCRAPER_CUSTOM_USER_AGENTS", "").split(",") if ua.strip()
    ])

    # Content analysis settings
    enable_nlp: bool = os.getenv("SCRAPER_ENABLE_NLP", "true").lower() == "true"
    min_content_length: int = int(os.getenv("SCRAPER_MIN_CONTENT_LENGTH", "100"))

    # Competitor analysis settings
    max_blog_posts_per_competitor: int = int(os.getenv("SCRAPER_MAX_BLOG_POSTS", "5"))
    max_product_pages_per_competitor: int = int(os.getenv("SCRAPER_MAX_PRODUCT_PAGES", "10"))

    # Backlink discovery settings
    backlink_discovery_enabled: bool = os.getenv("SCRAPER_BACKLINK_DISCOVERY", "true").lower() == "true"
    max_backlinks_per_domain: int = int(os.getenv("SCRAPER_MAX_BACKLINKS", "100"))
    common_crawl_api_url: str = os.getenv(
        "COMMON_CRAWL_API_URL",
        "http://index.commoncrawl.org/CC-MAIN-2024-10-index"
    )

    # Content theme analysis settings
    max_topics_per_page: int = int(os.getenv("SCRAPER_MAX_TOPICS", "10"))
    max_keywords_per_page: int = int(os.getenv("SCRAPER_MAX_KEYWORDS", "20"))

    # Rate limiting
    global_rate_limit: Optional[int] = int(os.getenv("SCRAPER_GLOBAL_RATE_LIMIT", "100")) or None  # requests per minute
    domain_rate_limit: Optional[int] = int(os.getenv("SCRAPER_DOMAIN_RATE_LIMIT", "30")) or None  # requests per minute per domain


# Default configuration instance
DEFAULT_SCRAPING_CONFIG = WebScrapingConfig()


def get_scraping_config() -> WebScrapingConfig:
    """Get the web scraping configuration.

    Returns:
        WebScrapingConfig instance
    """
    return DEFAULT_SCRAPING_CONFIG


# Export configuration options for documentation
SCRAPING_CONFIG_OPTIONS = {
    "SCRAPER_DEFAULT_TIMEOUT": {
        "description": "Default timeout for HTTP requests (seconds)",
        "default": "30",
        "type": "int"
    },
    "SCRAPER_MAX_RETRIES": {
        "description": "Maximum number of retries for failed requests",
        "default": "3",
        "type": "int"
    },
    "SCRAPER_RESPECT_ROBOTS": {
        "description": "Whether to respect robots.txt",
        "default": "true",
        "type": "bool"
    },
    "SCRAPER_THROTTLE_DELAY": {
        "description": "Minimum delay between requests to same domain (seconds)",
        "default": "1.0",
        "type": "float"
    },
    "SCRAPER_USE_PLAYWRIGHT": {
        "description": "Use Playwright for JavaScript rendering by default",
        "default": "false",
        "type": "bool"
    },
    "SCRAPER_PLAYWRIGHT_TIMEOUT": {
        "description": "Playwright page load timeout (milliseconds)",
        "default": "30000",
        "type": "int"
    },
    "SCRAPER_WAIT_FOR_TIMEOUT": {
        "description": "Timeout for waiting for selectors (milliseconds)",
        "default": "5000",
        "type": "int"
    },
    "SCRAPER_MAX_CONCURRENT": {
        "description": "Maximum concurrent requests in batch scraping",
        "default": "5",
        "type": "int"
    },
    "SCRAPER_BATCH_DELAY": {
        "description": "Delay between batches (seconds)",
        "default": "0.5",
        "type": "float"
    },
    "SCRAPER_CIRCUIT_BREAKER_ENABLED": {
        "description": "Enable circuit breaker pattern",
        "default": "true",
        "type": "bool"
    },
    "SCRAPER_FAILURE_THRESHOLD": {
        "description": "Number of failures before circuit opens",
        "default": "5",
        "type": "int"
    },
    "SCRAPER_RECOVERY_TIMEOUT": {
        "description": "Time to wait before retrying after circuit opens (seconds)",
        "default": "60",
        "type": "int"
    },
    "SCRAPER_HALF_OPEN_MAX_CALLS": {
        "description": "Maximum calls allowed in half-open state",
        "default": "3",
        "type": "int"
    },
    "SCRAPER_ROTATE_USER_AGENTS": {
        "description": "Rotate user agents across requests",
        "default": "true",
        "type": "bool"
    },
    "SCRAPER_CUSTOM_USER_AGENTS": {
        "description": "Comma-separated list of custom user agents",
        "default": "",
        "type": "string"
    },
    "SCRAPER_ENABLE_NLP": {
        "description": "Enable NLP-based content analysis",
        "default": "true",
        "type": "bool"
    },
    "SCRAPER_MIN_CONTENT_LENGTH": {
        "description": "Minimum content length for analysis (characters)",
        "default": "100",
        "type": "int"
    },
    "SCRAPER_MAX_BLOG_POSTS": {
        "description": "Maximum blog posts to scrape per competitor",
        "default": "5",
        "type": "int"
    },
    "SCRAPER_MAX_PRODUCT_PAGES": {
        "description": "Maximum product pages to scrape per competitor",
        "default": "10",
        "type": "int"
    },
    "SCRAPER_BACKLINK_DISCOVERY": {
        "description": "Enable backlink discovery",
        "default": "true",
        "type": "bool"
    },
    "SCRAPER_MAX_BACKLINKS": {
        "description": "Maximum backlinks to discover per domain",
        "default": "100",
        "type": "int"
    },
    "COMMON_CRAWL_API_URL": {
        "description": "Common Crawl Index API URL",
        "default": "http://index.commoncrawl.org/CC-MAIN-2024-10-index",
        "type": "string"
    },
    "SCRAPER_MAX_TOPICS": {
        "description": "Maximum topics to extract per page",
        "default": "10",
        "type": "int"
    },
    "SCRAPER_MAX_KEYWORDS": {
        "description": "Maximum keywords to extract per page",
        "default": "20",
        "type": "int"
    },
    "SCRAPER_GLOBAL_RATE_LIMIT": {
        "description": "Global rate limit (requests per minute)",
        "default": "100",
        "type": "int"
    },
    "SCRAPER_DOMAIN_RATE_LIMIT": {
        "description": "Per-domain rate limit (requests per minute)",
        "default": "30",
        "type": "int"
    },
}
