import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from src.services.ai.audience_intelligence import (
    AudienceIntelligenceService,
    AudienceSegment,
    EngagementMetrics,
    DemographicProfile,
    InterestProfile,
    BehaviorPattern,
    AudienceIntelligenceError
)
from tests.utils import MockUser, MockContent, get_mock_db_session, MockResult

@pytest.fixture
def mock_users():
    return [
        MockUser(
            id=1,
            email="user1@example.com",
            metadata={
                'age': 25,
                'location': 'San Francisco',
                'interests': ['technology', 'ai'],
                'engagement_score': 0.8
            }
        ),
        MockUser(
            id=2,
            email="user2@example.com",
            metadata={
                'age': 35,
                'location': 'New York',
                'interests': ['business', 'marketing'],
                'engagement_score': 0.6
            }
        )
    ]

@pytest.fixture
def mock_content():
    return [
        MockContent(
            id=1,
            title="Test Content 1",
            text="Test content text 1",
            user_id=1,
            metadata={
                'engagement_metrics': {
                    'views': 1000,
                    'likes': 50,
                    'shares': 20,
                    'comments': 10
                }
            }
        ),
        MockContent(
            id=2,
            title="Test Content 2",
            text="Test content text 2",
            user_id=2,
            metadata={
                'engagement_metrics': {
                    'views': 500,
                    'likes': 25,
                    'shares': 10,
                    'comments': 5
                }
            }
        )
    ]

@pytest.fixture
def audience_service():
    with patch('src.services.ai.audience_intelligence.get_db_session', return_value=get_mock_db_session()):
        service = AudienceIntelligenceService()
        return service

@pytest.mark.asyncio
async def test_analyze_audience_demographics(audience_service, mock_users):
    """Test audience demographics analysis"""
    mock_users[0].metadata = {
        'age': 25,
        'location': 'San Francisco'
    }
    mock_users[1].metadata = {
        'age': 35,
        'location': 'New York'
    }
    
    with patch('src.services.ai.audience_intelligence.get_db_session') as mock_get_session:
        mock_session = get_mock_db_session()
        mock_session.execute_result = MockResult(mock_users)
        mock_get_session.return_value = mock_session
        
        demographics = await audience_service.analyze_audience_demographics()
        
        assert demographics.metrics is not None
        assert 'age_distribution' in demographics.metrics
        assert 'location_distribution' in demographics.metrics
        assert len(demographics.segments) == 2
        assert len(demographics.insights) > 0
        assert demographics.updated_at is not None

@pytest.mark.asyncio
async def test_analyze_audience_interests(audience_service, mock_users):
    """Test audience interests analysis"""
    mock_users[0].metadata = {
        'interests': ['technology', 'ai', 'business']
    }
    mock_users[1].metadata = {
        'interests': ['marketing', 'technology', 'finance']
    }
    
    with patch('src.services.ai.audience_intelligence.get_db_session') as mock_get_session:
        mock_session = get_mock_db_session()
        mock_session.execute_result = MockResult(mock_users)
        mock_get_session.return_value = mock_session
        
        interests = await audience_service.analyze_audience_interests()
        
        assert interests.top_interests is not None
        assert len(interests.interest_clusters) > 0
        assert interests.interest_scores is not None
        assert len(interests.trending_topics) > 0
        assert interests.updated_at is not None

@pytest.mark.asyncio
async def test_analyze_engagement_patterns(audience_service, mock_content):
    """Test engagement patterns analysis"""
    mock_content[0].metadata = {
        'engagement_metrics': {
            'views': 1000,
            'likes': 50,
            'shares': 20
        }
    }
    mock_content[1].metadata = {
        'engagement_metrics': {
            'views': 500,
            'likes': 25,
            'shares': 10
        }
    }
    
    with patch('src.services.ai.audience_intelligence.get_db_session') as mock_get_session:
        mock_session = get_mock_db_session()
        mock_session.execute_result = MockResult(mock_content)
        mock_get_session.return_value = mock_session
        
        patterns = await audience_service.analyze_engagement_patterns()
        
        assert patterns.patterns is not None
        assert len(patterns.patterns) == 2
        assert patterns.metrics is not None
        assert 'avg_views' in patterns.metrics
        assert 'avg_likes' in patterns.metrics
        assert 'avg_shares' in patterns.metrics
        assert len(patterns.insights) > 0
        assert patterns.updated_at is not None

@pytest.mark.asyncio
async def test_get_audience_segments(audience_service, mock_users, mock_content):
    """Test audience segmentation"""
    mock_users[0].metadata = {
        'age': 25,
        'location': 'San Francisco',
        'interests': ['technology', 'ai'],
        'engagement_score': 0.8
    }
    mock_users[1].metadata = {
        'age': 35,
        'location': 'New York',
        'interests': ['business', 'marketing'],
        'engagement_score': 0.6
    }
    
    with patch('src.services.ai.audience_intelligence.get_db_session') as mock_get_session:
        mock_session = get_mock_db_session()
        mock_session.execute_result = MockResult(mock_users)
        mock_get_session.return_value = mock_session
        
        segments = await audience_service.get_audience_segments()
        assert len(segments) > 0
        assert all(isinstance(segment, dict) for segment in segments)
        assert all('demographics' in segment for segment in segments)
        assert all('interests' in segment for segment in segments)
        assert all('engagement_level' in segment for segment in segments)

@pytest.mark.asyncio
async def test_get_engagement_metrics(audience_service, mock_content):
    """Test engagement metrics calculation"""
    with patch('src.services.ai.audience_intelligence.get_db_session') as mock_get_session:
        mock_session = get_mock_db_session()
        mock_session.execute_result = MockResult(mock_content)
        mock_get_session.return_value = mock_session
        
        metrics = await audience_service.get_engagement_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) == 2
        assert all(isinstance(metric, EngagementMetrics) for metric in metrics)
        assert all(hasattr(metric, 'views') for metric in metrics)
        assert all(hasattr(metric, 'likes') for metric in metrics)
        assert all(hasattr(metric, 'shares') for metric in metrics)

@pytest.mark.asyncio
async def test_get_audience_recommendations(audience_service, mock_users):
    """Test audience recommendations"""
    mock_users[0].metadata = {
        'interests': ['technology', 'ai'],
        'engagement_score': 0.8
    }
    mock_users[1].metadata = {
        'interests': ['business', 'marketing'],
        'engagement_score': 0.7
    }
    
    with patch('src.services.ai.audience_intelligence.get_db_session') as mock_get_session:
        mock_session = get_mock_db_session()
        mock_session.execute_result = MockResult(mock_users)
        mock_get_session.return_value = mock_session
        
        recommendations = await audience_service.get_audience_recommendations()
        assert len(recommendations) > 0
        assert all(isinstance(rec, dict) for rec in recommendations)
        assert all('interests' in rec for rec in recommendations)
        assert all('recommendation' in rec for rec in recommendations)

@pytest.mark.asyncio
async def test_empty_data_handling(audience_service):
    """Test handling of empty data"""
    with patch('src.services.ai.audience_intelligence.get_db_session') as mock_get_session:
        mock_session = get_mock_db_session()
        mock_session.execute_result = MockResult([])
        mock_get_session.return_value = mock_session
        
        demographics = await audience_service.analyze_audience_demographics()
        assert demographics.metrics == {}
        assert demographics.segments == []
        assert demographics.insights == []
        assert demographics.updated_at is not None
        
        interests = await audience_service.analyze_audience_interests()
        assert interests.top_interests == []
        assert interests.interest_clusters == []
        assert interests.interest_scores == {}
        assert interests.trending_topics == []
        assert interests.updated_at is not None
        
        patterns = await audience_service.analyze_engagement_patterns()
        assert patterns.patterns == []
        assert patterns.metrics == {}
        assert patterns.insights == []
        assert patterns.updated_at is not None
        
        metrics = await audience_service.get_engagement_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) == 0

@pytest.mark.asyncio
async def test_error_handling(audience_service):
    """Test error handling in audience intelligence service"""
    with patch('src.services.ai.audience_intelligence.get_db_session') as mock_get_session:
        mock_session = get_mock_db_session()
        mock_session.execute_result = Exception("Database error")
        mock_get_session.return_value = mock_session
        
        with pytest.raises(AudienceIntelligenceError) as exc_info:
            await audience_service.analyze_audience_demographics()
        assert "Error analyzing audience demographics" in str(exc_info.value)
        
        with pytest.raises(AudienceIntelligenceError) as exc_info:
            await audience_service.analyze_audience_interests()
        assert "Error analyzing audience interests" in str(exc_info.value)
        
        with pytest.raises(AudienceIntelligenceError) as exc_info:
            await audience_service.analyze_engagement_patterns()
        assert "Error analyzing engagement patterns" in str(exc_info.value)
        
        with pytest.raises(AudienceIntelligenceError) as exc_info:
            await audience_service.get_engagement_metrics()
        assert "Error getting engagement metrics" in str(exc_info.value)
