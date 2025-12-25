"""Test suite for CampaignService following BDD/TDD approach."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.campaign.campaign_service import CampaignService
from src.models.company import Company
from src.models.competitor import Competitor

class TestCampaignService:
    """BDD-style tests for the Campaign Service."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        mock = AsyncMock(spec=AsyncSession)
        mock.execute = AsyncMock()
        mock.commit = AsyncMock()
        return mock
    
    @pytest.fixture
    def campaign_service(self, mock_db):
        """Campaign service with mock database."""
        return CampaignService(mock_db)
    
    async def test_create_campaign(self, campaign_service, mock_db):
        """
        GIVEN a campaign name and primary company ID
        WHEN create_campaign is called
        THEN a new campaign should be created with the specified primary company
        """
        # Arrange
        mock_db.execute.return_value.scalar_one_or_none.return_value = Company(
            id=1, 
            name="JLL", 
            domain="jll.com",
            description="Real estate services"
        )
        
        # Act
        result = await campaign_service.create_campaign(
            name="JLL Analysis",
            primary_company_id=1,
            description="Competitive analysis for JLL"
        )
        
        # Assert
        assert result["success"] is True
        assert result["campaign"]["name"] == "JLL Analysis"
        assert result["campaign"]["primary_company_id"] == 1
        assert mock_db.add.called
        assert mock_db.commit.called
    
    async def test_identify_competitors(self, campaign_service, mock_db):
        """
        GIVEN a campaign ID
        WHEN identify_competitors is called
        THEN a list of relevant competitors should be returned
        """
        # Arrange
        mock_company = Company(
            id=1, 
            name="JLL", 
            domain="jll.com",
            industry="Real Estate Services",
            description="Commercial real estate services"
        )
        
        # Mock database results for competitors
        mock_competitors = [
            Competitor(id=2, name="CBRE", domain="cbre.com", description="Real estate services company"),
            Competitor(id=3, name="Cushman & Wakefield", domain="cushmanwakefield.com", description="Global real estate services"),
            Competitor(id=4, name="Colliers", domain="colliers.com", description="Commercial real estate services")
        ]
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_company
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_competitors
        
        # Act
        result = await campaign_service.identify_competitors(campaign_id=1, max_competitors=3)
        
        # Assert
        assert len(result) == 3
        assert result[0]["name"] == "CBRE"
        assert "relevance_score" in result[0]
        assert mock_db.execute.called
