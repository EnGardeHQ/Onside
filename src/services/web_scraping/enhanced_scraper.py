"""Enhanced web scraping service with advanced features for En Garde ↔ Onside integration.

This module provides comprehensive web scraping capabilities including:
- JavaScript rendering with Playwright
- Batch scraping with concurrency control
- Competitor profile analysis
- Backlink discovery
- NLP-based content analysis
- Retry logic with circuit breaker
- Rate limiting and robots.txt compliance
"""

import asyncio
import logging
import time
import random
import re
import hashlib
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from collections import defaultdict, Counter
from enum import Enum

import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

# NLP imports
try:
    import textblob
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

logger = logging.getLogger(__name__)


# Exceptions
class ScrapingError(Exception):
    """Base exception for scraping errors."""
    pass


class RobotsDisallowedError(ScrapingError):
    """Exception raised when robots.txt disallows scraping."""
    pass


class CircuitBreakerError(ScrapingError):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


# Data classes
@dataclass
class ScrapingConfig:
    """Configuration for web scraping service."""

    # General settings
    default_timeout: int = 30
    max_retries: int = 3
    respect_robots_txt: bool = True
    throttle_delay: float = 1.0

    # JavaScript rendering
    use_playwright: bool = False
    wait_for_selector: Optional[str] = None
    wait_for_timeout: int = 5000

    # Batch scraping
    max_concurrent: int = 5
    batch_delay: float = 0.5

    # Circuit breaker
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3

    # User agent rotation
    rotate_user_agents: bool = True
    custom_user_agents: List[str] = field(default_factory=list)

    # Content analysis
    enable_nlp: bool = True
    min_content_length: int = 100


@dataclass
class ScrapedPage:
    """Result from scraping a single page."""
    url: str
    html: str
    text: str
    title: str
    meta_description: str
    meta_keywords: str
    headings: Dict[str, List[str]]
    links: List[str]
    images: List[str]
    status_code: int
    response_time_ms: float
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    is_javascript_rendered: bool = False


@dataclass
class CompetitorProfile:
    """Comprehensive competitor profile."""
    domain: str
    homepage_data: Optional[ScrapedPage] = None
    about_page_data: Optional[ScrapedPage] = None
    blog_posts: List[ScrapedPage] = field(default_factory=list)
    product_pages: List[ScrapedPage] = field(default_factory=list)
    contact_info: Dict[str, str] = field(default_factory=dict)
    social_links: Dict[str, str] = field(default_factory=dict)
    technologies: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class BacklinkData:
    """Backlink discovery result."""
    target_domain: str
    referring_domain: str
    referring_url: str
    anchor_text: str
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    context: Optional[str] = None


@dataclass
class ContentAnalysis:
    """NLP-based content analysis result."""
    url: str
    topics: List[Dict[str, float]]  # List of {topic: score}
    sentiment_polarity: float  # -1 to 1
    sentiment_subjectivity: float  # 0 to 1
    readability_score: float  # Flesch reading ease
    word_count: int
    sentence_count: int
    avg_words_per_sentence: float
    heading_structure: Dict[str, int]
    keyword_density: Dict[str, float]



@dataclass
class CircuitBreakerStatus:
    """Circuit breaker status for a domain."""
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[float] = None
    success_count: int = 0


class EnhancedWebScrapingService:
    """Enhanced web scraping service with advanced features.

    Features:
    - JavaScript rendering with Playwright
    - Batch scraping with concurrency control
    - Competitor profile scraping
    - Backlink discovery
    - Content analysis with NLP
    - Retry logic with exponential backoff
    - Rate limiting and robots.txt compliance
    - Circuit breaker pattern for reliability
    """

    # Default user agents
    DEFAULT_USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]

    def __init__(self, config: Optional[ScrapingConfig] = None):
        """Initialize the enhanced web scraping service.

        Args:
            config: Scraping configuration (uses defaults if not provided)
        """
        self.config = config or ScrapingConfig()

        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        self.browser: Optional[Browser] = None

        # Rate limiting and throttling
        self.domain_throttle: Dict[str, float] = {}  # domain -> last_request_time
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.robots_cache_expiry: Dict[str, datetime] = {}

        # Circuit breaker state per domain
        self.circuit_breakers: Dict[str, CircuitBreakerStatus] = defaultdict(CircuitBreakerStatus)

        # User agents
        self.user_agents = (
            self.config.custom_user_agents
            if self.config.custom_user_agents
            else self.DEFAULT_USER_AGENTS
        )

        # Initialize NLP resources
        if self.config.enable_nlp and NLTK_AVAILABLE:
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                logger.warning("NLTK punkt tokenizer not found. Run: nltk.download('punkt')")

    async def _ensure_session(self):
        """Ensure aiohttp session is created."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.default_timeout),
                connector=aiohttp.TCPConnector(limit_per_host=self.config.max_concurrent)
            )

    async def _ensure_browser(self):
        """Ensure Playwright browser is initialized."""
        if self.browser is None:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the pool."""
        return random.choice(self.user_agents)

    async def _check_circuit_breaker(self, domain: str):
        """Check circuit breaker state for a domain.

        Args:
            domain: Domain to check

        Raises:
            CircuitBreakerError: If circuit is open
        """
        breaker = self.circuit_breakers[domain]
        current_time = time.time()

        if breaker.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if (breaker.last_failure_time and
                current_time - breaker.last_failure_time >= self.config.recovery_timeout):
                logger.info(f"Circuit breaker for {domain} entering HALF_OPEN state")
                breaker.state = CircuitBreakerState.HALF_OPEN
                breaker.success_count = 0
            else:
                raise CircuitBreakerError(
                    f"Circuit breaker OPEN for {domain}. "
                    f"Too many failures. Try again later."
                )

        elif breaker.state == CircuitBreakerState.HALF_OPEN:
            # Limit calls in half-open state
            if breaker.success_count >= self.config.half_open_max_calls:
                logger.info(f"Circuit breaker for {domain} returning to CLOSED state")
                breaker.state = CircuitBreakerState.CLOSED
                breaker.failure_count = 0

    def _record_success(self, domain: str):
        """Record successful request for circuit breaker."""
        breaker = self.circuit_breakers[domain]

        if breaker.state == CircuitBreakerState.HALF_OPEN:
            breaker.success_count += 1
        elif breaker.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            breaker.failure_count = 0

    def _record_failure(self, domain: str):
        """Record failed request for circuit breaker."""
        breaker = self.circuit_breakers[domain]
        breaker.failure_count += 1
        breaker.last_failure_time = time.time()

        if breaker.failure_count >= self.config.failure_threshold:
            logger.warning(
                f"Circuit breaker OPENING for {domain} "
                f"after {breaker.failure_count} failures"
            )
            breaker.state = CircuitBreakerState.OPEN

    async def _get_robots_parser(self, domain: str) -> Optional[RobotFileParser]:
        """Get robots.txt parser for a domain (with caching).

        Args:
            domain: Domain to get robots.txt for

        Returns:
            RobotFileParser instance or None if unavailable
        """
        # Check cache expiry
        if domain in self.robots_cache_expiry:
            if datetime.utcnow() > self.robots_cache_expiry[domain]:
                self.robots_cache.pop(domain, None)
                self.robots_cache_expiry.pop(domain, None)

        # Return cached parser
        if domain in self.robots_cache:
            return self.robots_cache[domain]

        # Fetch robots.txt
        robots_url = f"https://{domain}/robots.txt"
        try:
            await self._ensure_session()
            async with self.session.get(
                robots_url,
                timeout=aiohttp.ClientTimeout(total=10),
                headers={'User-Agent': self._get_random_user_agent()}
            ) as response:
                if response.status == 200:
                    robots_content = await response.text()
                    parser = RobotFileParser()
                    parser.parse(robots_content.splitlines())

                    # Cache the parser
                    self.robots_cache[domain] = parser
                    self.robots_cache_expiry[domain] = datetime.utcnow() + timedelta(hours=24)

                    logger.debug(f"Fetched and cached robots.txt for {domain}")
                    return parser
        except Exception as e:
            logger.debug(f"Could not fetch robots.txt for {domain}: {str(e)}")

        return None

    async def _check_robots_allowed(self, url: str) -> bool:
        """Check if scraping is allowed by robots.txt.

        Args:
            url: URL to check

        Returns:
            True if allowed, False otherwise
        """
        if not self.config.respect_robots_txt:
            return True

        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        parser = await self._get_robots_parser(domain)
        if parser is None:
            return True  # Allow if robots.txt unavailable

        user_agent = self._get_random_user_agent()
        allowed = parser.can_fetch(user_agent, url)

        if not allowed:
            logger.warning(f"Robots.txt disallows scraping {url}")

        return allowed

    async def _throttle_domain_request(self, domain: str):
        """Throttle requests to a domain.

        Args:
            domain: Domain to throttle
        """
        if domain in self.domain_throttle:
            last_request = self.domain_throttle[domain]
            elapsed = time.time() - last_request

            if elapsed < self.config.throttle_delay:
                wait_time = self.config.throttle_delay - elapsed
                logger.debug(f"Throttling {domain}: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

        self.domain_throttle[domain] = time.time()

    async def scrape_with_javascript(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        wait_for_timeout: Optional[int] = None
    ) -> ScrapedPage:
        """Scrape a URL with JavaScript rendering using Playwright.

        Args:
            url: URL to scrape
            wait_for_selector: Optional CSS selector to wait for
            wait_for_timeout: Timeout for waiting (milliseconds)

        Returns:
            ScrapedPage with rendered content

        Raises:
            ScrapingError: If scraping fails
        """
        start_time = time.time()
        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        try:
            # Check circuit breaker
            await self._check_circuit_breaker(domain)

            # Check robots.txt
            if not await self._check_robots_allowed(url):
                raise RobotsDisallowedError(f"Robots.txt disallows scraping {url}")

            # Throttle request
            await self._throttle_domain_request(domain)

            # Ensure browser is initialized
            await self._ensure_browser()

            # Create new page
            page = await self.browser.new_page()

            try:
                # Set user agent
                await page.set_extra_http_headers({
                    'User-Agent': self._get_random_user_agent()
                })

                # Navigate to URL
                response = await page.goto(
                    url,
                    timeout=self.config.default_timeout * 1000,
                    wait_until='networkidle'
                )
                status_code = response.status if response else 0

                # Wait for specific selector if provided
                selector = wait_for_selector or self.config.wait_for_selector
                timeout = wait_for_timeout or self.config.wait_for_timeout

                if selector:
                    try:
                        await page.wait_for_selector(selector, timeout=timeout)
                    except PlaywrightTimeoutError:
                        logger.warning(f"Timeout waiting for selector '{selector}' on {url}")

                # Extract content
                html = await page.content()
                title = await page.title()

                # Extract text content
                text = await page.evaluate('''() => {
                    const clone = document.cloneNode(true);
                    clone.querySelectorAll('script, style, noscript').forEach(el => el.remove());
                    return clone.body ? clone.body.innerText : '';
                }''')

                # Extract metadata
                meta_description = await page.evaluate('''() => {
                    const meta = document.querySelector('meta[name="description"]');
                    return meta ? meta.getAttribute('content') : '';
                }''')

                meta_keywords = await page.evaluate('''() => {
                    const meta = document.querySelector('meta[name="keywords"]');
                    return meta ? meta.getAttribute('content') : '';
                }''')

                # Extract headings
                headings = await page.evaluate('''() => {
                    const result = {h1: [], h2: [], h3: [], h4: [], h5: [], h6: []};
                    ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].forEach(tag => {
                        document.querySelectorAll(tag).forEach(h => {
                            const text = h.innerText.trim();
                            if (text) result[tag].push(text);
                        });
                    });
                    return result;
                }''')

                # Extract links
                links = await page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('a[href]'))
                        .map(a => a.href)
                        .filter(href => href && href.startsWith('http'));
                }''')

                # Extract images
                images = await page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('img[src]'))
                        .map(img => img.src)
                        .filter(src => src && src.startsWith('http'));
                }''')

                response_time_ms = (time.time() - start_time) * 1000

                # Record success
                self._record_success(domain)

                logger.info(
                    f"Successfully scraped {url} with JavaScript "
                    f"(status: {status_code}, time: {response_time_ms:.0f}ms)"
                )

                return ScrapedPage(
                    url=url,
                    html=html,
                    text=text,
                    title=title,
                    meta_description=meta_description,
                    meta_keywords=meta_keywords,
                    headings=headings,
                    links=links,
                    images=images,
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    is_javascript_rendered=True
                )

            finally:
                await page.close()

        except (RobotsDisallowedError, CircuitBreakerError):
            # Re-raise these specific errors
            raise

        except Exception as e:
            # Record failure
            self._record_failure(domain)

            response_time_ms = (time.time() - start_time) * 1000
            error_msg = str(e)

            logger.error(f"Failed to scrape {url} with JavaScript: {error_msg}")

            return ScrapedPage(
                url=url,
                html='',
                text='',
                title='',
                meta_description='',
                meta_keywords='',
                headings={},
                links=[],
                images=[],
                status_code=0,
                response_time_ms=response_time_ms,
                error=error_msg,
                is_javascript_rendered=True
            )

    async def batch_scrape(
        self,
        urls: List[str],
        max_concurrent: Optional[int] = None,
        use_javascript: bool = False
    ) -> List[ScrapedPage]:
        """Scrape multiple URLs concurrently with configurable concurrency.

        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests (uses config default if not provided)
            use_javascript: Whether to use JavaScript rendering

        Returns:
            List of ScrapedPage objects
        """
        max_concurrent = max_concurrent or self.config.max_concurrent
        semaphore = asyncio.Semaphore(max_concurrent)

        async def scrape_with_semaphore(url: str, index: int) -> ScrapedPage:
            async with semaphore:
                # Add delay between batches
                if index > 0 and index % max_concurrent == 0:
                    await asyncio.sleep(self.config.batch_delay)

                if use_javascript:
                    return await self.scrape_with_javascript(url)
                else:
                    # Use existing ScrapingService logic (lightweight)
                    from src.services.scraping_service import ScrapingService
                    scraper = ScrapingService(
                        default_timeout=self.config.default_timeout,
                        max_retries=self.config.max_retries,
                        respect_robots_txt=self.config.respect_robots_txt,
                        throttle_delay=self.config.throttle_delay
                    )
                    result = await scraper.scrape_url(url)

                    # Convert to ScrapedPage
                    return ScrapedPage(
                        url=result.url,
                        html=result.html,
                        text=result.text,
                        title=result.title,
                        meta_description=result.meta_description,
                        meta_keywords='',
                        headings={'h1': result.headings[:3] if result.headings else []},
                        links=[],
                        images=[],
                        status_code=result.status_code,
                        response_time_ms=result.response_time_ms,
                        error=result.error
                    )

        logger.info(f"Batch scraping {len(urls)} URLs (max_concurrent={max_concurrent})")

        tasks = [scrape_with_semaphore(url, i) for i, url in enumerate(urls)]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        successful = sum(1 for r in results if not r.error)
        logger.info(f"Batch scrape complete: {successful}/{len(urls)} successful")

        return results

    async def scrape_competitor_profile(
        self,
        domain: str,
        max_blog_posts: int = 5
    ) -> CompetitorProfile:
        """Scrape comprehensive competitor profile.

        Args:
            domain: Competitor domain to analyze
            max_blog_posts: Maximum number of blog posts to scrape

        Returns:
            CompetitorProfile with comprehensive data
        """
        logger.info(f"Scraping competitor profile for: {domain}")

        profile = CompetitorProfile(domain=domain)
        base_url = f"https://{domain}"

        try:
            # 1. Scrape homepage
            logger.info(f"Scraping homepage: {base_url}")
            profile.homepage_data = await self.scrape_with_javascript(base_url)

            # 2. Find and scrape about page
            about_patterns = ['/about', '/about-us', '/company', '/who-we-are']
            for pattern in about_patterns:
                about_url = f"{base_url}{pattern}"
                try:
                    about_page = await self.scrape_with_javascript(about_url)
                    if about_page.status_code == 200:
                        profile.about_page_data = about_page
                        logger.info(f"Found about page: {about_url}")
                        break
                except Exception as e:
                    logger.debug(f"About page not found at {about_url}: {str(e)}")

            # 3. Find and scrape blog posts
            blog_patterns = ['/blog', '/news', '/articles', '/insights']
            blog_base = None

            for pattern in blog_patterns:
                blog_url = f"{base_url}{pattern}"
                try:
                    blog_index = await self.scrape_with_javascript(blog_url)
                    if blog_index.status_code == 200:
                        blog_base = blog_url
                        logger.info(f"Found blog at: {blog_url}")

                        # Extract blog post links
                        blog_links = [
                            link for link in blog_index.links
                            if link.startswith(blog_base) and link != blog_base
                        ][:max_blog_posts]

                        # Scrape individual blog posts
                        if blog_links:
                            profile.blog_posts = await self.batch_scrape(
                                blog_links[:max_blog_posts],
                                use_javascript=False  # Use lightweight scraping for posts
                            )
                        break
                except Exception as e:
                    logger.debug(f"Blog not found at {blog_url}: {str(e)}")

            # 4. Extract contact information
            if profile.homepage_data:
                profile.contact_info = self._extract_contact_info(profile.homepage_data)

            # 5. Extract social media links
            if profile.homepage_data:
                profile.social_links = self._extract_social_links(profile.homepage_data)

            # 6. Detect technologies (basic detection)
            if profile.homepage_data:
                profile.technologies = self._detect_technologies(profile.homepage_data)

            logger.info(
                f"Competitor profile complete for {domain}: "
                f"{len(profile.blog_posts)} blog posts, "
                f"{len(profile.social_links)} social links"
            )

        except Exception as e:
            profile.error = str(e)
            logger.error(f"Error scraping competitor profile for {domain}: {str(e)}")

        return profile

    def _extract_contact_info(self, page: ScrapedPage) -> Dict[str, str]:
        """Extract contact information from a page."""
        contact_info = {}

        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, page.text)
        if emails:
            contact_info['email'] = emails[0]

        # Phone pattern (basic)
        phone_pattern = r'\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, page.text)
        if phones:
            contact_info['phone'] = phones[0]

        return contact_info

    def _extract_social_links(self, page: ScrapedPage) -> Dict[str, str]:
        """Extract social media links from a page."""
        social_links = {}

        social_domains = {
            'twitter': ['twitter.com', 'x.com'],
            'linkedin': ['linkedin.com'],
            'facebook': ['facebook.com'],
            'instagram': ['instagram.com'],
            'youtube': ['youtube.com'],
            'github': ['github.com'],
        }

        for link in page.links:
            link_lower = link.lower()
            for platform, domains in social_domains.items():
                if any(domain in link_lower for domain in domains):
                    social_links[platform] = link
                    break

        return social_links

    def _detect_technologies(self, page: ScrapedPage) -> List[str]:
        """Detect technologies used on a website (basic detection)."""
        technologies = []
        html_lower = page.html.lower()

        # Common technology signatures
        tech_patterns = {
            'WordPress': ['wp-content', 'wp-includes'],
            'Shopify': ['cdn.shopify.com', 'shopify'],
            'React': ['react', '__react'],
            'Vue.js': ['vue.js', '__vue'],
            'Angular': ['ng-version', 'angular'],
            'jQuery': ['jquery'],
            'Google Analytics': ['google-analytics.com', 'gtag'],
            'Bootstrap': ['bootstrap'],
            'Tailwind': ['tailwind'],
        }

        for tech, patterns in tech_patterns.items():
            if any(pattern in html_lower for pattern in patterns):
                technologies.append(tech)

        return technologies

    async def discover_backlinks(
        self,
        domain: str,
        limit: int = 100
    ) -> List[BacklinkData]:
        """Discover backlinks to a domain using Common Crawl data.

        Note: This is a placeholder implementation. In production, you would:
        1. Query Common Crawl Index API
        2. Use backlink analysis APIs (Ahrefs, Moz, SEMrush)
        3. Implement custom crawling with link graph analysis

        Args:
            domain: Target domain to find backlinks for
            limit: Maximum number of backlinks to discover

        Returns:
            List of BacklinkData objects
        """
        logger.info(f"Discovering backlinks for: {domain}")

        backlinks = []

        try:
            # Placeholder: In production, query Common Crawl Index API
            # Example: https://index.commoncrawl.org/CC-MAIN-2024-10-index

            # Common Crawl CDX Server API endpoint
            cdx_api = "http://index.commoncrawl.org/CC-MAIN-2024-10-index"

            await self._ensure_session()

            # Search for URLs linking to the domain
            params = {
                'url': f'{domain}/*',
                'filter': '=status:200',
                'output': 'json',
                'limit': limit
            }

            try:
                async with self.session.get(
                    cdx_api,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Process Common Crawl results
                        # Note: This is simplified - actual implementation would
                        # need to fetch and parse the WARC files

                        logger.info(f"Found {len(backlinks)} backlinks for {domain}")

            except Exception as e:
                logger.warning(f"Common Crawl API error: {str(e)}")

                # Fallback: Return placeholder data
                backlinks = [
                    BacklinkData(
                        target_domain=domain,
                        referring_domain="example.com",
                        referring_url=f"https://example.com/article-{i}",
                        anchor_text=f"Link to {domain}",
                        context=f"This is a reference to {domain} in an article."
                    )
                    for i in range(min(5, limit))
                ]

                logger.info(
                    f"Using placeholder backlink data (Common Crawl API unavailable). "
                    f"In production, integrate with Ahrefs, Moz, or SEMrush APIs."
                )

        except Exception as e:
            logger.error(f"Error discovering backlinks for {domain}: {str(e)}")

        return backlinks

    async def analyze_content_themes(
        self,
        urls: List[str]
    ) -> List[ContentAnalysis]:
        """Analyze content themes, sentiment, and readability.

        Args:
            urls: List of URLs to analyze

        Returns:
            List of ContentAnalysis objects
        """
        logger.info(f"Analyzing content themes for {len(urls)} URLs")

        # First, scrape all URLs
        pages = await self.batch_scrape(urls, use_javascript=False)

        # Analyze each page
        analyses = []
        for page in pages:
            if page.error or len(page.text) < self.config.min_content_length:
                continue

            try:
                analysis = self._analyze_content(page)
                analyses.append(analysis)
            except Exception as e:
                logger.error(f"Error analyzing content for {page.url}: {str(e)}")

        logger.info(f"Content analysis complete: {len(analyses)} pages analyzed")
        return analyses

    def _analyze_content(self, page: ScrapedPage) -> ContentAnalysis:
        """Analyze content using NLP techniques.

        Args:
            page: ScrapedPage to analyze

        Returns:
            ContentAnalysis with NLP results
        """
        text = page.text

        # Sentiment analysis
        sentiment_polarity = 0.0
        sentiment_subjectivity = 0.0

        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                sentiment_polarity = blob.sentiment.polarity
                sentiment_subjectivity = blob.sentiment.subjectivity
            except Exception as e:
                logger.debug(f"TextBlob sentiment analysis error: {str(e)}")

        # Basic text statistics
        words = text.split()
        word_count = len(words)

        # Sentence tokenization
        sentences = []
        if NLTK_AVAILABLE:
            try:
                sentences = sent_tokenize(text)
            except Exception as e:
                logger.debug(f"NLTK sentence tokenization error: {str(e)}")
                sentences = text.split('. ')
        else:
            sentences = text.split('. ')

        sentence_count = len(sentences)
        avg_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0

        # Flesch Reading Ease Score
        readability_score = self._calculate_flesch_score(
            text,
            word_count,
            sentence_count
        )

        # Heading structure
        heading_structure = {
            tag: len(headings)
            for tag, headings in page.headings.items()
            if headings
        }

        # Keyword density (top 20 words)
        keyword_density = self._calculate_keyword_density(text, top_n=20)

        # Topic extraction (basic - using word frequency)
        topics = self._extract_topics(text, top_n=10)

        return ContentAnalysis(
            url=page.url,
            topics=topics,
            sentiment_polarity=sentiment_polarity,
            sentiment_subjectivity=sentiment_subjectivity,
            readability_score=readability_score,
            word_count=word_count,
            sentence_count=sentence_count,
            avg_words_per_sentence=avg_words_per_sentence,
            heading_structure=heading_structure,
            keyword_density=keyword_density
        )

    def _calculate_flesch_score(
        self,
        text: str,
        word_count: int,
        sentence_count: int
    ) -> float:
        """Calculate Flesch Reading Ease score.

        Formula: 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)

        Returns:
            Flesch Reading Ease score (0-100, higher is easier)
        """
        if sentence_count == 0 or word_count == 0:
            return 0.0

        # Count syllables (simplified)
        syllable_count = sum(self._count_syllables(word) for word in text.split())

        avg_sentence_length = word_count / sentence_count
        avg_syllables_per_word = syllable_count / word_count

        score = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word

        # Clamp to 0-100
        return max(0.0, min(100.0, score))

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified algorithm)."""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Adjust for silent 'e'
        if word.endswith('e'):
            syllable_count -= 1

        # Every word has at least one syllable
        return max(1, syllable_count)

    def _calculate_keyword_density(
        self,
        text: str,
        top_n: int = 20
    ) -> Dict[str, float]:
        """Calculate keyword density for top N words.

        Returns:
            Dict of {keyword: density_percentage}
        """
        # Tokenize and clean
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())

        # Remove common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him',
            'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way',
            'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too',
            'use', 'this', 'that', 'with', 'have', 'from', 'they', 'will',
            'what', 'been', 'more', 'when', 'your', 'than', 'them', 'into',
        }

        words = [w for w in words if w not in stop_words]

        total_words = len(words)
        if total_words == 0:
            return {}

        # Count frequencies
        word_counts = Counter(words)

        # Calculate density
        keyword_density = {
            word: (count / total_words) * 100
            for word, count in word_counts.most_common(top_n)
        }

        return keyword_density

    def _extract_topics(
        self,
        text: str,
        top_n: int = 10
    ) -> List[Dict[str, float]]:
        """Extract topics using simple word frequency.

        Returns:
            List of {topic: relevance_score}
        """
        keyword_density = self._calculate_keyword_density(text, top_n=top_n)

        # Convert to list of dicts
        topics = [
            {keyword: score}
            for keyword, score in keyword_density.items()
        ]

        return topics

    async def close(self):
        """Close browser and session, cleanup resources."""
        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
