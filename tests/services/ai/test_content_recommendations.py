import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from src.services.ai.content_recommendations import (
    ContentRecommendationService,
    RecommendationType,
    RecommendationScore,
    ContentSimilarity
)
from tests.utils import MockContent, get_mock_db_session, MockResult

@pytest.fixture
def mock_content():
    return [
        MockContent(
            id=1,
            title="Test Content",
            text="This is test content for recommendations",
            user_id=1,
            metadata={
                "category": "technology",
                "tags": ["ai", "machine learning"],
                "engagement_score": 0.8
            }
        )
    ]

@pytest.fixture
def recommendation_service():
    with patch('src.services.ai.content_recommendations.get_db_session', return_value=get_mock_db_session()):
        service = ContentRecommendationService()
        return service

@pytest.mark.asyncio
async def test_get_similar_content(recommendation_service, mock_content):
    """Test getting similar content based on content similarity"""
    similar_content = [
        MockContent(
            id=2,
            title="Similar Content 1",
            text="Related content about AI",
            user_id=1,
            metadata={"category": "technology", "tags": ["ai"]}
        ),
        MockContent(
            id=3,
            title="Similar Content 2",
            text="Another ML article",
            user_id=1,
            metadata={"category": "technology", "tags": ["machine learning"]}
        )
    ]
    
    with patch('src.services.ai.content_recommendations.get_db_session') as mock_get_session:
        mock_session = get_mock_db_session()
        mock_session.execute_result = MockResult(similar_content)
        mock_get_session.return_value = mock_session
        
        results = await recommendation_service.get_similar_content(mock_content[0].id)
        
        assert len(results) > 0
        assert all(isinstance(r, ContentSimilarity) for r in results)
        assert all(r.score >= 0 and r.score <= 1 for r in results)

@pytest.mark.asyncio
async def test_get_personalized_recommendations(recommendation_service):
    """Test getting personalized recommendations for a user"""
    recommended_content = [
        MockContent(
            id=1,
            title="Recommended Content 1",
            text="Content based on user preferences",
            user_id=2,
            metadata={"category": "technology"}
        ),
        MockContent(
            id=2,
            title="Recommended Content 2",
            text="More personalized content",
            user_id=2,
            metadata={"category": "science"}
        )
    ]
    
    with patch('src.services.ai.content_recommendations.get_db_session') as mock_get_session:
        mock_session = get_mock_db_session()
        mock_session.execute_result = MockResult(recommended_content)
        mock_get_session.return_value = mock_session
        
        results = await recommendation_service.get_personalized_recommendations(1)
        
        assert len(results) > 0
        assert all(isinstance(r, RecommendationScore) for r in results)
        assert all(r.score >= 0 and r.score <= 1 for r in results)

@pytest.mark.asyncio
async def test_get_trending_content(recommendation_service):
    """Test getting trending content"""
    trending_content = [
        MockContent(
            id=1,
            title="Trending Content 1",
            text="Popular content",
            user_id=1,
            metadata={"engagement_score": 0.9}
        ),
        MockContent(
            id=2,
            title="Trending Content 2",
            text="Viral content",
            user_id=2,
            metadata={"engagement_score": 0.85}
        )
    ]
    
    with patch('src.services.ai.content_recommendations.get_db_session') as mock_get_session:
        mock_session = get_mock_db_session()
        mock_session.execute_result = MockResult(trending_content)
        mock_get_session.return_value = mock_session
        
        results = await recommendation_service.get_trending_content()
        
        assert len(results) > 0
        assert all(isinstance(r, RecommendationScore) for r in results)
        assert all(r.score >= 0.8 for r in results)
        assert all(r.confidence > 0 for r in results)

@pytest.mark.asyncio
async def test_get_recommendations_by_type(recommendation_service):
    """Test getting recommendations by specific type"""
    content_items = [
        MockContent(
            id=1,
            title="Content 1",
            text="Test content",
            user_id=1,
            metadata={"category": "technology"}
        ),
        MockContent(
            id=2,
            title="Content 2",
            text="More test content",
            user_id=2,
            metadata={"category": "science"}
        )
    ]
    
    with patch('src.services.ai.content_recommendations.get_db_session') as mock_get_session:
        mock_session = get_mock_db_session()
        mock_session.execute_result = MockResult(content_items)
        mock_get_session.return_value = mock_session
        
        for rec_type in RecommendationType:
            results = await recommendation_service.get_recommendations_by_type(
                user_id=1,
                recommendation_type=rec_type
            )
            
            assert len(results) > 0
            assert all(isinstance(r, (RecommendationScore, ContentSimilarity, MockContent)) for r in results)

@pytest.mark.asyncio
async def test_get_recommendations_empty_results(recommendation_service):
    """Test handling of empty recommendation results"""
    with patch('src.services.ai.content_recommendations.get_db_session') as mock_get_session:
        mock_session = get_mock_db_session()
        mock_session.execute_result = MockResult([])
        mock_get_session.return_value = mock_session
        
        results = await recommendation_service.get_trending_content()
        assert len(results) == 0
        
        results = await recommendation_service.get_personalized_recommendations(user_id=1)
        assert len(results) == 0

@pytest.mark.asyncio
async def test_invalid_recommendation_parameters(recommendation_service):
    """Test handling of invalid parameters"""
    with pytest.raises(ValueError):
        await recommendation_service.get_similar_content(content_id=-1)
    
    with pytest.raises(ValueError):
        await recommendation_service.get_personalized_recommendations(user_id=-1)
    
    with pytest.raises(ValueError):
        await recommendation_service.get_recommendations_by_type(
            user_id=-1,
            recommendation_type=RecommendationType.SIMILAR
        )
