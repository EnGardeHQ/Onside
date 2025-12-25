"""
Test suite for the complete JLL analysis workflow.

Following Semantic Seed BDD/TDD standards, this test suite ensures that:
1. The campaign creation process works correctly
2. Competitor identification functions properly
3. The web scraping workflow captures required data
4. The PDF report is generated with all required sections
"""
import pytest
import os
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

from src.services.campaign.campaign_service import CampaignService
from src.services.web_scraper.web_scraper import WebScraperService
from src.services.link_search.link_search import LinkSearchService
from src.services.engagement_extraction.engagement_extraction import EngagementExtractionService
from src.workflow.scraping_workflow import scrape_company_data, scrape_competitors_data
from src.services.pdf_export import PDFExportService
from src.services.pdf_visualization import create_swot_table, create_market_position_chart

# Fixture for mock database session
@pytest.fixture
def mock_db():
    """Mock database session for testing."""
    db = AsyncMock()
    return db

@pytest.fixture
def campaign_service(mock_db):
    """Create a CampaignService instance with a mock DB."""
    return CampaignService(mock_db)

@pytest.fixture
def web_scraper_service(mock_db):
    """Create a WebScraperService instance with a mock DB."""
    return WebScraperService(mock_db)

@pytest.fixture
def link_search_service(mock_db):
    """Create a LinkSearchService instance with a mock DB."""
    return LinkSearchService(mock_db)

@pytest.fixture
def engagement_extraction_service(mock_db):
    """Create an EngagementExtractionService instance with a mock DB."""
    return EngagementExtractionService(mock_db)

@pytest.fixture
def pdf_export_service():
    """Create a PDFExportService instance with a temporary export dir."""
    temp_dir = Path("test_exports")
    temp_dir.mkdir(exist_ok=True)
    return PDFExportService(export_dir=str(temp_dir))

@pytest.mark.asyncio
async def test_campaign_creation(campaign_service):
    """
    GIVEN a CampaignService and valid company data
    WHEN creating a new campaign
    THEN it should return a success response with campaign details
    """
    # Setup
    campaign_service._db.execute = AsyncMock()
    campaign_service._db.execute.return_value.fetchone.return_value = {"id": 1, "name": "Test Company"}
    
    # Execute
    result = await campaign_service.create_campaign(
        name="Test Campaign", 
        primary_company_id=1,
        description="Test Description"
    )
    
    # Assert
    assert result["success"] is True
    assert "campaign" in result
    assert result["campaign"]["name"] == "Test Campaign"
    assert result["campaign"]["primary_company_id"] == 1

@pytest.mark.asyncio
async def test_competitor_identification(campaign_service):
    """
    GIVEN a campaign with a primary company
    WHEN identifying competitors
    THEN it should return relevant competitors with relevance scores
    """
    # Setup
    campaign_service._db.execute = AsyncMock()
    # Mock that it finds the campaign
    campaign_service._db.execute.return_value.fetchone.side_effect = [
        {"id": 1, "report_id": 1, "primary_company_id": 1},
        {"id": 1, "name": "JLL", "description": "Real estate services", "industry": "real_estate_services"}
    ]
    # Mock that it finds competitors
    campaign_service._db.execute.return_value.fetchall.return_value = [
        {"id": 2, "name": "CBRE", "description": "Commercial real estate services", "industry": "real_estate_services"},
        {"id": 3, "name": "Cushman & Wakefield", "description": "Property management", "industry": "real_estate_services"}
    ]
    
    # Execute
    result = await campaign_service.identify_competitors(campaign_id=1, max_competitors=2)
    
    # Assert
    assert len(result) == 2
    assert "name" in result[0]
    assert "relevance_score" in result[0]
    assert result[0]["relevance_score"] > 0

@pytest.mark.asyncio
async def test_scrape_company_data(web_scraper_service, link_search_service, engagement_extraction_service):
    """
    GIVEN web scraping services and a company ID
    WHEN scraping data for the company
    THEN it should return scraped data with engagement metrics
    """
    # Setup mocks
    web_scraper_service._db.execute = AsyncMock()
    web_scraper_service._db.execute.return_value.fetchone.return_value = {
        "id": 1, "name": "JLL", "website": "https://www.jll.com"
    }
    
    # Mock that domain is found
    link_search_service._db.execute = AsyncMock()
    link_search_service._db.execute.return_value.fetchone.return_value = {"id": 1, "domain": "jll.com"}
    
    # Mock that links are found
    link_search_service._db.execute.return_value.fetchall.return_value = [
        {"id": 1, "url": "https://www.jll.com/en/about-jll"},
        {"id": 2, "url": "https://www.jll.com/en/services"}
    ]
    
    # Mock content scraping
    web_scraper_service.scrape_url = AsyncMock(return_value={"success": True, "content": "Test content"})
    
    # Mock engagement extraction
    engagement_extraction_service.extract_metrics = AsyncMock(
        return_value={"success": True, "engagement_score": 0.85}
    )
    
    # Execute
    result = await scrape_company_data(
        web_scraper_service, 
        link_search_service,
        engagement_extraction_service,
        company_id=1
    )
    
    # Assert
    assert result["success"] is True
    assert "links_scraped" in result
    assert result["links_scraped"] > 0

@pytest.mark.asyncio
async def test_scrape_competitors_data(web_scraper_service, link_search_service, engagement_extraction_service):
    """
    GIVEN web scraping services and a list of competitors
    WHEN scraping data for all competitors
    THEN it should return aggregated scraping results
    """
    # Setup mocks - similar to company scraping but for multiple companies
    web_scraper_service._db.execute = AsyncMock()
    web_scraper_service._db.execute.return_value.fetchone.side_effect = [
        {"id": 2, "name": "CBRE", "website": "https://www.cbre.com"},
        {"id": 3, "name": "Cushman", "website": "https://www.cushmanwakefield.com"}
    ]
    
    # Mock domain finding/creation
    link_search_service._db.execute = AsyncMock()
    link_search_service._db.execute.return_value.fetchone.side_effect = [
        {"id": 2, "domain": "cbre.com"},
        {"id": 3, "domain": "cushmanwakefield.com"}
    ]
    
    # Mock link finding
    link_search_service._db.execute.return_value.fetchall.side_effect = [
        [{"id": 3, "url": "https://www.cbre.com/about"}],
        [{"id": 4, "url": "https://www.cushmanwakefield.com/en/about-us"}]
    ]
    
    # Mock content scraping
    web_scraper_service.scrape_url = AsyncMock(return_value={"success": True, "content": "Test content"})
    
    # Mock engagement extraction
    engagement_extraction_service.extract_metrics = AsyncMock(
        return_value={"success": True, "engagement_score": 0.75}
    )
    
    # Competitors to scrape
    competitors = [
        {"id": 2, "name": "CBRE", "relevance_score": 0.9},
        {"id": 3, "name": "Cushman & Wakefield", "relevance_score": 0.8}
    ]
    
    # Execute
    result = await scrape_competitors_data(
        web_scraper_service,
        link_search_service,
        engagement_extraction_service,
        competitors
    )
    
    # Assert
    assert "successful_scrapes" in result
    assert result["successful_scrapes"] > 0

@pytest.mark.asyncio
async def test_pdf_visualization_swot_table():
    """
    GIVEN analysis data with SWOT components
    WHEN creating a SWOT table
    THEN it should return a properly formatted Table object
    """
    # Setup
    analysis = {
        "strengths": ["Market leadership", "Strong brand"],
        "weaknesses": ["High costs", "Legacy systems"],
        "opportunities": ["Digital transformation", "New markets"],
        "threats": ["Increasing competition", "Economic downturn"]
    }
    styles = getSampleStyleSheet()
    
    # Execute
    with patch('reportlab.platypus.Table') as mock_table:
        mock_table.return_value.setStyle = MagicMock()
        result = await create_swot_table(analysis, styles)
        
        # Assert
        assert mock_table.called
        assert mock_table.return_value.setStyle.called

@pytest.mark.asyncio
async def test_pdf_visualization_market_chart():
    """
    GIVEN analysis data with market position information
    WHEN creating a market position chart
    THEN it should return an Image object
    """
    # Setup
    analysis = {
        "company_name": "JLL",
        "market_share": 0.15,
        "growth_rate": 0.04,
        "competitors": [
            {"name": "CBRE", "market_share": 0.18, "growth": 0.03},
            {"name": "Cushman & Wakefield", "market_share": 0.12, "growth": 0.02}
        ]
    }
    
    # Execute - with appropriate mocking to avoid actually creating images
    with patch('matplotlib.pyplot.figure'), \
         patch('matplotlib.pyplot.scatter'), \
         patch('matplotlib.pyplot.annotate'), \
         patch('matplotlib.pyplot.savefig'), \
         patch('matplotlib.pyplot.close'), \
         patch('reportlab.platypus.Image') as mock_image:
        
        result = await create_market_position_chart(analysis)
        
        # Assert
        assert mock_image.called
