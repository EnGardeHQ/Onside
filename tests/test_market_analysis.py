"""
Tests for the Market Analysis Service
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from src.services.analytics.market_analysis_service import MarketAnalysisService
from src.models.market import (
    Competitor,
    CompetitorContent,
    CompetitorMetrics,
    MarketTag
)
from unittest.mock import Mock, AsyncMock, call

@pytest.fixture
def market_analysis_service():
    """Create a market analysis service instance"""
    return MarketAnalysisService(
        min_confidence_score=0.7,
        market_share_window_days=90,
        content_freshness_days=30,
        min_data_points=3
    )

@pytest.fixture
async def sample_competitor(test_db: AsyncSession, request):
    """Create a sample competitor with a unique domain"""
    # Use test node ID to create unique domain
    unique_id = request.node.nodeid.split('::')[-1]
    domain = f"testcompetitor-{unique_id}.com"
    
    competitor = Competitor(
        name=f"Test Competitor {unique_id}",
        domain=domain,
        description="A test competitor",
        meta_data={"industry": "tech"}
    )
    test_db.add(competitor)
    await test_db.commit()
    await test_db.refresh(competitor)
    return competitor

@pytest.fixture
async def sample_metrics(test_db: AsyncSession, sample_competitor: Competitor):
    """Create sample competitor metrics"""
    base_date = datetime.now() - timedelta(days=30)
    metrics = []

    for i in range(5):
        metric = CompetitorMetrics(
            competitor_id=sample_competitor.id,
            metric_date=base_date + timedelta(days=i*7),
            start_date=base_date + timedelta(days=i*7),
            end_date=base_date + timedelta(days=(i+1)*7),
            metric_type="revenue",
            value=1000 + (i * 100),
            confidence_score=0.8,
            source="test",
            meta_data={}
        )
        metrics.append(metric)
        test_db.add(metric)

    await test_db.commit()
    return metrics

@pytest.fixture
async def sample_content(test_db: AsyncSession, sample_competitor: Competitor):
    """Create sample competitor content"""
    content_types = ["blog", "whitepaper", "case_study"]
    content_items = []
    
    for i, content_type in enumerate(content_types):
        content = CompetitorContent(
            competitor_id=sample_competitor.id,
            url=f"https://testcompetitor.com/content/{i}",
            title=f"Test Content {i}",
            content_type=content_type,
            publish_date=datetime.now() - timedelta(days=i),
            engagement_metrics={"views": 100, "shares": 10},
            content_metrics={"word_count": 1000},
            meta_data={}
        )
        content_items.append(content)
        test_db.add(content)
    
    await test_db.commit()
    return content_items

@pytest.mark.asyncio
async def test_add_competitor(
    test_db: AsyncSession,
    market_analysis_service: MarketAnalysisService
):
    """Test adding a new competitor"""
    competitor = await market_analysis_service.add_competitor(
        session=test_db,
        name="New Competitor",
        domain="newcompetitor.com",
        description="A new competitor",
        tags=["tech", "startup"],
        meta_data={"industry": "tech"}
    )
    
    assert competitor is not None
    assert competitor.name == "New Competitor"
    assert competitor.domain == "newcompetitor.com"

@pytest.mark.asyncio
async def test_add_duplicate_competitor(
    test_db: AsyncSession,
    market_analysis_service: MarketAnalysisService,
    sample_competitor: Competitor
):
    """Test adding a duplicate competitor"""
    # Try to add competitor with same domain
    duplicate = await market_analysis_service.add_competitor(
        session=test_db,
        name=sample_competitor.name,
        domain=sample_competitor.domain,
        description="Duplicate competitor",
        meta_data={"industry": "tech"}
    )
    
    assert duplicate is None

@pytest.mark.asyncio
async def test_update_competitor_metrics(market_analysis_service, test_db, sample_competitor):
    """Test updating competitor metrics"""
    now = datetime.now()
    result = await market_analysis_service.update_competitor_metrics(
        test_db,
        competitor_id=sample_competitor.id,
        metric_type="revenue",
        value=1000.0,
        confidence_score=0.9,
        source="test",
        meta_data={"start_date": now.isoformat()}  # Add start_date in meta_data
    )
    assert result is True
    
    # Verify metrics were added
    result = await test_db.execute(
        select(CompetitorMetrics)
        .where(CompetitorMetrics.competitor_id == sample_competitor.id)
    )
    metric = result.scalar_one()
    assert metric.value == 1000.0
    assert metric.confidence_score == 0.9

@pytest.mark.asyncio
async def test_add_competitor_content(
    test_db: AsyncSession,
    market_analysis_service: MarketAnalysisService,
    sample_competitor: Competitor
):
    """Test adding competitor content"""
    content = await market_analysis_service.add_competitor_content(
        session=test_db,
        competitor_id=sample_competitor.id,
        url="https://testcompetitor.com/new-content",
        title="New Content",
        content_type="blog",
        engagement_metrics={"views": 100},
        content_metrics={"word_count": 1000},
        meta_data={"author": "Test Author"}
    )
    
    assert content is not None
    assert content.title == "New Content"
    assert content.content_type == "blog"
    assert content.engagement_metrics["views"] == 100

@pytest.mark.asyncio
async def test_get_market_trends(
    test_db: AsyncSession,
    market_analysis_service: MarketAnalysisService,
    sample_metrics: list
):
    """Test getting market trends"""
    trends = await market_analysis_service.get_market_trends(
        session=test_db,
        metric_type="revenue",
        days=30
    )
    
    assert len(trends) > 0
    trend = trends[0]
    assert "competitor_id" in trend
    assert "trend_direction" in trend
    assert "change_percent" in trend
    assert trend["trend_direction"] in ["up", "down"]

@pytest.mark.asyncio
async def test_get_content_gaps(
    test_db: AsyncSession,
    market_analysis_service: MarketAnalysisService,
    sample_content: list
):
    """Test getting content gaps analysis"""
    gaps = await market_analysis_service.get_content_gaps(
        session=test_db,
        days=30
    )
    
    assert len(gaps) > 0
    for gap in gaps:
        assert "content_type" in gap
        assert "count" in gap
        assert "percentage" in gap
        assert "is_gap" in gap

@pytest.mark.asyncio
async def test_market_share_calculation(market_analysis_service, test_db):
    """Test market share calculation with confidence weighting"""
    # Clean up any existing data
    from sqlalchemy import text
    await test_db.execute(text("DELETE FROM competitor_metrics"))
    await test_db.execute(text("DELETE FROM competitors"))
    await test_db.commit()

    now = datetime.now()

    # Create competitors
    competitor1 = await market_analysis_service.add_competitor(
        test_db,
        name="Competitor 1",
        domain="competitor1.com"
    )

    competitor2 = await market_analysis_service.add_competitor(
        test_db,
        name="Competitor 2",
        domain="competitor2.com"
    )

    # Add metrics with start_date
    await market_analysis_service.update_competitor_metrics(
        test_db,
        competitor_id=competitor1.id,
        metric_type="revenue",
        value=1000.0,
        confidence_score=0.9,
        source="test",
        meta_data={"start_date": now.isoformat()}
    )

    await market_analysis_service.update_competitor_metrics(
        test_db,
        competitor_id=competitor2.id,
        metric_type="revenue",
        value=2000.0,
        confidence_score=0.9,
        source="test",
        meta_data={"start_date": now.isoformat()}
    )

    # Update market shares
    await market_analysis_service._update_market_shares(test_db)

    # Verify market shares
    result = await test_db.execute(
        select(Competitor.market_share).where(Competitor.id == competitor1.id)
    )
    market_share = result.scalar_one()
    assert market_share == pytest.approx(33.33, rel=0.01)  # (1000 * 0.9) / ((1000 * 0.9) + (2000 * 0.9)) * 100

@pytest.mark.asyncio
async def test_weighted_market_trends(market_analysis_service, test_db):
    """Test weighted market trend calculations"""
    now = datetime.now()
    metrics = [
        CompetitorMetrics(
            competitor_id=1,
            metric_type='revenue',
            metric_date=now - timedelta(days=i),
            value=1000 + i * 100,
            confidence_score=0.8 + 0.02 * i
        )
        for i in range(10)
    ]
    
    trends = market_analysis_service._calculate_market_trends(metrics)
    assert len(trends) > 0
    assert 'weighted_avg' in trends[0]
    assert 'velocity' in trends[0]
    assert 'acceleration' in trends[0]
    assert 'trend_score' in trends[0]
    assert trends[0]['trend_score'] > 0

@pytest.mark.asyncio
async def test_engagement_weighted_content_gaps(market_analysis_service, test_db):
    """Test content gap analysis with engagement weighting"""
    now = datetime.now()
    content_items = [
        CompetitorContent(
            competitor_id=1,
            content_type='blog',
            url=f'http://example.com/blog/{i}',
            title=f'Blog Post {i}',
            publish_date=now - timedelta(days=i),
            engagement_metrics={
                'views': 100 + i * 10,
                'shares': 20 + i * 2,
                'comments': 10 + i,
                'likes': 50 + i * 5
            }
        )
        for i in range(5)
    ]
    
    gaps = market_analysis_service._analyze_content_gaps(content_items)
    assert len(gaps) > 0
    assert 'engagement_velocity' in gaps[0]
    assert 'weighted_gap_score' in gaps[0]
    
    # Test that high engagement velocity affects gap score
    high_engagement_content = CompetitorContent(
        competitor_id=1,
        content_type='video',
        url='http://example.com/video/1',
        title='Viral Video',
        publish_date=now - timedelta(days=1),
        engagement_metrics={
            'views': 10000,
            'shares': 1000,
            'comments': 500,
            'likes': 2000
        }
    )
    
    gaps_with_viral = market_analysis_service._analyze_content_gaps([high_engagement_content])
    assert len(gaps_with_viral) > 0
    assert gaps_with_viral[0]['engagement_velocity'] > gaps[0]['engagement_velocity']

@pytest.mark.asyncio
async def test_confidence_weighted_market_shares(market_analysis_service, test_db):
    """Test market share calculations with confidence weighting"""
    now = datetime.now()

    # Create test metrics with varying confidence scores
    metrics = [
        CompetitorMetrics(
            competitor_id=1,
            metric_type='revenue',
            metric_date=now - timedelta(days=i),
            start_date=now - timedelta(days=i),
            end_date=now - timedelta(days=i-1),
            value=1000,
            confidence_score=0.9,
            source='test'
        )
        for i in range(5)
    ] + [
        CompetitorMetrics(
            competitor_id=2,
            metric_type='revenue',
            metric_date=now - timedelta(days=i),
            start_date=now - timedelta(days=i),
            end_date=now - timedelta(days=i-1),
            value=1000,
            confidence_score=0.7,
            source='test'
        )
        for i in range(5)
    ]

    # Add metrics to database
    for metric in metrics:
        test_db.add(metric)
    await test_db.commit()

    # Calculate weighted market shares
    market_shares = await market_analysis_service.get_market_shares(test_db)

    # Verify that competitor with higher confidence score has higher market share
    assert len(market_shares) == 2
    assert market_shares[0]['confidence_score'] == 0.9
    assert market_shares[1]['confidence_score'] == 0.7
    assert market_shares[0]['market_share'] > market_shares[1]['market_share']

@pytest.mark.asyncio
async def test_custom_weights(market_analysis_service, test_db):
    """Test market analysis with custom weights"""
    custom_trend_weights = {
        'revenue': 3.0,
        'market_share': 2.0,
        'traffic': 1.5,
        'engagement': 1.0
    }
    
    custom_engagement_weights = {
        'shares': 4.0,
        'comments': 3.0,
        'likes': 2.0,
        'views': 1.0
    }
    
    service = MarketAnalysisService(
        trend_weights=custom_trend_weights,
        engagement_weights=custom_engagement_weights
    )
    
    # Test that custom weights are applied
    assert service.trend_weights == custom_trend_weights
    assert service.engagement_weights == custom_engagement_weights
    
    # Create test metrics
    now = datetime.now()
    metrics = [
        CompetitorMetrics(
            competitor_id=1,
            metric_type='revenue',
            metric_date=now - timedelta(days=i),
            value=1000,
            confidence_score=0.9
        )
        for i in range(5)
    ]
    
    # Calculate trends with custom weights
    trends = service._calculate_market_trends(metrics)
    assert len(trends) > 0
    assert trends[0]['trend_score'] > 0
