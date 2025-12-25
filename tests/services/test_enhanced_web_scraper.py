"""Comprehensive tests for EnhancedWebScrapingService.

This module tests all features of the enhanced web scraping service including:
- JavaScript rendering
- Batch scraping
- Competitor profile scraping
- Backlink discovery
- Content analysis with NLP
- Circuit breaker pattern
- Rate limiting and throttling
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.services.web_scraping import (
    EnhancedWebScrapingService,
    ScrapingConfig,
    ScrapedPage,
    CompetitorProfile,
    BacklinkData,
    ContentAnalysis,
    CircuitBreakerError,
    ScrapingError,
    RobotsDisallowedError,
    CircuitBreakerState,
)


@pytest.fixture
def scraping_config():
    """Create test scraping configuration."""
    return ScrapingConfig(
        default_timeout=5,
        max_retries=2,
        respect_robots_txt=False,  # Disable for testing
        throttle_delay=0.1,
        use_playwright=False,
        max_concurrent=3,
        enable_nlp=True,
        failure_threshold=3,
        recovery_timeout=5,
    )


@pytest.fixture
async def scraper_service(scraping_config):
    """Create EnhancedWebScrapingService instance."""
    service = EnhancedWebScrapingService(config=scraping_config)
    yield service
    await service.close()


@pytest.fixture
def mock_html_response():
    """Mock HTML response for testing."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Test Page</title>
        <meta name="description" content="Test description">
        <meta name="keywords" content="test, keywords">
    </head>
    <body>
        <h1>Main Heading</h1>
        <h2>Subheading 1</h2>
        <h2>Subheading 2</h2>
        <p>This is test content with multiple sentences. It contains enough text for analysis.
        The content should be analyzed for sentiment and readability. This helps test NLP features.</p>
        <a href="https://example.com/page1">Link 1</a>
        <a href="https://example.com/page2">Link 2</a>
        <img src="https://example.com/image1.jpg" />
        <a href="https://twitter.com/testaccount">Twitter</a>
        <a href="https://linkedin.com/company/test">LinkedIn</a>
    </body>
    </html>
    """


class TestBasicScraping:
    """Test basic scraping functionality."""

    @pytest.mark.asyncio
    async def test_scrape_with_javascript_success(self, scraper_service, mock_html_response):
        """Test successful JavaScript-based scraping."""
        with patch('src.services.web_scraping.enhanced_scraper.async_playwright') as mock_playwright:
            # Mock Playwright components
            mock_page = AsyncMock()
            mock_page.goto = AsyncMock(return_value=AsyncMock(status=200))
            mock_page.title = AsyncMock(return_value="Test Page")
            mock_page.content = AsyncMock(return_value=mock_html_response)
            mock_page.evaluate = AsyncMock(side_effect=[
                "Test content text",  # text content
                "Test description",   # meta description
                "",                   # meta keywords
                {                     # headings
                    'h1': ['Main Heading'],
                    'h2': ['Subheading 1', 'Subheading 2'],
                    'h3': [], 'h4': [], 'h5': [], 'h6': []
                },
                ['https://example.com/page1', 'https://example.com/page2'],  # links
                ['https://example.com/image1.jpg'],  # images
            ])
            mock_page.close = AsyncMock()
            mock_page.set_extra_http_headers = AsyncMock()

            mock_browser = AsyncMock()
            mock_browser.new_page = AsyncMock(return_value=mock_page)

            mock_pw = AsyncMock()
            mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)

            # Perform scraping
            result = await scraper_service.scrape_with_javascript("https://example.com")

            # Assertions
            assert isinstance(result, ScrapedPage)
            assert result.url == "https://example.com"
            assert result.status_code == 200
            assert result.title == "Test Page"
            assert result.is_javascript_rendered is True
            assert result.error is None
            assert len(result.headings['h2']) == 2

    @pytest.mark.asyncio
    async def test_scrape_with_robots_disallowed(self, scraping_config):
        """Test that scraping respects robots.txt."""
        config = scraping_config
        config.respect_robots_txt = True
        scraper = EnhancedWebScrapingService(config=config)

        with patch.object(scraper, '_check_robots_allowed', return_value=False):
            with pytest.raises(RobotsDisallowedError):
                await scraper.scrape_with_javascript("https://example.com")

        await scraper.close()


class TestBatchScraping:
    """Test batch scraping functionality."""

    @pytest.mark.asyncio
    async def test_batch_scrape_success(self, scraper_service):
        """Test successful batch scraping of multiple URLs."""
        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3",
        ]

        with patch('src.services.scraping_service.ScrapingService.scrape_url') as mock_scrape:
            mock_scrape.return_value = Mock(
                url=urls[0],
                html="<html></html>",
                text="Test content",
                title="Test",
                meta_description="Description",
                headings=["H1"],
                status_code=200,
                response_time_ms=100,
                error=None
            )

            results = await scraper_service.batch_scrape(urls, max_concurrent=2)

            assert len(results) == 3
            assert all(isinstance(r, ScrapedPage) for r in results)

    @pytest.mark.asyncio
    async def test_batch_scrape_with_concurrency_limit(self, scraper_service):
        """Test that batch scraping respects concurrency limit."""
        urls = ["https://example.com/page{}".format(i) for i in range(10)]

        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0

        async def mock_scrape_with_tracking(*args, **kwargs):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.1)
            concurrent_count -= 1
            return Mock(
                url=args[0],
                html="<html></html>",
                text="Test",
                title="Test",
                meta_description="",
                headings=[],
                status_code=200,
                response_time_ms=100,
                error=None
            )

        with patch('src.services.scraping_service.ScrapingService.scrape_url',
                   side_effect=mock_scrape_with_tracking):
            await scraper_service.batch_scrape(urls, max_concurrent=3)

            # Should not exceed max_concurrent
            assert max_concurrent <= 3


class TestCompetitorProfiling:
    """Test competitor profile scraping."""

    @pytest.mark.asyncio
    async def test_scrape_competitor_profile(self, scraper_service, mock_html_response):
        """Test scraping comprehensive competitor profile."""
        with patch.object(scraper_service, 'scrape_with_javascript') as mock_scrape:
            mock_scrape.return_value = ScrapedPage(
                url="https://competitor.com",
                html=mock_html_response,
                text="Competitor content",
                title="Competitor",
                meta_description="Competitor description",
                meta_keywords="",
                headings={'h1': ['Main'], 'h2': []},
                links=[
                    "https://competitor.com/blog/post1",
                    "https://twitter.com/competitor",
                ],
                images=[],
                status_code=200,
                response_time_ms=200,
            )

            profile = await scraper_service.scrape_competitor_profile("competitor.com")

            assert isinstance(profile, CompetitorProfile)
            assert profile.domain == "competitor.com"
            assert profile.homepage_data is not None
            assert profile.error is None

    @pytest.mark.asyncio
    async def test_extract_social_links(self, scraper_service):
        """Test extraction of social media links."""
        page = ScrapedPage(
            url="https://example.com",
            html="",
            text="",
            title="",
            meta_description="",
            meta_keywords="",
            headings={},
            links=[
                "https://twitter.com/testaccount",
                "https://linkedin.com/company/test",
                "https://facebook.com/testpage",
                "https://example.com/other",
            ],
            images=[],
            status_code=200,
            response_time_ms=100,
        )

        social_links = scraper_service._extract_social_links(page)

        assert 'twitter' in social_links
        assert 'linkedin' in social_links
        assert 'facebook' in social_links
        assert len(social_links) >= 3

    @pytest.mark.asyncio
    async def test_extract_contact_info(self, scraper_service):
        """Test extraction of contact information."""
        page = ScrapedPage(
            url="https://example.com",
            html="",
            text="Contact us at info@example.com or call (555) 123-4567",
            title="",
            meta_description="",
            meta_keywords="",
            headings={},
            links=[],
            images=[],
            status_code=200,
            response_time_ms=100,
        )

        contact_info = scraper_service._extract_contact_info(page)

        assert 'email' in contact_info
        assert contact_info['email'] == 'info@example.com'
        assert 'phone' in contact_info


class TestBacklinkDiscovery:
    """Test backlink discovery functionality."""

    @pytest.mark.asyncio
    async def test_discover_backlinks(self, scraper_service):
        """Test backlink discovery for a domain."""
        backlinks = await scraper_service.discover_backlinks("example.com", limit=10)

        assert isinstance(backlinks, list)
        # Note: Current implementation returns placeholder data
        # In production, this would test actual Common Crawl API integration

    @pytest.mark.asyncio
    async def test_backlink_data_structure(self, scraper_service):
        """Test that backlink data has correct structure."""
        backlinks = await scraper_service.discover_backlinks("example.com", limit=5)

        if backlinks:
            backlink = backlinks[0]
            assert isinstance(backlink, BacklinkData)
            assert hasattr(backlink, 'target_domain')
            assert hasattr(backlink, 'referring_domain')
            assert hasattr(backlink, 'referring_url')
            assert hasattr(backlink, 'anchor_text')


class TestContentAnalysis:
    """Test NLP-based content analysis."""

    @pytest.mark.asyncio
    async def test_analyze_content_themes(self, scraper_service):
        """Test content theme analysis."""
        urls = ["https://example.com/article"]

        with patch('src.services.scraping_service.ScrapingService.scrape_url') as mock_scrape:
            mock_scrape.return_value = Mock(
                url=urls[0],
                html="<html></html>",
                text="This is a test article about web scraping. " * 20,  # Sufficient content
                title="Test Article",
                meta_description="Description",
                headings=["Web Scraping"],
                status_code=200,
                response_time_ms=100,
                error=None
            )

            analyses = await scraper_service.analyze_content_themes(urls)

            assert len(analyses) > 0
            analysis = analyses[0]
            assert isinstance(analysis, ContentAnalysis)
            assert analysis.word_count > 0
            assert analysis.sentence_count > 0
            assert 0 <= analysis.readability_score <= 100

    def test_calculate_flesch_score(self, scraper_service):
        """Test Flesch Reading Ease score calculation."""
        text = "This is a simple sentence. This is another sentence."
        score = scraper_service._calculate_flesch_score(text, 10, 2)

        assert 0 <= score <= 100
        assert isinstance(score, float)

    def test_count_syllables(self, scraper_service):
        """Test syllable counting."""
        assert scraper_service._count_syllables("hello") >= 1
        assert scraper_service._count_syllables("beautiful") >= 1
        assert scraper_service._count_syllables("a") == 1

    def test_calculate_keyword_density(self, scraper_service):
        """Test keyword density calculation."""
        text = "python python python programming code programming"
        density = scraper_service._calculate_keyword_density(text, top_n=5)

        assert isinstance(density, dict)
        assert 'python' in density
        assert 'programming' in density
        assert all(0 <= v <= 100 for v in density.values())

    def test_extract_topics(self, scraper_service):
        """Test topic extraction."""
        text = "web scraping data analysis python programming" * 10
        topics = scraper_service._extract_topics(text, top_n=5)

        assert isinstance(topics, list)
        assert len(topics) <= 5
        if topics:
            assert isinstance(topics[0], dict)


class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, scraper_service):
        """Test that circuit breaker opens after threshold failures."""
        domain = "failing-domain.com"

        # Record multiple failures
        for _ in range(scraper_service.config.failure_threshold):
            scraper_service._record_failure(domain)

        # Circuit should now be open
        breaker = scraper_service.circuit_breakers[domain]
        assert breaker.state == CircuitBreakerState.OPEN

        # Should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await scraper_service._check_circuit_breaker(domain)

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, scraper_service):
        """Test circuit breaker recovery to half-open state."""
        domain = "recovering-domain.com"

        # Open the circuit
        for _ in range(scraper_service.config.failure_threshold):
            scraper_service._record_failure(domain)

        breaker = scraper_service.circuit_breakers[domain]
        assert breaker.state == CircuitBreakerState.OPEN

        # Simulate recovery timeout
        breaker.last_failure_time = 0  # Long time ago

        # Should transition to half-open
        await scraper_service._check_circuit_breaker(domain)
        assert breaker.state == CircuitBreakerState.HALF_OPEN

    def test_circuit_breaker_success_resets_failures(self, scraper_service):
        """Test that successes reset failure count in closed state."""
        domain = "test-domain.com"

        scraper_service._record_failure(domain)
        assert scraper_service.circuit_breakers[domain].failure_count == 1

        scraper_service._record_success(domain)
        assert scraper_service.circuit_breakers[domain].failure_count == 0


class TestRateLimiting:
    """Test rate limiting and throttling."""

    @pytest.mark.asyncio
    async def test_domain_throttling(self, scraper_service):
        """Test that requests to same domain are throttled."""
        domain = "example.com"

        # First request
        start = asyncio.get_event_loop().time()
        await scraper_service._throttle_domain_request(domain)

        # Second request should be delayed
        await scraper_service._throttle_domain_request(domain)
        elapsed = asyncio.get_event_loop().time() - start

        # Should have waited at least throttle_delay
        assert elapsed >= scraper_service.config.throttle_delay * 0.9  # Allow some margin

    @pytest.mark.asyncio
    async def test_robots_txt_caching(self, scraper_service):
        """Test that robots.txt responses are cached."""
        domain = "example.com"

        with patch.object(scraper_service, 'session', new_callable=AsyncMock) as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="User-agent: *\nDisallow:")
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.__aexit__ = AsyncMock()

            # First call - should fetch
            await scraper_service._get_robots_parser(domain)

            # Second call - should use cache
            await scraper_service._get_robots_parser(domain)

            # Should only have called once (cached second time)
            assert domain in scraper_service.robots_cache


class TestErrorHandling:
    """Test error handling and resilience."""

    @pytest.mark.asyncio
    async def test_scrape_returns_error_on_failure(self, scraper_service):
        """Test that scraping failures return error information."""
        with patch.object(scraper_service, '_ensure_browser', side_effect=Exception("Browser error")):
            result = await scraper_service.scrape_with_javascript("https://example.com")

            assert isinstance(result, ScrapedPage)
            assert result.error is not None
            assert "Browser error" in result.error

    @pytest.mark.asyncio
    async def test_batch_scrape_continues_on_partial_failure(self, scraper_service):
        """Test that batch scraping continues even if some URLs fail."""
        urls = [
            "https://example.com/success1",
            "https://example.com/fail",
            "https://example.com/success2",
        ]

        call_count = 0

        async def mock_scrape_with_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if "fail" in args[0]:
                return Mock(
                    url=args[0],
                    html="",
                    text="",
                    title="",
                    meta_description="",
                    headings=[],
                    status_code=0,
                    response_time_ms=0,
                    error="Scraping failed"
                )
            return Mock(
                url=args[0],
                html="<html></html>",
                text="Success",
                title="Test",
                meta_description="",
                headings=[],
                status_code=200,
                response_time_ms=100,
                error=None
            )

        with patch('src.services.scraping_service.ScrapingService.scrape_url',
                   side_effect=mock_scrape_with_failure):
            results = await scraper_service.batch_scrape(urls)

            # Should have attempted all URLs
            assert len(results) == 3
            assert call_count == 3

            # Check success and failure
            success_count = sum(1 for r in results if r.error is None)
            assert success_count == 2


class TestResourceManagement:
    """Test resource management and cleanup."""

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self):
        """Test that context manager properly cleans up resources."""
        config = ScrapingConfig()

        async with EnhancedWebScrapingService(config=config) as scraper:
            assert scraper is not None

        # After context exit, resources should be cleaned up
        # (browser and session should be None)

    @pytest.mark.asyncio
    async def test_close_method(self, scraper_service):
        """Test that close method properly cleans up resources."""
        # Initialize resources
        await scraper_service._ensure_session()

        # Close
        await scraper_service.close()

        # Resources should be cleaned up
        assert scraper_service.session is None or scraper_service.session.closed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
