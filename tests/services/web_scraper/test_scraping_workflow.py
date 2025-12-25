"""Test suite for the integrated web scraping workflow following BDD/TDD approach."""
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.web_scraper.web_scraper import WebScraperService
from src.services.link_search.link_search import LinkSearchService
from src.services.engagement_extraction.engagement_extraction import EngagementExtractionService
from src.models.company import Company
from src.models.competitor import Competitor
from src.models.link import Link
from src.models.domain import Domain

class TestScrapingWorkflow:
    """BDD-style tests for the integrated web scraping workflow."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        mock = AsyncMock(spec=AsyncSession)
        mock.execute = AsyncMock()
        mock.commit = AsyncMock()
        return mock
    
    @pytest.fixture
    def web_scraper_service(self, mock_db):
        """Web scraper service with mock database."""
        return WebScraperService(mock_db)
    
    @pytest.fixture
    def link_search_service(self, mock_db):
        """Link search service with mock database."""
        return LinkSearchService(mock_db)
    
    @pytest.fixture
    def engagement_extraction_service(self, mock_db):
        """Engagement extraction service with mock database."""
        return EngagementExtractionService(mock_db)
    
    async def test_scrape_company_data_workflow(
        self, 
        web_scraper_service, 
        link_search_service,
        engagement_extraction_service,
        mock_db
    ):
        """
        GIVEN a company ID
        WHEN scrape_company_data is called
        THEN the company's web presence should be scraped and analyzed
        """
        # Arrange
        mock_company = Company(
            id=1, 
            name="JLL", 
            domain="jll.com",
            description="Commercial real estate services"
        )
        
        mock_domain = Domain(
            id=1,
            domain_name="jll.com",
            company_id=1
        )
        
        mock_links = [
            Link(id=1, url="https://jll.com/about", title="About JLL", domain_id=1),
            Link(id=2, url="https://jll.com/services", title="Our Services", domain_id=1)
        ]
        
        # Mock database queries
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            mock_company,  # For get_company
            mock_domain,   # For get_domain
            mock_links[0], # For get_link in scrape_link
            mock_links[1]  # For second link
        ]
        
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_links
        
        # Mock service methods
        with patch.object(
            web_scraper_service, 
            '_fetch_url', 
            return_value=("<html><body>JLL content</body></html>", None)
        ):
            with patch.object(
                web_scraper_service,
                '_take_screenshot',
                return_value="screenshots/jll_1.png"
            ):
                with patch.object(
                    engagement_extraction_service,
                    'extract_engagement_metrics',
                    return_value={"social_shares": 120, "comments": 45}
                ):
                    # Act
                    from src.workflow.scraping_workflow import scrape_company_data
                    result = await scrape_company_data(
                        web_scraper_service,
                        link_search_service,
                        engagement_extraction_service,
                        company_id=1
                    )
                    
                    # Assert
                    assert result["success"] is True
                    assert result["company_id"] == 1
                    assert "links_scraped" in result
                    assert result["links_scraped"] >= 1
                    assert "engagement_metrics_extracted" in result
