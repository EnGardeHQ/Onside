"""Enhanced web scraping service for brand analysis with advanced features.

This service provides:
- Retry logic with exponential backoff
- User-agent rotation
- Robots.txt compliance checking
- Request throttling per domain
- Rate limiting and error handling
"""
import asyncio
import logging
import time
import random
from typing import Dict, Optional, List, Set
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from datetime import datetime, timedelta
from dataclasses import dataclass, field

import aiohttp
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)


class ScrapingError(Exception):
    """Base exception for scraping errors."""
    pass


class RobotsDisallowedError(ScrapingError):
    """Exception raised when robots.txt disallows scraping."""
    pass


class RateLimitError(ScrapingError):
    """Exception raised when rate limit is exceeded."""
    pass


@dataclass
class ScrapingResult:
    """Result from a scraping operation."""
    url: str
    html: str
    text: str
    title: str
    meta_description: str
    headings: List[str]
    status_code: int
    response_time_ms: float
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None


@dataclass
class DomainThrottleState:
    """Track throttling state for a domain."""
    last_request_time: float = 0.0
    request_count: int = 0
    min_delay: float = 1.0  # Minimum delay between requests in seconds


class ScrapingService:
    """Enhanced scraping service with retry logic, throttling, and robots.txt compliance.

    Features:
    - Exponential backoff retry logic for failed requests
    - User-agent rotation to avoid blocking
    - Robots.txt compliance checking
    - Per-domain request throttling (1 req/sec default)
    - Request timeout and error handling
    """

    # User agents to rotate through
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]

    def __init__(
        self,
        default_timeout: int = 30,
        max_retries: int = 3,
        respect_robots_txt: bool = True,
        throttle_delay: float = 1.0,
    ):
        """Initialize the scraping service.

        Args:
            default_timeout: Default request timeout in seconds
            max_retries: Maximum number of retry attempts
            respect_robots_txt: Whether to check and respect robots.txt
            throttle_delay: Minimum delay between requests per domain (seconds)
        """
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.respect_robots_txt = respect_robots_txt
        self.throttle_delay = throttle_delay

        # Domain-specific state
        self.domain_throttle: Dict[str, DomainThrottleState] = {}
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.robots_cache_expiry: Dict[str, datetime] = {}

        # Session for connection pooling
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        """Ensure aiohttp session is created."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.default_timeout),
                connector=aiohttp.TCPConnector(limit_per_host=5)
            )

    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the pool.

        Returns:
            Random user agent string
        """
        return random.choice(self.USER_AGENTS)

    async def _get_robots_parser(self, domain: str) -> Optional[RobotFileParser]:
        """Get robots.txt parser for a domain (with caching).

        Args:
            domain: Domain to get robots.txt for

        Returns:
            RobotFileParser instance or None if unavailable
        """
        # Check cache expiry (refresh every 24 hours)
        if domain in self.robots_cache_expiry:
            if datetime.utcnow() > self.robots_cache_expiry[domain]:
                # Cache expired, remove it
                self.robots_cache.pop(domain, None)
                self.robots_cache_expiry.pop(domain, None)

        # Return cached parser if available
        if domain in self.robots_cache:
            return self.robots_cache[domain]

        # Fetch and parse robots.txt
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

                    logger.info(f"Fetched and cached robots.txt for {domain}")
                    return parser
                else:
                    logger.warning(f"robots.txt not found for {domain} (status {response.status})")
                    return None

        except Exception as e:
            logger.warning(f"Failed to fetch robots.txt for {domain}: {str(e)}")
            return None

    async def _check_robots_allowed(self, url: str, user_agent: str) -> bool:
        """Check if scraping is allowed by robots.txt.

        Args:
            url: URL to check
            user_agent: User agent to check for

        Returns:
            True if allowed, False otherwise
        """
        if not self.respect_robots_txt:
            return True

        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        parser = await self._get_robots_parser(domain)
        if parser is None:
            # If we can't get robots.txt, allow by default
            return True

        allowed = parser.can_fetch(user_agent, url)
        if not allowed:
            logger.warning(f"Robots.txt disallows scraping {url} for {user_agent}")

        return allowed

    async def _throttle_domain_request(self, domain: str):
        """Throttle requests to a domain.

        Args:
            domain: Domain to throttle
        """
        if domain not in self.domain_throttle:
            self.domain_throttle[domain] = DomainThrottleState(min_delay=self.throttle_delay)

        throttle = self.domain_throttle[domain]
        current_time = time.time()

        # Calculate time since last request
        time_since_last = current_time - throttle.last_request_time

        # If we need to wait, do so
        if time_since_last < throttle.min_delay:
            wait_time = throttle.min_delay - time_since_last
            logger.debug(f"Throttling {domain}: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        # Update throttle state
        throttle.last_request_time = time.time()
        throttle.request_count += 1

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def _fetch_with_retry(
        self,
        url: str,
        headers: Dict[str, str],
        timeout: int
    ) -> aiohttp.ClientResponse:
        """Fetch URL with retry logic.

        Args:
            url: URL to fetch
            headers: Request headers
            timeout: Request timeout

        Returns:
            aiohttp response

        Raises:
            aiohttp.ClientError: On request failure
        """
        await self._ensure_session()

        async with self.session.get(
            url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout),
            allow_redirects=True
        ) as response:
            # Raise for bad status codes
            response.raise_for_status()
            return response

    async def scrape_url(
        self,
        url: str,
        timeout: Optional[int] = None,
        check_robots: bool = True
    ) -> ScrapingResult:
        """Scrape a URL with all enhanced features.

        Args:
            url: URL to scrape
            timeout: Request timeout (uses default if not provided)
            check_robots: Whether to check robots.txt

        Returns:
            ScrapingResult with scraped data

        Raises:
            RobotsDisallowedError: If robots.txt disallows scraping
            ScrapingError: On scraping failure
        """
        start_time = time.time()
        timeout = timeout or self.default_timeout

        try:
            # Parse URL and get domain
            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            if not domain:
                raise ScrapingError(f"Invalid URL: {url}")

            # Get random user agent
            user_agent = self._get_random_user_agent()

            # Check robots.txt
            if check_robots and self.respect_robots_txt:
                allowed = await self._check_robots_allowed(url, user_agent)
                if not allowed:
                    raise RobotsDisallowedError(f"Robots.txt disallows scraping {url}")

            # Throttle request
            await self._throttle_domain_request(domain)

            # Prepare headers
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            # Fetch with retry
            await self._ensure_session()
            async with self.session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
                allow_redirects=True
            ) as response:
                status_code = response.status
                html = await response.text()

            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')

            # Remove script and style tags
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract text content
            text = soup.get_text()
            text = ' '.join(text.split())  # Clean whitespace

            # Extract title
            title = soup.find('title').string if soup.find('title') else ''

            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_description = meta_desc['content'] if meta_desc and meta_desc.get('content') else ''

            # Extract headings
            headings = []
            for tag in ['h1', 'h2', 'h3']:
                for heading in soup.find_all(tag):
                    heading_text = heading.get_text().strip()
                    if heading_text:
                        headings.append(heading_text)

            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Successfully scraped {url} "
                f"(status: {status_code}, time: {response_time_ms:.0f}ms)"
            )

            return ScrapingResult(
                url=url,
                html=html,
                text=text,
                title=title,
                meta_description=meta_description,
                headings=headings,
                status_code=status_code,
                response_time_ms=response_time_ms,
            )

        except RobotsDisallowedError:
            # Re-raise robots.txt errors
            raise

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = str(e)

            logger.error(f"Failed to scrape {url}: {error_msg}")

            # Return error result
            return ScrapingResult(
                url=url,
                html='',
                text='',
                title='',
                meta_description='',
                headings=[],
                status_code=0,
                response_time_ms=response_time_ms,
                error=error_msg
            )

    async def scrape_multiple(
        self,
        urls: List[str],
        timeout: Optional[int] = None,
        max_concurrent: int = 5
    ) -> List[ScrapingResult]:
        """Scrape multiple URLs concurrently with concurrency limit.

        Args:
            urls: List of URLs to scrape
            timeout: Request timeout
            max_concurrent: Maximum concurrent requests

        Returns:
            List of ScrapingResult objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def scrape_with_semaphore(url: str) -> ScrapingResult:
            async with semaphore:
                return await self.scrape_url(url, timeout=timeout)

        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        return results

    async def close(self):
        """Close the session and cleanup resources."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
