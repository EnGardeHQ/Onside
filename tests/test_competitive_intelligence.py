import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.services.analytics.competitive_intelligence_service import CompetitiveIntelligenceService
from src.models.market import Competitor, CompetitorMetrics

@pytest.mark.asyncio
async def test_track_competitor_mentions(
    test_db: AsyncSession,
    competitive_intelligence_service: CompetitiveIntelligenceService,
    sample_competitor: Competitor,
    mock_meltwater_client
):
    """Test tracking competitor mentions"""
    # Replace the service's Meltwater client with our mock
    competitive_intelligence_service.meltwater_client = mock_meltwater_client
    
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    # Track mentions
    analysis = await competitive_intelligence_service.track_competitor_mentions(
        test_db,
        sample_competitor.id,
        start_date,
        end_date
    )
    
    # Verify analysis results
    assert analysis["total_mentions"] == 2
    assert 0.6 <= analysis["sentiment_score"] <= 0.8
    assert analysis["engagement_rate"] > 0
    assert "sources" in analysis["details"]
    assert "topics" in analysis["details"]
    
    # Verify metrics were stored
    result = await test_db.execute(
        select(CompetitorMetrics).where(
            CompetitorMetrics.competitor_id == sample_competitor.id
        )
    )
    metrics = result.scalars().all()
    assert len(metrics) > 0
    assert metrics[-1].mentions_count == 2

@pytest.mark.asyncio
async def test_get_competitor_insights(
    test_db: AsyncSession,
    competitive_intelligence_service: CompetitiveIntelligenceService,
    sample_competitor: Competitor,
    sample_competitor_metrics
):
    """Test getting competitor insights"""
    insights = await competitive_intelligence_service.get_competitor_insights(
        test_db,
        sample_competitor.id
    )
    
    # Verify insight structure
    assert "mention_trend" in insights
    assert "sentiment_analysis" in insights
    assert "key_topics" in insights
    assert "market_position" in insights
    
    # Verify trend calculations
    assert "trend" in insights["mention_trend"]
    assert "confidence" in insights["mention_trend"]
    assert insights["mention_trend"]["trend"] > 0  # Should show increasing trend
    
    # Verify topics
    assert len(insights["key_topics"]) > 0
    assert all(isinstance(topic, dict) for topic in insights["key_topics"])
    
    # Verify market position
    assert "market_share" in insights["market_position"]
    assert insights["market_position"]["market_share"] == sample_competitor.market_share

@pytest.mark.asyncio
async def test_set_up_competitor_alerts(
    test_db: AsyncSession,
    competitive_intelligence_service: CompetitiveIntelligenceService,
    sample_competitor: Competitor,
    mock_meltwater_client
):
    """Test setting up competitor alerts"""
    # Replace the service's Meltwater client with our mock
    competitive_intelligence_service.meltwater_client = mock_meltwater_client
    
    alert_config = {
        "frequency": "daily",
        "channels": ["email", "slack"],
        "threshold": "high"
    }
    
    # Set up alerts
    success = await competitive_intelligence_service.set_up_competitor_alerts(
        test_db,
        sample_competitor.id,
        alert_config
    )
    
    assert success is True
    
    # Verify alert configuration was stored
    result = await test_db.execute(
        select(Competitor).where(Competitor.id == sample_competitor.id)
    )
    competitor = result.scalar_one()
    assert "alerts" in competitor.meta_data
    assert competitor.meta_data["alerts"]["meltwater_alert_id"] == "test-alert-id"
    assert competitor.meta_data["alerts"]["config"] == alert_config

@pytest.mark.asyncio
async def test_analyze_mentions(
    competitive_intelligence_service: CompetitiveIntelligenceService,
    mock_meltwater_response
):
    """Test mention analysis"""
    analysis = await competitive_intelligence_service._analyze_mentions(
        mock_meltwater_response["mentions"]
    )
    
    # Verify analysis structure
    assert "total_mentions" in analysis
    assert "sentiment_score" in analysis
    assert "engagement_rate" in analysis
    assert "details" in analysis
    
    # Verify metrics
    assert analysis["total_mentions"] == 2
    assert 0.6 <= analysis["sentiment_score"] <= 0.8
    assert analysis["engagement_rate"] > 0
    
    # Verify details
    assert "sources" in analysis["details"]
    assert "topics" in analysis["details"]
    assert "peak_times" in analysis["details"]
    
    # Verify source analysis
    sources = analysis["details"]["sources"]
    assert "news" in sources
    assert "blogs" in sources
    
    # Verify topics
    topics = analysis["details"]["topics"]
    assert "product launch" in topics
    assert "innovation" in topics

@pytest.mark.asyncio
async def test_invalid_competitor(
    test_db: AsyncSession,
    competitive_intelligence_service: CompetitiveIntelligenceService
):
    """Test handling invalid competitor ID"""
    with pytest.raises(ValueError):
        await competitive_intelligence_service.track_competitor_mentions(
            test_db,
            999999,  # Invalid ID
            datetime.now() - timedelta(days=7),
            datetime.now()
        )

@pytest.mark.asyncio
async def test_empty_mentions(
    test_db: AsyncSession,
    competitive_intelligence_service: CompetitiveIntelligenceService,
    sample_competitor: Competitor
):
    """Test handling empty mentions list"""
    class EmptyMockClient:
        async def get_mentions(self, *args, **kwargs):
            return []
    
    competitive_intelligence_service.meltwater_client = EmptyMockClient()
    
    analysis = await competitive_intelligence_service.track_competitor_mentions(
        test_db,
        sample_competitor.id,
        datetime.now() - timedelta(days=7),
        datetime.now()
    )
    
    assert analysis["total_mentions"] == 0
    assert analysis["sentiment_score"] == 0
    assert analysis["engagement_rate"] == 0
    assert analysis["details"] == {
        "sources": {},
        "topics": [],
        "peak_times": []
    }
