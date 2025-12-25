"""
Tests for the Temporal Analysis Service
"""
import pytest
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import Mock, AsyncMock, patch
from src.services.analytics.temporal_analysis_service import TemporalAnalysisService
from src.models.content import Content, ContentEngagementHistory
from src.models.trend import TrendAnalysis

@pytest.fixture
def temporal_service():
    return TemporalAnalysisService()

@pytest.fixture
async def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    session.add = Mock()  # add is synchronous
    return session

@pytest.fixture
def sample_content():
    return Content(
        id=1,
        user_id=1,  # Add required user_id
        title="Test Content",
        content_text="Test Content Text",
        content_type="article",  # Add required content_type
        content_metadata={
            "type": "article",
            "url": "https://test.com/article",
            "source": "test_source"
        },
        created_at=datetime.now() - timedelta(days=5)
    )

@pytest.fixture
def sample_engagement_history():
    now = datetime.now()
    return [
        ContentEngagementHistory(
            id=i,
            content_id=1,
            timestamp=now - timedelta(days=i),
            views=100 + i * 10,
            shares=10 + i,
            comments=5 + i,
            likes=20 + i * 2
        )
        for i in range(7)
    ]

@pytest.mark.asyncio
async def test_calculate_content_decay(temporal_service):
    now = datetime.now()
    
    # Test recent content
    recent_date = now - timedelta(days=30)
    decay_score = await temporal_service.calculate_content_decay(recent_date)
    assert 0.9 <= decay_score <= 1.0
    
    # Test old content
    old_date = now - timedelta(days=400)
    decay_score = await temporal_service.calculate_content_decay(old_date)
    assert decay_score == 0.0
    
    # Test very recent content
    very_recent_date = now - timedelta(days=1)
    decay_score = await temporal_service.calculate_content_decay(very_recent_date)
    assert decay_score > 0.95

@pytest.mark.asyncio
async def test_update_content_engagement(temporal_service, mock_db_session):
    # Test successful update
    result = await temporal_service.update_content_engagement(
        mock_db_session,
        content_id=1,
        views=100,
        shares=10,
        comments=5,
        likes=20
    )
    assert result is True
    mock_db_session.add.assert_called_once()
    assert mock_db_session.commit.call_count == 1
    
    # Test failed update
    mock_db_session.commit.side_effect = Exception("Database error")
    result = await temporal_service.update_content_engagement(
        mock_db_session,
        content_id=1
    )
    assert result is False
    assert mock_db_session.rollback.call_count == 1

@pytest.mark.asyncio
async def test_get_engagement_history(temporal_service, mock_db_session, sample_engagement_history):
    # Mock the database query result
    mock_result = AsyncMock()
    mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=sample_engagement_history)))
    mock_db_session.execute.return_value = mock_result
    
    # Test retrieving all history
    history = await temporal_service.get_engagement_history(mock_db_session, content_id=1)
    assert len(history) == 7
    assert all(isinstance(h, ContentEngagementHistory) for h in history)
    
    # Test retrieving history with day limit
    history = await temporal_service.get_engagement_history(mock_db_session, content_id=1, days=3)
    assert mock_db_session.execute.call_count == 2

@pytest.mark.asyncio
async def test_analyze_content_trends(temporal_service, mock_db_session, sample_engagement_history, sample_content):
    # Mock get_engagement_history and content query
    with patch.object(
        temporal_service,
        'get_engagement_history',
        return_value=sample_engagement_history
    ):
        # Mock content query
        mock_content_result = AsyncMock()
        mock_content_result.scalar_one_or_none = Mock(return_value=sample_content)
        mock_db_session.execute.return_value = mock_content_result

        trends = await temporal_service.analyze_content_trends(mock_db_session, content_id=1)
        
        assert trends is not None
        assert all(metric in trends for metric in ['views', 'shares', 'comments', 'likes'])
        assert all(
            all(key in metric for key in ['slope', 'confidence'])
            for metric in trends.values()
        )
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.call_count == 1

@pytest.mark.asyncio
async def test_calculate_trend(temporal_service):
    # Test with increasing trend
    timestamps = np.array([1, 2, 3, 4, 5])
    values = np.array([10, 20, 30, 40, 50])
    slope, score = await temporal_service._calculate_trend(timestamps, values)
    assert slope > 0
    assert score > 0.9  # Strong linear correlation
    
    # Test with decreasing trend
    values = np.array([50, 40, 30, 20, 10])
    slope, score = await temporal_service._calculate_trend(timestamps, values)
    assert slope < 0
    assert score > 0.9  # Strong linear correlation

@pytest.mark.asyncio
async def test_get_trending_content(temporal_service, mock_db_session, sample_content):
    # Mock database query result
    trend_analysis = TrendAnalysis(
        trend_type="engagement",
        timestamp=datetime.now(),
        trend_data={
            'views': {'slope': 0.5, 'confidence': 0.9},
            'shares': {'slope': 0.3, 'confidence': 0.8}
        },
        trend_score=0.9
    )
    trend_analysis.contents.append(sample_content)

    mock_result = AsyncMock()
    mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[trend_analysis])))
    mock_db_session.execute.return_value = mock_result

    # Test get_trending_content
    trending = await temporal_service.get_trending_content(mock_db_session)
    assert len(trending) == 1
    assert trending[0]['trend_data']['views']['slope'] == 0.5

@pytest.mark.asyncio
async def test_error_handling(temporal_service, mock_db_session):
    # Test error handling in update_content_engagement
    mock_db_session.commit.side_effect = Exception("Test error")
    result = await temporal_service.update_content_engagement(
        mock_db_session,
        content_id=1
    )
    assert result is False
    assert mock_db_session.rollback.call_count == 1

@pytest.mark.asyncio
async def test_detect_realtime_trends(temporal_service, mock_db_session):
    # Create test data
    now = datetime.now()
    engagements = [
        ContentEngagementHistory(
            content_id=1,
            timestamp=now - timedelta(minutes=i * 5),
            views=100 + i * 20,
            shares=10 + i * 2,
            comments=5 + i,
            likes=20 + i * 3
        )
        for i in range(5)
    ]
    
    # Mock database query
    mock_result = AsyncMock()
    mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=engagements)))
    mock_db_session.execute.return_value = mock_result
    
    # Test without filters
    trends = await temporal_service.detect_realtime_trends(
        mock_db_session,
        time_window_minutes=30,
        min_engagement_threshold=10
    )
    
    assert len(trends) > 0
    assert all(key in trends[0] for key in [
        'content_id', 'total_engagement', 'velocity', 'acceleration', 'trending_score'
    ])
    assert trends[0]['trending_score'] > 0
    
    # Test with filters
    content_filters = {'title': 'Test Content'}  # Use an existing field
    trends = await temporal_service.detect_realtime_trends(
        mock_db_session,
        content_filters=content_filters
    )
    assert len(trends) > 0

@pytest.mark.asyncio
async def test_filter_content_by_performance(temporal_service, mock_db_session, sample_content, sample_engagement_history):
    # Mock content query
    mock_content_result = AsyncMock()
    mock_content_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[sample_content])))
    mock_db_session.execute.return_value = mock_content_result
    
    # Mock engagement history
    with patch.object(
        temporal_service,
        'get_engagement_history',
        return_value=sample_engagement_history
    ):
        # Test with performance metrics
        performance_metrics = {
            'view_weight': 1.0,
            'share_weight': 3.0,
            'comment_weight': 2.0,
            'like_weight': 1.0
        }
        
        filtered_content = await temporal_service.filter_content_by_performance(
            mock_db_session,
            performance_metrics=performance_metrics,
            content_filters={'title': 'Test Content'}  # Use an existing field from sample_content
        )
        
        assert len(filtered_content) > 0
        assert all(key in filtered_content[0] for key in [
            'content_id', 'title', 'score', 'metrics', 'decay_factor'
        ])
        assert filtered_content[0]['score'] > 0
        assert all(metric in filtered_content[0]['metrics'] for metric in [
            'views', 'shares', 'comments', 'likes'
        ])
