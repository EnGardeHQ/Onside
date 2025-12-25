import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.engagement.engagement_index_service import EngagementIndexService
from src.services.analytics.google_analytics import GoogleAnalyticsService
from src.services.analytics.adobe_analytics import AdobeAnalyticsService
from src.models.seo import ContentAsset, Subject, MarketScope

@pytest.fixture
def mock_ga_metrics():
    return {
        "pageviews": 1000,
        "engaged_sessions": 500,
        "conversions": 50,
        "revenue": 1000.0
    }

@pytest.fixture
def mock_adobe_metrics():
    return {
        "visits": 800,
        "time_on_page": 180,
        "bounce_rate": 0.25,
        "conversion_rate": 0.05
    }

@pytest.fixture
def mock_ga_client(mock_ga_metrics):
    client = MagicMock()
    client.run_report = AsyncMock()
    client.run_report.return_value = mock_ga_metrics
    return client

@pytest.fixture
def mock_adobe_client(mock_adobe_metrics):
    client = MagicMock()
    client.get_content_metrics = AsyncMock(return_value=mock_adobe_metrics)
    return client

@pytest.fixture
def engagement_service(mock_ga_client, mock_adobe_client):
    ga_service = GoogleAnalyticsService(client=mock_ga_client)
    adobe_service = AdobeAnalyticsService(client=mock_adobe_client)
    
    with patch('src.services.engagement.engagement_index_service.GoogleAnalyticsService', return_value=ga_service):
        with patch('src.services.engagement.engagement_index_service.AdobeAnalyticsService', return_value=adobe_service):
            service = EngagementIndexService()
            return service

@pytest.fixture
def sample_content_asset():
    """Create a sample content asset for testing"""
    return ContentAsset(
        id=123,
        url="https://example.com/test",
        topic="technology",
        style="Technical",
        format="Article",
        market="US",
        persona={
            "type": "Technical Professional",
            "industry": "Technology",
            "company_size": "Enterprise"
        },
        google_ranking=5,
        social_engagement={"likes": 100, "shares": 50},
        likeability_score=0.85,
        subject=Subject(
            name="Artificial Intelligence",
            market_scope=MarketScope.GLOBAL,
            language="en",
            search_volume=10000,
            competition=0.75
        )
    )

@pytest.mark.asyncio
async def test_calculate_engagement_index(engagement_service, sample_content_asset):
    # Test basic engagement index calculation
    result = await engagement_service.calculate_engagement_index(
        content_asset=sample_content_asset,
        market="US",
        persona={
            "type": "Technical Professional",
            "industry": "Technology",
            "company_size": "Enterprise"
        }
    )

    # Verify structure and values
    assert "engagement_index" in result
    assert "component_scores" in result
    assert "classifications" in result
    assert "business_impact" in result
    assert "metadata" in result

    # Verify score ranges
    assert 0 <= result["engagement_index"] <= 100
    
    # Verify component scores
    component_scores = result["component_scores"]
    for score in component_scores.values():
        assert 0 <= score <= 100

@pytest.mark.asyncio
async def test_calculate_opportunity_index(engagement_service, sample_content_asset):
    # Mock competitor and landscape data
    competitor_data = {
        "ei_scores": [75.0, 80.0, 85.0],
        "content_volume": 100
    }
    
    landscape_data = {
        "ei_scores": [70.0, 75.0, 80.0],
        "content_volume": 500
    }

    result = await engagement_service.calculate_opportunity_index(
        content_asset=sample_content_asset,
        competitor_data=competitor_data,
        landscape_data=landscape_data
    )

    # Verify structure and values
    assert "opportunity_index" in result
    assert "recommendations" in result
    assert "metrics" in result

    # Verify score ranges
    assert 0 <= result["opportunity_index"] <= 100
    
    # Verify metrics
    metrics = result["metrics"]
    assert "ei_comparison" in metrics
    assert "volume_metrics" in metrics
    assert "trend_analysis" in metrics

@pytest.mark.asyncio
async def test_business_impact_calculation(engagement_service, sample_content_asset):
    result = await engagement_service._calculate_business_impact(
        content_asset=sample_content_asset,
        ei_score=85.0
    )

    # Verify structure
    assert "projected_visitors" in result
    assert "projected_conversions" in result
    assert "projected_revenue" in result
    assert "roi_estimate" in result
    assert "impact_score" in result

    # Verify values are within expected ranges
    assert 0 <= result["projected_visitors"] <= 10000
    assert 0 <= result["projected_conversions"] <= 1000
    assert 0 <= result["projected_revenue"] <= 100000
    assert 0 <= result["roi_estimate"] <= 10.0
    assert 0 <= result["impact_score"] <= 100.0

@pytest.mark.asyncio
async def test_market_adjustments(engagement_service, sample_content_asset):
    # Test different markets
    markets = ["US", "UK", "JP", "DE"]
    
    results = []
    for market in markets:
        result = await engagement_service.calculate_engagement_index(
            content_asset=sample_content_asset,
            market=market,
            persona={"type": "Technical Professional"}
        )
        results.append(result["engagement_index"])

    # Verify market adjustments are applied
    assert len(set(results)) > 1  # Scores should vary by market

@pytest.mark.asyncio
async def test_persona_adjustments(engagement_service, sample_content_asset):
    # Test different personas
    personas = [
        {"type": "Technical Professional", "industry": "Technology"},
        {"type": "Business Executive", "industry": "Finance"},
        {"type": "Marketing Manager", "industry": "Retail"}
    ]
    
    results = []
    for persona in personas:
        result = await engagement_service.calculate_engagement_index(
            content_asset=sample_content_asset,
            market="US",
            persona=persona
        )
        results.append(result["engagement_index"])

    # Verify persona adjustments are applied
    assert len(set(results)) > 1  # Scores should vary by persona

@pytest.mark.asyncio
async def test_error_handling(engagement_service):
    # Test with invalid content asset
    with pytest.raises(Exception):
        await engagement_service.calculate_engagement_index(
            content_asset=None,
            market="US",
            persona={}
        )

    # Test with invalid market
    with pytest.raises(Exception):
        await engagement_service.calculate_engagement_index(
            content_asset=sample_content_asset,
            market="INVALID",
            persona={}
        )

    # Test with missing required data
    with pytest.raises(Exception):
        await engagement_service.calculate_opportunity_index(
            content_asset=sample_content_asset,
            competitor_data={},
            landscape_data={}
        )
