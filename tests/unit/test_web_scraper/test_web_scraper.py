"""Tests for the WebScraperService."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from bs4 import BeautifulSoup

from src.services.web_scraper.web_scraper import WebScraperService

@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session

@pytest.fixture
def web_scraper_service(mock_session):
    """Create a WebScraperService with a mock session."""
    service = WebScraperService(mock_session)
    # Mock the _fetch_url method to avoid actual HTTP requests
    service._fetch_url_mock = (
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="description" content="Test description">
            <meta name="keywords" content="test, keywords">
            <meta property="og:title" content="OG Title">
            <meta property="og:description" content="OG Description">
            <meta property="og:image" content="https://example.com/image.jpg">
            <title>Test Page</title>
        </head>
        <body>
            <div class="content">
                <h1>Test Content</h1>
                <p>This is a test page.</p>
                <div class="social">
                    <span class="likes">42 likes</span>
                    <span class="shares">10 shares</span>
                    <span class="comments">5 comments</span>
                </div>
            </div>
        </body>
        </html>
        """,
        None
    )
    return service

class TestWebScraperService:
    """Tests for the WebScraperService."""

    @patch('src.services.web_scraper.web_scraper.select')
    async def test_scrape_link(self, mock_select, web_scraper_service, mock_session):
        """Test scraping a link."""
        # Mock the link
        mock_link = MagicMock()
        mock_link.id = 1
        mock_link.url = "https://example.com"
        mock_link.title = "Example"
        mock_link.last_scraped_at = None
        mock_link.meta = {}

        # Mock the _get_link method
        web_scraper_service._get_link = AsyncMock(return_value=mock_link)
        
        # Mock the _take_screenshot method
        web_scraper_service._take_screenshot = AsyncMock(return_value="/path/to/screenshot.png")

        # Call the method
        result = await web_scraper_service.scrape_link(1)

        # Check the result
        assert result["success"] is True
        assert result["link_id"] == 1
        assert "metadata" in result
        assert result["metadata"]["title"] == "Test Page"
        assert result["metadata"]["description"] == "Test description"
        assert result["metadata"]["og_title"] == "OG Title"

        # Verify that the session was committed
        mock_session.commit.assert_awaited_once()

    @patch('src.services.web_scraper.web_scraper.select')
    async def test_scrape_domain(self, mock_select, web_scraper_service, mock_session):
        """Test scraping all links for a domain."""
        # Mock the domain
        mock_domain = MagicMock()
        mock_domain.id = 1
        mock_domain.domain_name = "example.com"

        # Mock the links
        mock_link1 = MagicMock()
        mock_link1.id = 1
        mock_link1.url = "https://example.com/page1"
        mock_link1.title = "Page 1"
        mock_link1.last_scraped_at = None
        mock_link1.meta = {}

        mock_link2 = MagicMock()
        mock_link2.id = 2
        mock_link2.url = "https://example.com/page2"
        mock_link2.title = "Page 2"
        mock_link2.last_scraped_at = None
        mock_link2.meta = {}

        # Mock the _get_domain method
        web_scraper_service._get_domain = AsyncMock(return_value=mock_domain)
        
        # Mock the _get_links_for_domain method
        web_scraper_service._get_links_for_domain = AsyncMock(return_value=[mock_link1, mock_link2])
        
        # Mock the scrape_link method
        web_scraper_service.scrape_link = AsyncMock(side_effect=[
            {"success": True, "link_id": 1},
            {"success": True, "link_id": 2}
        ])

        # Call the method
        result = await web_scraper_service.scrape_domain(1)

        # Check the result
        assert result["success"] is True
        assert result["links_processed"] == 2
        assert result["successful"] == 2
        assert result["failed"] == 0
        assert len(result["results"]) == 2

    def test_extract_metadata(self, web_scraper_service):
        """Test extracting metadata from HTML content."""
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="description" content="Test description">
            <meta name="keywords" content="test, keywords">
            <meta property="og:title" content="OG Title">
            <meta property="og:description" content="OG Description">
            <meta property="og:image" content="https://example.com/image.jpg">
            <title>Test Page</title>
            <link rel="canonical" href="https://example.com/canonical" />
        </head>
        <body>
            <div class="content">
                <h1>Test Content</h1>
                <p>This is a test page.</p>
            </div>
        </body>
        </html>
        """
        
        metadata = web_scraper_service._extract_metadata(html_content)
        
        assert metadata["title"] == "Test Page"
        assert metadata["description"] == "Test description"
        assert metadata["keywords"] == ["test", "keywords"]
        assert metadata["og_title"] == "OG Title"
        assert metadata["og_description"] == "OG Description"
        assert metadata["og_image"] == "https://example.com/image.jpg"
        assert metadata["canonical"] == "https://example.com/canonical"
        assert metadata["language"] == "en"

    def test_extract_engagement_metrics(self, web_scraper_service):
        """Test extracting engagement metrics from HTML content."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta property="og:likes" content="42">
            <meta property="og:shares" content="10">
            <meta property="og:comments" content="5">
        </head>
        <body>
            <div class="content">
                <div class="social">
                    <span class="likes">42 likes</span>
                    <span class="shares">10 shares</span>
                    <span class="comments">5 comments</span>
                </div>
            </div>
        </body>
        </html>
        """
        
        metrics = web_scraper_service._extract_engagement_metrics(html_content)
        
        assert metrics["likes"] == 42
        assert metrics["shares"] == 10
        assert metrics["comments"] == 5
        assert metrics["share_buttons"] == 0  # No elements with class="share" or class="social"
        assert metrics["comment_elements"] == 0  # No elements with class="comment" or class="disqus"
