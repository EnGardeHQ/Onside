import pytest
import asyncio
from datetime import datetime
from src.services.data.data_integration_service import DataIntegrationService

@pytest.fixture
def data_service():
    return DataIntegrationService()

@pytest.fixture
def sample_content_asset():
    return {
        "id": "test_content_1",
        "title": "Test Content",
        "content": "This is a test article about artificial intelligence and machine learning.",
        "url": "https://example.com/test-content",
        "publish_date": datetime.now().isoformat(),
        "subject": {
            "name": "Artificial Intelligence",
            "industry": "Technology"
        },
        "market": "US",
        "topic": "AI/ML",
        "format": "Article",
        "target_keywords": ["AI", "machine learning", "technology"]
    }

@pytest.mark.asyncio
async def test_gather_comprehensive_data(data_service, sample_content_asset):
    """Test gathering comprehensive data from multiple sources"""
    result = await data_service.gather_comprehensive_data(sample_content_asset)
    
    # Verify structure
    assert isinstance(result, dict)
    assert "search_metrics" in result
    assert "social_metrics" in result
    assert "multimedia_metrics" in result
    assert "market_metrics" in result
    assert "metadata" in result
    
    # Verify metadata
    metadata = result["metadata"]
    assert "timestamp" in metadata
    assert "data_sources" in metadata
    assert "coverage_score" in metadata
    
    # Verify timestamp format
    timestamp = datetime.fromisoformat(metadata["timestamp"])
    assert isinstance(timestamp, datetime)

@pytest.mark.asyncio
async def test_gather_search_data(data_service, sample_content_asset):
    """Test gathering search-related data"""
    result = await data_service._gather_search_data(sample_content_asset)
    
    # Verify structure
    assert isinstance(result, dict)
    assert "search_metrics" in result
    assert "timestamp" in result
    
    # Verify search metrics
    search_metrics = result["search_metrics"]
    assert "visibility_score" in search_metrics
    assert "ranking_distribution" in search_metrics
    assert "keyword_performance" in search_metrics
    assert "click_through_rates" in search_metrics
    assert "search_intent" in search_metrics
    assert "regional_performance" in search_metrics
    
    # Verify score ranges
    assert 0 <= search_metrics["visibility_score"] <= 100
    
    # Verify keyword performance
    assert len(search_metrics["keyword_performance"]) > 0
    for keyword in sample_content_asset["target_keywords"]:
        assert keyword in search_metrics["keyword_performance"]

@pytest.mark.asyncio
async def test_gather_social_data(data_service, sample_content_asset):
    """Test gathering social media data"""
    result = await data_service._gather_social_data(sample_content_asset)
    
    # Verify structure
    assert isinstance(result, dict)
    assert "social_metrics" in result
    assert "timestamp" in result
    
    # Verify social metrics
    social_metrics = result["social_metrics"]
    assert "engagement_score" in social_metrics
    assert "platform_metrics" in social_metrics
    assert "audience_demographics" in social_metrics
    assert "sentiment_analysis" in social_metrics
    assert "viral_potential" in social_metrics
    assert "interaction_patterns" in social_metrics
    
    # Verify score ranges
    assert 0 <= social_metrics["engagement_score"] <= 100

@pytest.mark.asyncio
async def test_gather_multimedia_data(data_service, sample_content_asset):
    """Test gathering multimedia content data"""
    result = await data_service._gather_multimedia_data(sample_content_asset)
    
    # Verify structure
    assert isinstance(result, dict)
    assert "multimedia_metrics" in result
    assert "timestamp" in result
    
    # Verify multimedia metrics
    multimedia_metrics = result["multimedia_metrics"]
    assert "view_metrics" in multimedia_metrics
    assert "engagement_metrics" in multimedia_metrics
    assert "audience_retention" in multimedia_metrics
    assert "quality_scores" in multimedia_metrics
    assert "platform_performance" in multimedia_metrics

@pytest.mark.asyncio
async def test_gather_market_data(data_service, sample_content_asset):
    """Test gathering market intelligence data"""
    result = await data_service._gather_market_data(sample_content_asset)
    
    # Verify structure
    assert isinstance(result, dict)
    assert "market_metrics" in result
    assert "timestamp" in result
    
    # Verify market metrics
    market_metrics = result["market_metrics"]
    assert "market_share" in market_metrics
    assert "competitor_analysis" in market_metrics
    assert "trend_analysis" in market_metrics
    assert "audience_insights" in market_metrics
    assert "content_gaps" in market_metrics

@pytest.mark.asyncio
async def test_process_search_results(data_service):
    """Test processing search results"""
    mock_results = [
        {
            "visibility_score": 80.0,
            "ranking_distribution": {"1-3": 5, "4-10": 10},
            "keyword_performance": {
                "AI": {"volume": 1000, "position": 2},
                "machine learning": {"volume": 800, "position": 3}
            },
            "click_through_rates": {"1": 0.3, "2": 0.15},
            "search_intent": {"informational": 0.7, "commercial": 0.3},
            "regional_performance": {"US": {"traffic": 1000}}
        },
        {
            "visibility_score": 70.0,
            "ranking_distribution": {"1-3": 3, "4-10": 8},
            "keyword_performance": {
                "AI": {"volume": 900, "position": 3},
                "machine learning": {"volume": 700, "position": 4}
            },
            "click_through_rates": {"1": 0.28, "2": 0.14},
            "search_intent": {"informational": 0.6, "commercial": 0.4},
            "regional_performance": {"US": {"traffic": 900}}
        }
    ]
    
    result = data_service._process_search_results(mock_results)
    
    # Verify structure
    assert isinstance(result, dict)
    assert "visibility_score" in result
    assert "ranking_distribution" in result
    assert "keyword_performance" in result
    assert "click_through_rates" in result
    assert "search_intent" in result
    assert "regional_performance" in result
    
    # Verify aggregation logic
    assert result["visibility_score"] == 150.0  # Sum of both scores
    assert result["ranking_distribution"]["1-3"] == 8  # Sum of 1-3 positions
    assert result["ranking_distribution"]["4-10"] == 18  # Sum of 4-10 positions
    
    # Verify keyword performance averaging
    ai_metrics = result["keyword_performance"]["AI"]
    assert ai_metrics["volume"] == 950.0  # Average of 1000 and 900
    assert ai_metrics["position"] == 2.5  # Average of 2 and 3

@pytest.mark.asyncio
async def test_error_handling(data_service):
    """Test error handling for invalid inputs"""
    # Test with None input
    with pytest.raises(Exception):
        await data_service.gather_comprehensive_data(None)
    
    # Test with missing required fields
    invalid_asset = {"id": "test"}
    with pytest.raises(Exception):
        await data_service.gather_comprehensive_data(invalid_asset)
    
    # Test with invalid market
    invalid_market_asset = {
        "id": "test",
        "market": "INVALID",
        "content": "test",
        "target_keywords": []
    }
    with pytest.raises(Exception):
        await data_service.gather_comprehensive_data(invalid_market_asset)
