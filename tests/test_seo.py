import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.models.seo import Subject, Subtopic, ContentAsset, OpportunityScore
from src.services.seo.semrush_service import SemrushService
from src.services.seo.serp_service import SerpService
from src.services.content.asset_tracker import ContentAssetTracker
from src.main import app
from src.database import get_db
from unittest.mock import Mock, patch
from src.services.seo.scoring_service import ScoringService
from unittest.mock import MagicMock
from unittest.mock import AsyncMock, create_autospec
import numpy as np

client = TestClient(app, raise_server_exceptions=False)

@pytest.fixture
def db_session():
    """Create a test database session"""
    # This would typically create a test database session
    # For now, we'll mock it
    return Mock(spec=Session)

@pytest.fixture
def semrush_service():
    """Create a mock SEMRush service"""
    return Mock(spec=SemrushService)

@pytest.fixture
def serp_service():
    """Create a mock SERP service"""
    return Mock(spec=SerpService)

@pytest.fixture
def content_tracker(semrush_service, serp_service):
    """Create a ContentAssetTracker with mock services"""
    return ContentAssetTracker(semrush_service, serp_service)

@pytest.fixture
def mock_semrush_service():
    return AsyncMock(spec=SemrushService)

@pytest.fixture
def mock_serp_service():
    return AsyncMock(spec=SerpService)

@pytest.fixture
def scoring_service(mock_semrush_service, mock_serp_service):
    return ScoringService(
        semrush_service=mock_semrush_service,
        serp_service=mock_serp_service
    )

@pytest.fixture
def sample_content_asset():
    return ContentAsset(
        url="https://example.com/content",
        topic="Office Leasing",
        style="Analysis",
        format="Article",
        social_engagement={
            "likes": 500,
            "shares": 250,
            "linkedin": 100
        }
    )

@pytest.fixture
def sample_subject():
    return Subject(
        name="Office Leasing",
        search_volume=10000,
        competition=0.5
    )

@pytest.fixture
def sample_subtopic():
    return Subtopic(
        name="Office Location Analysis",
        search_volume=1000,
        competition=0.3
    )

@pytest.mark.asyncio
async def test_create_subject(test_client, test_db):
    """Test creating a new subject"""
    # Arrange
    subject_data = {
        "name": "Test Subject",
        "market_scope": "global",
        "language": "en"
    }
    
    # Act
    response = test_client.post("/api/v1/seo/subjects/", json=subject_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == subject_data["name"]
    assert data["market_scope"] == subject_data["market_scope"]

@pytest.mark.asyncio
async def test_get_subtopics(test_client, test_subject, test_subtopic):
    """Test getting subtopics for a subject"""
    # Act
    response = test_client.get(f"/api/v1/seo/subjects/{test_subject.id}/subtopics/")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == test_subtopic.name

@pytest.mark.asyncio
async def test_analyze_subject(test_client, test_subject):
    """Test analyzing a subject with SEMRush"""
    # Arrange
    mock_keyword_data = [
        {"keyword": "Topic 1", "search_volume": 1000, "competition": 0.5},
        {"keyword": "Topic 2", "search_volume": 2000, "competition": 0.3}
    ]
    mock_serp_data = [
        {"url": "https://example.com/1", "position": 1},
        {"url": "https://example.com/2", "position": 2}
    ]
    
    with patch("src.services.seo.semrush_service.SemrushService.get_keywords") as mock_keywords:
        mock_keywords.return_value = mock_keyword_data
        with patch("src.services.seo.serp_service.SerpService.analyze_serp") as mock_serp:
            mock_serp.return_value = mock_serp_data
            
            # Act
            response = test_client.post(f"/api/v1/seo/subjects/{test_subject.id}/analyze/")
            
            # Assert
            assert response.status_code == 200
            assert response.json()["message"] == "Subject analyzed successfully"

@pytest.mark.asyncio
async def test_create_content_asset(test_client, test_subject):
    """Test creating a new content asset"""
    # Arrange
    asset_data = {
        "subject_id": test_subject.id,
        "url": "https://example.com/content",
        "topic": "Test Topic",
        "style": "blog",
        "format": "article"
    }
    
    # Act
    response = test_client.post("/api/v1/seo/content-assets/", json=asset_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == asset_data["url"]
    assert data["subject_id"] == test_subject.id

@pytest.mark.asyncio
async def test_get_content_metrics(test_client, test_content_asset):
    """Test getting metrics for a content asset"""
    # Arrange
    mock_domain_analytics = {
        "domain": "example.com",
        "traffic": 5000,
        "keywords": 100
    }
    mock_serp_data = {
        "position": 1,
        "url": "https://example.com/test"
    }
    
    with patch("src.services.seo.semrush_service.SemrushService.analyze_domain") as mock_domain:
        mock_domain.return_value = mock_domain_analytics
        with patch("src.services.seo.serp_service.SerpService.analyze_serp") as mock_serp:
            mock_serp.return_value = mock_serp_data
            
            # Act
            response = test_client.get(f"/api/v1/seo/content-assets/{test_content_asset.id}/metrics/")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "domain_analytics" in data
            assert "serp_data" in data

@pytest.mark.asyncio
async def test_get_competitor_content(test_client, test_subject):
    """Test getting competitor content analysis"""
    # Arrange
    mock_competitors = [
        {
            "url": "https://competitor1.com/content",
            "domain": "competitor1.com",
            "traffic": 5000,
            "keywords": ["kw1", "kw2"],
            "ranking": 1
        }
    ]
    
    with patch("src.services.content.asset_tracker.ContentAssetTracker.get_competitor_content") as mock_content:
        mock_content.return_value = mock_competitors
        
        # Act
        response = test_client.get(f"/api/v1/seo/subjects/{test_subject.id}/competitors/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(mock_competitors)
        assert data[0]["url"] == mock_competitors[0]["url"]

@pytest.mark.asyncio
async def test_calculate_likeability_index(scoring_service, sample_content_asset):
    # Mock SERP data
    scoring_service.serp.analyze_serp.return_value = {
        "position": 5,
        "visibility": 0.8
    }
    
    # Calculate expected scores
    ranking_score = 95  # 100 - position
    visibility_score = 80  # visibility * 100
    likes_score = 50  # (500/1000) * 100
    shares_score = 50  # (250/500) * 100
    linkedin_score = 50  # (100/200) * 100
    
    expected_score = (
        ranking_score * 0.40 +
        visibility_score * 0.20 +
        likes_score * 0.15 +
        shares_score * 0.15 +
        linkedin_score * 0.10
    )
    
    result = await scoring_service.calculate_likeability_index(sample_content_asset)
    assert abs(result - round(expected_score, 2)) < 0.01

@pytest.mark.asyncio
async def test_calculate_opportunity_index(scoring_service, sample_subject, sample_subtopic):
    # Mock keyword data
    scoring_service.semrush.get_keyword_data.return_value = {
        "search_volume": 1000,
        "engagement": 2.0,
        "competition": 0.3,
        "content_saturation": 0.4
    }
    
    result = await scoring_service.calculate_opportunity_index(sample_subject, sample_subtopic)
    
    # Verify result is within expected range
    assert 0 <= result <= 100
    
    # Verify higher values for better opportunities
    scoring_service.semrush.get_keyword_data.return_value = {
        "search_volume": 2000,
        "engagement": 3.0,
        "competition": 0.2,
        "content_saturation": 0.3
    }
    
    better_result = await scoring_service.calculate_opportunity_index(sample_subject, sample_subtopic)
    assert better_result > result

@pytest.mark.asyncio
async def test_calculate_niche_potential(scoring_service, sample_subject):
    # Mock market data
    scoring_service.semrush.analyze_topic.return_value = {
        "topics": [
            {"search_volume": 1000, "engagement": 2.0, "competition": 0.3},
            {"search_volume": 1500, "engagement": 2.5, "competition": 0.4}
        ]
    }
    
    scoring_service.semrush.get_competitors.return_value = ["comp1.com", "comp2.com"]
    
    result = await scoring_service.calculate_niche_potential(sample_subject)
    
    # Verify result is within expected range
    assert 0 <= result <= 100
    
    # Test with better niche potential
    scoring_service.semrush.analyze_topic.return_value = {
        "topics": [
            {"search_volume": 2000, "engagement": 3.0, "competition": 0.2},
            {"search_volume": 2500, "engagement": 3.5, "competition": 0.3}
        ]
    }
    
    better_result = await scoring_service.calculate_niche_potential(sample_subject)
    assert better_result > result

@pytest.mark.asyncio
async def test_segment_market(scoring_service, sample_subject):
    # Mock topic and competitor data
    scoring_service.semrush.analyze_topic.return_value = {
        "topics": [
            {
                "domain": "competitor.com",
                "topic": "Office Leasing",
                "search_volume": 1000,
                "social_signals": 500
            },
            {
                "domain": "gov.edu",
                "topic": "Office Regulations",
                "search_volume": 800,
                "social_signals": 300
            },
            {
                "domain": "blog.news.com",
                "topic": "Office Trends",
                "search_volume": 1200,
                "social_signals": 700
            }
        ]
    }
    
    scoring_service.semrush.get_competitors.return_value = ["competitor.com"]
    
    result = await scoring_service.segment_market(sample_subject)
    
    # Verify all required segments are present
    assert all(segment in result for segment in [
        "client_competitors",
        "other_competitors",
        "government_institutions",
        "publishers_independent"
    ])
    
    # Verify correct classification
    assert any(item["domain"] == "competitor.com" for item in result["client_competitors"])
    assert any(item["domain"] == "gov.edu" for item in result["government_institutions"])
    assert any(item["domain"] == "blog.news.com" for item in result["publishers_independent"])

@pytest.mark.asyncio
async def test_analyze_content_by_dimension(scoring_service):
    content_assets = [
        ContentAsset(
            url="https://example.com/1",
            topic="Location",
            style="Analysis",
            format="Article",
            social_engagement={"likes": 500, "shares": 250, "linkedin": 100}
        ),
        ContentAsset(
            url="https://example.com/2",
            topic="Cost",
            style="Guide",
            format="Video",
            social_engagement={"likes": 1000, "shares": 500, "linkedin": 200}
        )
    ]
    
    # Mock SERP data
    scoring_service.serp.analyze_serp.return_value = {
        "position": 5,
        "visibility": 0.8
    }
    
    # Test topic dimension
    topic_results = await scoring_service.analyze_content_by_dimension(content_assets, "topic")
    assert "Location" in topic_results
    assert "Cost" in topic_results
    assert all(key in topic_results["Location"] for key in ["average_score", "assets"])
    
    # Test style dimension
    style_results = await scoring_service.analyze_content_by_dimension(content_assets, "style")
    assert "Analysis" in style_results
    assert "Guide" in style_results
    
    # Test format dimension
    format_results = await scoring_service.analyze_content_by_dimension(content_assets, "format")
    assert "Article" in format_results
    assert "Video" in format_results
    
    # Verify scores are properly calculated and sorted
    for dimension_results in [topic_results, style_results, format_results]:
        for category in dimension_results.values():
            assert 0 <= category["average_score"] <= 100
            assert len(category["assets"]) > 0
            # Verify assets are sorted by score
            scores = [asset["score"] for asset in category["assets"]]
            assert scores == sorted(scores, reverse=True)

@pytest.mark.asyncio
async def test_edge_cases(scoring_service, sample_content_asset, sample_subject, sample_subtopic):
    # Test with zero search volume
    scoring_service.semrush.get_keyword_data.return_value = {
        "search_volume": 0,
        "engagement": 0,
        "competition": 0,
        "content_saturation": 0
    }
    
    result = await scoring_service.calculate_opportunity_index(sample_subject, sample_subtopic)
    assert result >= 0  # Should handle zero values gracefully
    
    # Test with missing social metrics
    sample_content_asset.social_engagement = {}
    scoring_service.serp.analyze_serp.return_value = {
        "position": 100,
        "visibility": 0
    }
    
    result = await scoring_service.calculate_likeability_index(sample_content_asset)
    assert result >= 0  # Should handle missing metrics gracefully
    
    # Test with invalid dimension
    with pytest.raises(ValueError):
        await scoring_service.analyze_content_by_dimension([sample_content_asset], "invalid_dimension")
