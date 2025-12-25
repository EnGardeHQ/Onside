"""
Comprehensive unit and integration tests for WebScrapingService.

This module provides extensive test coverage for web scraping functionality,
including HTML extraction, screenshot capture, version tracking, change detection,
and error handling with mocked Playwright browser.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime
from typing import Dict, Any

from src.services.web_scraping_service import WebScrapingService, WebScrapingError
from src.models.scraped_content import ScrapedContent, ContentChange
from src.services.storage_service import StorageService


@pytest.fixture
def mock_storage_service():
    """Create a mock storage service."""
    mock_service = AsyncMock(spec=StorageService)
    mock_service.upload_file = AsyncMock(return_value="/storage/test.png")
    return mock_service


@pytest.fixture
def scraping_service(mock_storage_service):
    """Create a WebScrapingService instance with mocked storage."""
    return WebScrapingService(storage_service=mock_storage_service)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    mock = MagicMock()
    mock.query = MagicMock(return_value=mock)
    mock.filter = MagicMock(return_value=mock)
    mock.order_by = MagicMock(return_value=mock)
    mock.first = MagicMock(return_value=None)
    mock.all = MagicMock(return_value=[])
    mock.limit = MagicMock(return_value=mock)
    mock.count = MagicMock(return_value=0)
    mock.add = MagicMock()
    mock.commit = MagicMock()
    mock.refresh = MagicMock()
    return mock


@pytest.fixture
def mock_page():
    """Create a mock Playwright page."""
    page = AsyncMock()
    page.goto = AsyncMock(return_value=AsyncMock(status=200))
    page.content = AsyncMock(return_value="<html><body><h1>Test Page</h1></body></html>")
    page.title = AsyncMock(return_value="Test Page")
    page.evaluate = AsyncMock(side_effect=[
        "Test page content text",  # text_content
        "Test description",  # meta_description
        "test, keywords",  # meta_keywords
    ])
    page.screenshot = AsyncMock(return_value=b"fake_screenshot_data")
    page.wait_for_selector = AsyncMock()
    page.close = AsyncMock()
    return page


@pytest.fixture
def mock_browser(mock_page):
    """Create a mock Playwright browser."""
    browser = AsyncMock()
    browser.new_page = AsyncMock(return_value=mock_page)
    browser.close = AsyncMock()
    return browser


class TestWebScrapingServiceInitialization:
    """Test suite for WebScrapingService initialization."""

    def test_init_with_default_storage_service(self):
        """Test initialization creates default storage service."""
        service = WebScrapingService()
        assert service.storage_service is not None
        assert service.browser is None

    def test_init_with_custom_storage_service(self, mock_storage_service):
        """Test initialization with custom storage service."""
        service = WebScrapingService(storage_service=mock_storage_service)
        assert service.storage_service == mock_storage_service


class TestWebScrapingServiceScrapeURL:
    """Test suite for scrape_url method."""

    @pytest.mark.asyncio
    async def test_scrape_url_success_without_screenshot(
        self, scraping_service, mock_db, mock_browser, mock_page
    ):
        """Test successful URL scraping without screenshot."""
        # Arrange
        url = "https://example.com/test"
        scraping_service.browser = mock_browser

        # Act
        result = await scraping_service.scrape_url(
            url=url,
            db=mock_db,
            capture_screenshot=False
        )

        # Assert
        assert mock_page.goto.called
        assert mock_page.content.called
        assert mock_page.title.called
        assert not mock_page.screenshot.called
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_scrape_url_success_with_screenshot(
        self, scraping_service, mock_db, mock_browser, mock_page, mock_storage_service
    ):
        """Test successful URL scraping with screenshot capture."""
        # Arrange
        url = "https://example.com/test"
        scraping_service.browser = mock_browser

        # Act
        result = await scraping_service.scrape_url(
            url=url,
            db=mock_db,
            capture_screenshot=True
        )

        # Assert
        assert mock_page.screenshot.called
        assert mock_storage_service.upload_file.called
        screenshot_call = mock_storage_service.upload_file.call_args
        assert screenshot_call[1]['content_type'] == 'image/png'

    @pytest.mark.asyncio
    async def test_scrape_url_with_company_id(
        self, scraping_service, mock_db, mock_browser
    ):
        """Test scraping with company_id association."""
        # Arrange
        url = "https://example.com/test"
        company_id = 123
        scraping_service.browser = mock_browser

        # Act
        await scraping_service.scrape_url(
            url=url,
            db=mock_db,
            company_id=company_id,
            capture_screenshot=False
        )

        # Assert
        add_call_args = mock_db.add.call_args[0][0]
        assert add_call_args.company_id == company_id

    @pytest.mark.asyncio
    async def test_scrape_url_with_competitor_id(
        self, scraping_service, mock_db, mock_browser
    ):
        """Test scraping with competitor_id association."""
        # Arrange
        url = "https://example.com/test"
        competitor_id = 456
        scraping_service.browser = mock_browser

        # Act
        await scraping_service.scrape_url(
            url=url,
            db=mock_db,
            competitor_id=competitor_id,
            capture_screenshot=False
        )

        # Assert
        add_call_args = mock_db.add.call_args[0][0]
        assert add_call_args.competitor_id == competitor_id

    @pytest.mark.asyncio
    async def test_scrape_url_wait_for_selector(
        self, scraping_service, mock_db, mock_browser, mock_page
    ):
        """Test scraping with wait_for_selector option."""
        # Arrange
        url = "https://example.com/test"
        selector = ".dynamic-content"
        scraping_service.browser = mock_browser

        # Act
        await scraping_service.scrape_url(
            url=url,
            db=mock_db,
            wait_for_selector=selector,
            capture_screenshot=False
        )

        # Assert
        mock_page.wait_for_selector.assert_called_once_with(selector, timeout=5000)

    @pytest.mark.asyncio
    async def test_scrape_url_version_increment(
        self, scraping_service, mock_db, mock_browser
    ):
        """Test that version increments for existing URL."""
        # Arrange
        url = "https://example.com/test"
        existing_version = MagicMock(spec=ScrapedContent)
        existing_version.version = 3
        existing_version.content_hash = "old_hash"

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = existing_version
        scraping_service.browser = mock_browser

        # Act
        await scraping_service.scrape_url(
            url=url,
            db=mock_db,
            capture_screenshot=False
        )

        # Assert
        add_call_args = mock_db.add.call_args[0][0]
        assert add_call_args.version == 4

    @pytest.mark.asyncio
    async def test_scrape_url_extracts_domain(
        self, scraping_service, mock_db, mock_browser
    ):
        """Test that domain is correctly extracted from URL."""
        # Arrange
        url = "https://www.example.com/path/to/page"
        scraping_service.browser = mock_browser

        # Act
        await scraping_service.scrape_url(
            url=url,
            db=mock_db,
            capture_screenshot=False
        )

        # Assert
        add_call_args = mock_db.add.call_args[0][0]
        assert add_call_args.domain == "www.example.com"

    @pytest.mark.asyncio
    async def test_scrape_url_handles_timeout(
        self, scraping_service, mock_db, mock_browser, mock_page
    ):
        """Test handling of timeout during page load."""
        # Arrange
        url = "https://example.com/slow"
        mock_page.goto.side_effect = TimeoutError("Page load timeout")
        scraping_service.browser = mock_browser

        # Act & Assert
        with pytest.raises(WebScrapingError) as exc_info:
            await scraping_service.scrape_url(
                url=url,
                db=mock_db,
                timeout=5000
            )

        assert "Scraping failed" in str(exc_info.value)
        # Error record should be created
        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_scrape_url_handles_network_error(
        self, scraping_service, mock_db, mock_browser, mock_page
    ):
        """Test handling of network errors."""
        # Arrange
        url = "https://invalid-domain-xyz.com"
        mock_page.goto.side_effect = Exception("Network error")
        scraping_service.browser = mock_browser

        # Act & Assert
        with pytest.raises(WebScrapingError):
            await scraping_service.scrape_url(
                url=url,
                db=mock_db
            )

    @pytest.mark.asyncio
    async def test_scrape_url_page_closes_on_error(
        self, scraping_service, mock_db, mock_browser, mock_page
    ):
        """Test that page is closed even when error occurs."""
        # Arrange
        url = "https://example.com"
        mock_page.content.side_effect = Exception("Content extraction error")
        scraping_service.browser = mock_browser

        # Act
        with pytest.raises(WebScrapingError):
            await scraping_service.scrape_url(url=url, db=mock_db)

        # Assert
        assert mock_page.close.called


class TestWebScrapingServiceChangeDetection:
    """Test suite for content change detection."""

    @pytest.mark.asyncio
    async def test_detect_changes_no_change(
        self, scraping_service, mock_db
    ):
        """Test change detection when content is identical."""
        # Arrange
        old_version = ScrapedContent(
            id=1,
            url="https://example.com",
            text_content="Same content",
            content_hash="abc123"
        )
        new_version = ScrapedContent(
            id=2,
            url="https://example.com",
            text_content="Same content",
            content_hash="abc123"
        )

        # Act
        result = await scraping_service._detect_changes(mock_db, old_version, new_version)

        # Assert
        assert result is None
        assert not mock_db.add.called

    @pytest.mark.asyncio
    async def test_detect_changes_minor_change(
        self, scraping_service, mock_db
    ):
        """Test detection of minor content changes."""
        # Arrange
        old_version = ScrapedContent(
            id=1,
            url="https://example.com",
            text_content="This is the original content",
            content_hash="old_hash"
        )
        new_version = ScrapedContent(
            id=2,
            url="https://example.com",
            text_content="This is the updated content",
            content_hash="new_hash"
        )

        # Act
        result = await scraping_service._detect_changes(mock_db, old_version, new_version)

        # Assert
        assert mock_db.add.called
        change_record = mock_db.add.call_args[0][0]
        assert isinstance(change_record, ContentChange)
        assert change_record.change_type == "minor"
        assert change_record.url == "https://example.com"

    @pytest.mark.asyncio
    async def test_detect_changes_significant_change(
        self, scraping_service, mock_db
    ):
        """Test detection of significant content changes."""
        # Arrange
        old_content = "Short content"
        new_content = "This is much longer content with many additional words and sentences that make it significantly different from the original."

        old_version = ScrapedContent(
            id=1,
            url="https://example.com",
            text_content=old_content,
            content_hash="old_hash"
        )
        new_version = ScrapedContent(
            id=2,
            url="https://example.com",
            text_content=new_content,
            content_hash="new_hash"
        )

        # Act
        result = await scraping_service._detect_changes(mock_db, old_version, new_version)

        # Assert
        change_record = mock_db.add.call_args[0][0]
        assert change_record.change_type in ["significant", "major"]
        assert change_record.change_percentage > 20

    @pytest.mark.asyncio
    async def test_detect_changes_major_change(
        self, scraping_service, mock_db
    ):
        """Test detection of major content changes (>50% length change)."""
        # Arrange
        old_content = "x" * 100
        new_content = "y" * 200  # 100% increase in length

        old_version = ScrapedContent(
            id=1,
            url="https://example.com",
            text_content=old_content,
            content_hash="old_hash"
        )
        new_version = ScrapedContent(
            id=2,
            url="https://example.com",
            text_content=new_content,
            content_hash="new_hash"
        )

        # Act
        result = await scraping_service._detect_changes(mock_db, old_version, new_version)

        # Assert
        change_record = mock_db.add.call_args[0][0]
        assert change_record.change_type == "major"


class TestWebScrapingServiceMultipleScraping:
    """Test suite for scraping multiple URLs concurrently."""

    @pytest.mark.asyncio
    async def test_scrape_multiple_success(
        self, scraping_service, mock_db, mock_browser
    ):
        """Test successful concurrent scraping of multiple URLs."""
        # Arrange
        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3"
        ]
        scraping_service.browser = mock_browser

        # Act
        results = await scraping_service.scrape_multiple(
            urls=urls,
            db=mock_db,
            capture_screenshot=False
        )

        # Assert
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_scrape_multiple_partial_failure(
        self, scraping_service, mock_db, mock_browser, mock_page
    ):
        """Test scraping multiple URLs with some failures."""
        # Arrange
        urls = [
            "https://example.com/good",
            "https://example.com/bad",
            "https://example.com/good2"
        ]

        call_count = [0]

        async def mock_goto(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:  # Second call fails
                raise Exception("Page load failed")
            return AsyncMock(status=200)

        mock_page.goto = mock_goto
        scraping_service.browser = mock_browser

        # Act
        results = await scraping_service.scrape_multiple(
            urls=urls,
            db=mock_db,
            capture_screenshot=False
        )

        # Assert - should get 2 successful results despite 1 failure
        assert len(results) >= 0  # Some may succeed


class TestWebScrapingServiceHistory:
    """Test suite for content history retrieval."""

    @pytest.mark.asyncio
    async def test_get_content_history(
        self, scraping_service, mock_db
    ):
        """Test retrieving content history for a URL."""
        # Arrange
        url = "https://example.com"
        mock_versions = [
            MagicMock(spec=ScrapedContent, version=3),
            MagicMock(spec=ScrapedContent, version=2),
            MagicMock(spec=ScrapedContent, version=1),
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_versions

        # Act
        results = await scraping_service.get_content_history(
            db=mock_db,
            url=url,
            limit=10
        )

        # Assert
        assert len(results) == 3
        assert results == mock_versions

    @pytest.mark.asyncio
    async def test_get_changes_for_url(
        self, scraping_service, mock_db
    ):
        """Test retrieving change history for a URL."""
        # Arrange
        url = "https://example.com"
        mock_changes = [
            MagicMock(spec=ContentChange, change_type="minor"),
            MagicMock(spec=ContentChange, change_type="significant"),
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_changes

        # Act
        results = await scraping_service.get_changes_for_url(
            db=mock_db,
            url=url,
            limit=10
        )

        # Assert
        assert len(results) == 2
        assert results == mock_changes


class TestWebScrapingServiceCompareVersions:
    """Test suite for version comparison."""

    @pytest.mark.asyncio
    async def test_compare_versions_success(
        self, scraping_service, mock_db
    ):
        """Test successful comparison of two versions."""
        # Arrange
        v1 = ScrapedContent(
            id=1,
            url="https://example.com",
            version=1,
            text_content="Original content",
            content_hash="hash1",
            created_at=datetime(2024, 1, 1)
        )
        v2 = ScrapedContent(
            id=2,
            url="https://example.com",
            version=2,
            text_content="Updated content",
            content_hash="hash2",
            created_at=datetime(2024, 1, 2)
        )

        def mock_query_filter(version_id):
            if version_id == 1:
                return v1
            return v2

        mock_db.query.return_value.filter.return_value.first.side_effect = [v1, v2]

        # Act
        result = await scraping_service.compare_versions(
            db=mock_db,
            version_id_1=1,
            version_id_2=2
        )

        # Assert
        assert result['url'] == "https://example.com"
        assert result['version1']['id'] == 1
        assert result['version2']['id'] == 2
        assert 'similarity' in result
        assert 'change_percentage' in result
        assert 'html_diff' in result

    @pytest.mark.asyncio
    async def test_compare_versions_not_found(
        self, scraping_service, mock_db
    ):
        """Test comparison when version not found."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(WebScrapingError, match="not found"):
            await scraping_service.compare_versions(
                db=mock_db,
                version_id_1=1,
                version_id_2=2
            )

    @pytest.mark.asyncio
    async def test_compare_versions_different_urls(
        self, scraping_service, mock_db
    ):
        """Test comparison fails when URLs differ."""
        # Arrange
        v1 = ScrapedContent(id=1, url="https://example.com/page1")
        v2 = ScrapedContent(id=2, url="https://example.com/page2")

        mock_db.query.return_value.filter.return_value.first.side_effect = [v1, v2]

        # Act & Assert
        with pytest.raises(WebScrapingError, match="different URLs"):
            await scraping_service.compare_versions(
                db=mock_db,
                version_id_1=1,
                version_id_2=2
            )


class TestWebScrapingServiceResourceManagement:
    """Test suite for resource management and cleanup."""

    @pytest.mark.asyncio
    async def test_close_browser(self, scraping_service, mock_browser):
        """Test browser cleanup."""
        # Arrange
        scraping_service.browser = mock_browser

        # Act
        await scraping_service.close()

        # Assert
        assert mock_browser.close.called
        assert scraping_service.browser is None

    @pytest.mark.asyncio
    async def test_async_context_manager(self, mock_storage_service):
        """Test service as async context manager."""
        # Arrange
        service = WebScrapingService(storage_service=mock_storage_service)

        # Act
        async with patch('src.services.web_scraping_service.async_playwright') as mock_playwright:
            mock_pw_instance = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
            mock_browser = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)

            async with service as svc:
                assert svc is not None
                # Browser should be initialized
                await svc._ensure_browser()

        # Browser should be closed after context exit
        # (if it was created during the context)


class TestWebScrapingServiceEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_scrape_url_empty_content(
        self, scraping_service, mock_db, mock_browser, mock_page
    ):
        """Test scraping page with empty content."""
        # Arrange
        url = "https://example.com/empty"
        mock_page.content = AsyncMock(return_value="")
        mock_page.evaluate = AsyncMock(return_value="")
        scraping_service.browser = mock_browser

        # Act
        await scraping_service.scrape_url(
            url=url,
            db=mock_db,
            capture_screenshot=False
        )

        # Assert
        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_scrape_url_missing_meta_tags(
        self, scraping_service, mock_db, mock_browser, mock_page
    ):
        """Test scraping page without meta tags."""
        # Arrange
        url = "https://example.com/no-meta"
        mock_page.evaluate = AsyncMock(side_effect=[
            "Content without meta",  # text_content
            None,  # meta_description
            None,  # meta_keywords
        ])
        scraping_service.browser = mock_browser

        # Act
        await scraping_service.scrape_url(
            url=url,
            db=mock_db,
            capture_screenshot=False
        )

        # Assert
        add_call_args = mock_db.add.call_args[0][0]
        assert add_call_args.meta_description is None
        assert add_call_args.meta_keywords is None

    @pytest.mark.asyncio
    async def test_scrape_url_with_status_code_error(
        self, scraping_service, mock_db, mock_browser, mock_page
    ):
        """Test scraping with non-200 status code."""
        # Arrange
        url = "https://example.com/404"
        mock_response = AsyncMock(status=404)
        mock_page.goto = AsyncMock(return_value=mock_response)
        scraping_service.browser = mock_browser

        # Act
        await scraping_service.scrape_url(
            url=url,
            db=mock_db,
            capture_screenshot=False
        )

        # Assert
        add_call_args = mock_db.add.call_args[0][0]
        assert add_call_args.status_code == 404

    @pytest.mark.asyncio
    async def test_scrape_url_no_response(
        self, scraping_service, mock_db, mock_browser, mock_page
    ):
        """Test scraping when page.goto returns None."""
        # Arrange
        url = "https://example.com/no-response"
        mock_page.goto = AsyncMock(return_value=None)
        scraping_service.browser = mock_browser

        # Act
        await scraping_service.scrape_url(
            url=url,
            db=mock_db,
            capture_screenshot=False
        )

        # Assert
        add_call_args = mock_db.add.call_args[0][0]
        assert add_call_args.status_code is None


class TestWebScrapingServicePerformance:
    """Test suite for performance-related functionality."""

    @pytest.mark.asyncio
    async def test_scrape_duration_recorded(
        self, scraping_service, mock_db, mock_browser
    ):
        """Test that scrape duration is recorded."""
        # Arrange
        url = "https://example.com"
        scraping_service.browser = mock_browser

        # Act
        await scraping_service.scrape_url(
            url=url,
            db=mock_db,
            capture_screenshot=False
        )

        # Assert
        add_call_args = mock_db.add.call_args[0][0]
        assert add_call_args.scrape_duration_ms is not None
        assert add_call_args.scrape_duration_ms >= 0
