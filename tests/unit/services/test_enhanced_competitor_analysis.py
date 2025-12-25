"""Unit tests for Enhanced Competitor Analysis Service.

This module tests the EnhancedCompetitorAnalysisService which integrates
news data from GNews with competitive intelligence analysis.

Tests cover:
- News enrichment for competitors
- Sentiment analysis of news coverage
- Topic extraction and trend analysis
- Cross-competitor news comparison
- Source diversity analysis
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from src.services.analytics.enhanced_competitor_analysis import (
    EnhancedCompetitorAnalysisService
)
from src.models.external_api import GNewsArticle
from src.models.market import Competitor


class TestEnhancedCompetitorAnalysisService:
    """Test class for EnhancedCompetitorAnalysisService."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration object."""
        config = MagicMock()
        config.meltwater_api_key = "test_key"
        config.meltwater_base_url = "https://api.test.com"
        config.alert_threshold = 0.8
        return config

    @pytest.fixture
    def service(self, mock_config):
        """Create an instance of EnhancedCompetitorAnalysisService."""
        return EnhancedCompetitorAnalysisService(mock_config)

    @pytest.fixture
    def mock_competitor(self):
        """Create a mock competitor object."""
        competitor = MagicMock(spec=Competitor)
        competitor.id = 1
        competitor.name = "Test Company"
        competitor.domain = "testcompany.com"
        competitor.market_share = 15.5
        return competitor

    @pytest.fixture
    def mock_articles(self) -> List[MagicMock]:
        """Create a list of mock GNews articles."""
        articles = []
        base_date = datetime.utcnow()

        test_data = [
            {
                "id": 1,
                "article_id": "art_001",
                "title": "Test Company Announces Amazing New Product Launch",
                "description": "The company revealed their best innovation yet with great success.",
                "source_name": "Tech News Daily",
                "sentiment": "positive"
            },
            {
                "id": 2,
                "article_id": "art_002",
                "title": "Test Company Reports Strong Quarterly Growth",
                "description": "Revenue exceeds expectations with excellent performance.",
                "source_name": "Business Wire",
                "sentiment": "positive"
            },
            {
                "id": 3,
                "article_id": "art_003",
                "title": "Test Company Faces Challenges in Market",
                "description": "The company struggles with declining sales and problems.",
                "source_name": "Market Watch",
                "sentiment": "negative"
            },
            {
                "id": 4,
                "article_id": "art_004",
                "title": "Test Company Updates Terms of Service",
                "description": "Minor changes to user agreements announced.",
                "source_name": "Tech News Daily",
                "sentiment": "neutral"
            },
            {
                "id": 5,
                "article_id": "art_005",
                "title": "Test Company Partners with Industry Leader",
                "description": "Strategic partnership announced for innovation.",
                "source_name": "Industry Today",
                "sentiment": "positive"
            }
        ]

        for i, data in enumerate(test_data):
            article = MagicMock(spec=GNewsArticle)
            article.id = data["id"]
            article.article_id = data["article_id"]
            article.title = data["title"]
            article.description = data["description"]
            article.url = f"https://news.example.com/article/{data['id']}"
            article.image_url = f"https://news.example.com/images/{data['id']}.jpg"
            article.published_at = base_date - timedelta(days=i * 2)
            article.source_name = data["source_name"]
            article.source_url = f"https://{data['source_name'].lower().replace(' ', '')}.com"
            article.query_term = "Test Company"
            article.language = "en"
            article.country = "us"
            article.competitor_id = 1
            articles.append(article)

        return articles

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    # Tests for _analyze_text_sentiment

    def test_analyze_text_sentiment_positive(self, service):
        """Test sentiment analysis for positive text."""
        text = "This is an amazing and wonderful achievement with great success!"
        result = service._analyze_text_sentiment(text)

        assert "score" in result
        assert "category" in result
        assert "confidence" in result
        assert result["score"] > 0
        assert result["category"] == "positive"

    def test_analyze_text_sentiment_negative(self, service):
        """Test sentiment analysis for negative text."""
        text = "This is terrible news with awful consequences and massive failures."
        result = service._analyze_text_sentiment(text)

        assert result["score"] < 0
        assert result["category"] == "negative"

    def test_analyze_text_sentiment_neutral(self, service):
        """Test sentiment analysis for neutral text."""
        text = "The company announced a change in their policy."
        result = service._analyze_text_sentiment(text)

        assert "score" in result
        assert result["category"] in ["neutral", "positive", "negative"]

    def test_analyze_text_sentiment_empty(self, service):
        """Test sentiment analysis for empty text."""
        result = service._analyze_text_sentiment("")
        assert result["score"] == 0.0
        assert result["category"] == "neutral"

    # Tests for _categorize_sentiment

    def test_categorize_sentiment_positive(self, service):
        """Test categorization of positive sentiment score."""
        assert service._categorize_sentiment(0.5) == "positive"
        assert service._categorize_sentiment(0.15) == "positive"

    def test_categorize_sentiment_negative(self, service):
        """Test categorization of negative sentiment score."""
        assert service._categorize_sentiment(-0.5) == "negative"
        assert service._categorize_sentiment(-0.15) == "negative"

    def test_categorize_sentiment_neutral(self, service):
        """Test categorization of neutral sentiment score."""
        assert service._categorize_sentiment(0.0) == "neutral"
        assert service._categorize_sentiment(0.05) == "neutral"
        assert service._categorize_sentiment(-0.05) == "neutral"

    # Tests for _extract_keywords

    def test_extract_keywords_basic(self, service):
        """Test keyword extraction from text."""
        text = "The company announced innovative technology solutions"
        keywords = service._extract_keywords(text)

        assert isinstance(keywords, list)
        assert "company" in keywords
        assert "innovative" in keywords
        assert "technology" in keywords
        # Stop words should be filtered
        assert "the" not in keywords

    def test_extract_keywords_empty(self, service):
        """Test keyword extraction from empty text."""
        keywords = service._extract_keywords("")
        assert keywords == []

    def test_extract_keywords_short_words(self, service):
        """Test that short words are filtered."""
        text = "I am a big fan of AI and ML tech"
        keywords = service._extract_keywords(text)

        # Short words (< 4 chars) should be filtered
        assert "big" not in keywords  # Less than 4 chars
        assert "fan" not in keywords  # Less than 4 chars
        assert "tech" in keywords  # 4 chars

    # Tests for _extract_topics_from_articles

    def test_extract_topics_from_articles(self, service, mock_articles):
        """Test topic extraction from articles."""
        topics = service._extract_topics_from_articles(mock_articles)

        assert isinstance(topics, list)
        assert len(topics) > 0
        assert all("topic" in t for t in topics)
        assert all("count" in t for t in topics)
        assert all("percentage" in t for t in topics)
        # Topics should be sorted by count
        if len(topics) > 1:
            assert topics[0]["count"] >= topics[1]["count"]

    def test_extract_topics_from_articles_empty(self, service):
        """Test topic extraction from empty article list."""
        topics = service._extract_topics_from_articles([])
        assert topics == []

    # Tests for _analyze_source_diversity

    def test_analyze_source_diversity(self, service, mock_articles):
        """Test source diversity analysis."""
        sources = service._analyze_source_diversity(mock_articles)

        assert isinstance(sources, list)
        assert len(sources) > 0
        assert all("source_name" in s for s in sources)
        assert all("article_count" in s for s in sources)
        assert all("percentage" in s for s in sources)

        # Check that percentages sum to ~100
        total_percentage = sum(s["percentage"] for s in sources)
        assert 99 <= total_percentage <= 101

    def test_analyze_source_diversity_empty(self, service):
        """Test source diversity analysis with no articles."""
        sources = service._analyze_source_diversity([])
        assert sources == []

    # Tests for _calculate_volume_trend

    def test_calculate_volume_trend(self, service, mock_articles):
        """Test volume trend calculation."""
        trend = service._calculate_volume_trend(mock_articles, 30)

        assert isinstance(trend, list)
        # Each data point should have date and count
        if trend:
            assert all("date" in t for t in trend)
            assert all("article_count" in t for t in trend)

    def test_calculate_volume_trend_empty(self, service):
        """Test volume trend calculation with no articles."""
        trend = service._calculate_volume_trend([], 30)
        assert trend == []

    # Tests for _calculate_sentiment_distribution

    def test_calculate_sentiment_distribution(self, service):
        """Test sentiment distribution calculation."""
        article_sentiments = [
            {"article": MagicMock(), "sentiment": {"score": 0.5, "category": "positive", "confidence": 0.8}},
            {"article": MagicMock(), "sentiment": {"score": 0.3, "category": "positive", "confidence": 0.7}},
            {"article": MagicMock(), "sentiment": {"score": -0.5, "category": "negative", "confidence": 0.8}},
            {"article": MagicMock(), "sentiment": {"score": 0.0, "category": "neutral", "confidence": 0.5}},
        ]

        distribution = service._calculate_sentiment_distribution(article_sentiments)

        assert distribution["positive"] == 2
        assert distribution["negative"] == 1
        assert distribution["neutral"] == 1

    def test_calculate_sentiment_distribution_empty(self, service):
        """Test sentiment distribution with no articles."""
        distribution = service._calculate_sentiment_distribution([])

        assert distribution["positive"] == 0
        assert distribution["negative"] == 0
        assert distribution["neutral"] == 0

    # Tests for _calculate_volume_change

    def test_calculate_volume_change_increase(self, service):
        """Test volume change calculation for increasing trend."""
        volume_trend = [
            {"date": "2024-01-01", "article_count": 5},
            {"date": "2024-01-08", "article_count": 5},
            {"date": "2024-01-15", "article_count": 10},
            {"date": "2024-01-22", "article_count": 10},
        ]

        change = service._calculate_volume_change(volume_trend)
        assert change > 0  # Should indicate increase

    def test_calculate_volume_change_decrease(self, service):
        """Test volume change calculation for decreasing trend."""
        volume_trend = [
            {"date": "2024-01-01", "article_count": 10},
            {"date": "2024-01-08", "article_count": 10},
            {"date": "2024-01-15", "article_count": 5},
            {"date": "2024-01-22", "article_count": 5},
        ]

        change = service._calculate_volume_change(volume_trend)
        assert change < 0  # Should indicate decrease

    def test_calculate_volume_change_insufficient_data(self, service):
        """Test volume change calculation with insufficient data."""
        change = service._calculate_volume_change([{"date": "2024-01-01", "article_count": 5}])
        assert change == 0.0

    # Tests for _generate_comparison_insights

    def test_generate_comparison_insights(self, service):
        """Test insight generation from competitor comparison."""
        competitor_data = [
            {
                "competitor_id": 1,
                "competitor_name": "Company A",
                "article_count": 50,
                "average_sentiment": 0.45,
                "share_of_voice": 62.5
            },
            {
                "competitor_id": 2,
                "competitor_name": "Company B",
                "article_count": 30,
                "average_sentiment": 0.15,
                "share_of_voice": 37.5
            }
        ]

        insights = service._generate_comparison_insights(competitor_data)

        assert isinstance(insights, list)
        assert len(insights) > 0
        # Should have insights about coverage difference
        assert any("coverage" in insight.lower() or "more" in insight.lower() for insight in insights)

    def test_generate_comparison_insights_single_competitor(self, service):
        """Test insight generation with single competitor."""
        competitor_data = [
            {
                "competitor_id": 1,
                "competitor_name": "Company A",
                "article_count": 50,
                "average_sentiment": 0.45,
                "share_of_voice": 100.0
            }
        ]

        insights = service._generate_comparison_insights(competitor_data)
        assert "Insufficient data" in insights[0]

    # Tests for _article_to_dict

    def test_article_to_dict(self, service, mock_articles):
        """Test conversion of article to dictionary."""
        article = mock_articles[0]
        sentiment = {"score": 0.5, "category": "positive", "confidence": 0.8}

        result = service._article_to_dict(article, sentiment)

        assert result["id"] == article.id
        assert result["article_id"] == article.article_id
        assert result["title"] == article.title
        assert result["sentiment"]["score"] == 0.5
        assert result["sentiment"]["category"] == "positive"

    # Tests for _empty_sentiment_response

    def test_empty_sentiment_response(self, service):
        """Test generation of empty sentiment response."""
        start_date = datetime.utcnow() - timedelta(days=30)
        result = service._empty_sentiment_response(
            competitor_id=1,
            competitor_name="Test Company",
            start_date=start_date
        )

        assert result["competitor_id"] == 1
        assert result["competitor_name"] == "Test Company"
        assert result["article_count"] == 0
        assert result["overall_sentiment"]["score"] == 0.0
        assert result["overall_sentiment"]["category"] == "neutral"
        assert result["sentiment_distribution"]["positive"] == 0
        assert result["top_positive_articles"] == []
        assert result["top_negative_articles"] == []

    # Integration tests with mocked dependencies

    @pytest.mark.asyncio
    async def test_enrich_with_news(self, service, mock_session, mock_competitor, mock_articles):
        """Test news enrichment for competitor."""
        # Mock the competitor lookup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_competitor
        mock_session.execute.return_value = mock_result

        # Mock GNewsRepository
        with patch("src.services.analytics.enhanced_competitor_analysis.GNewsRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_articles_by_competitor = AsyncMock(return_value=mock_articles)

            # Mock CompetitorMetricsRepository
            with patch("src.services.analytics.enhanced_competitor_analysis.CompetitorMetricsRepository") as MockMetricsRepo:
                mock_metrics_repo = MockMetricsRepo.return_value
                mock_metrics_repo.create_metric = AsyncMock(return_value=MagicMock())

                # Mock competitive intelligence service
                with patch.object(service.competitive_intelligence, "get_competitor_insights") as mock_insights:
                    mock_insights.return_value = {
                        "mention_trend": {"trend": 0.5, "confidence": 0.8},
                        "sentiment_analysis": {"trend": 0.3, "confidence": 0.7}
                    }

                    result = await service.enrich_with_news(
                        session=mock_session,
                        competitor_id=1,
                        days_back=30
                    )

                    assert result["competitor_id"] == 1
                    assert result["competitor_name"] == "Test Company"
                    assert "news_coverage" in result
                    assert "sentiment" in result
                    assert "topics" in result
                    assert "source_diversity" in result

    @pytest.mark.asyncio
    async def test_enrich_with_news_not_found(self, service, mock_session):
        """Test news enrichment when competitor is not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(ValueError) as exc_info:
            await service.enrich_with_news(
                session=mock_session,
                competitor_id=999,
                days_back=30
            )

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analyze_news_sentiment(self, service, mock_session, mock_competitor, mock_articles):
        """Test sentiment analysis of news."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_competitor
        mock_session.execute.return_value = mock_result

        with patch("src.services.analytics.enhanced_competitor_analysis.GNewsRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_articles_by_competitor = AsyncMock(return_value=mock_articles)

            result = await service.analyze_news_sentiment(
                session=mock_session,
                competitor_id=1,
                days_back=30
            )

            assert result["competitor_id"] == 1
            assert "overall_sentiment" in result
            assert "article_count" in result
            assert result["article_count"] == len(mock_articles)
            assert "sentiment_distribution" in result
            assert "top_positive_articles" in result
            assert "top_negative_articles" in result

    @pytest.mark.asyncio
    async def test_analyze_news_sentiment_no_articles(self, service, mock_session, mock_competitor):
        """Test sentiment analysis with no articles."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_competitor
        mock_session.execute.return_value = mock_result

        with patch("src.services.analytics.enhanced_competitor_analysis.GNewsRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_articles_by_competitor = AsyncMock(return_value=[])

            result = await service.analyze_news_sentiment(
                session=mock_session,
                competitor_id=1,
                days_back=30
            )

            assert result["article_count"] == 0
            assert result["overall_sentiment"]["score"] == 0.0

    @pytest.mark.asyncio
    async def test_get_news_trends(self, service, mock_session, mock_competitor, mock_articles):
        """Test news trends retrieval."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_competitor
        mock_session.execute.return_value = mock_result

        with patch("src.services.analytics.enhanced_competitor_analysis.GNewsRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_articles_by_competitor = AsyncMock(return_value=mock_articles)

            result = await service.get_news_trends(
                session=mock_session,
                competitor_id=1,
                days_back=30
            )

            assert result["competitor_id"] == 1
            assert "total_articles" in result
            assert "volume_trend" in result
            assert "trending_topics" in result
            assert "emerging_topics" in result
            assert "source_diversity" in result

    @pytest.mark.asyncio
    async def test_compare_news_coverage(self, service, mock_session, mock_competitor, mock_articles):
        """Test cross-competitor news comparison."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_competitor
        mock_session.execute.return_value = mock_result

        with patch("src.services.analytics.enhanced_competitor_analysis.GNewsRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_articles_by_competitor = AsyncMock(return_value=mock_articles)

            result = await service.compare_news_coverage(
                session=mock_session,
                competitor_ids=[1, 2],
                days_back=30
            )

            assert "competitors" in result
            assert "total_articles" in result
            assert "coverage_leader" in result
            assert "sentiment_leader" in result
            assert "insights" in result

    @pytest.mark.asyncio
    async def test_compare_news_coverage_empty_ids(self, service, mock_session):
        """Test comparison with empty competitor IDs."""
        with pytest.raises(ValueError) as exc_info:
            await service.compare_news_coverage(
                session=mock_session,
                competitor_ids=[],
                days_back=30
            )

        assert "required" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_refresh_competitor_news(self, service, mock_session, mock_competitor):
        """Test refreshing competitor news."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_competitor
        mock_session.execute.return_value = mock_result

        with patch("src.services.analytics.enhanced_competitor_analysis.GNewsRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.count_articles_by_competitor = AsyncMock(return_value=50)

            result = await service.refresh_competitor_news(
                session=mock_session,
                competitor_id=1,
                days_back=30
            )

            assert result["competitor_id"] == 1
            assert result["competitor_name"] == "Test Company"
            assert "total_articles" in result
            assert result["status"] == "success"

    # Tests for _identify_trending_topics

    def test_identify_trending_topics(self, service, mock_articles):
        """Test identification of trending topics."""
        # This test verifies the method handles articles correctly
        trending, emerging = service._identify_trending_topics(mock_articles, 30)

        assert isinstance(trending, list)
        assert isinstance(emerging, list)

    def test_identify_trending_topics_empty(self, service):
        """Test trending topic identification with no articles."""
        trending, emerging = service._identify_trending_topics([], 30)

        assert trending == []
        assert emerging == []

    # Tests for _find_peak_coverage_dates

    def test_find_peak_coverage_dates(self, service, mock_articles):
        """Test finding peak coverage dates."""
        peaks = service._find_peak_coverage_dates(mock_articles)

        assert isinstance(peaks, list)
        # If there are peaks, they should have required fields
        for peak in peaks:
            assert "date" in peak
            assert "article_count" in peak
            assert "reason" in peak

    def test_find_peak_coverage_dates_empty(self, service):
        """Test peak coverage with no articles."""
        peaks = service._find_peak_coverage_dates([])
        assert peaks == []


class TestEnhancedCompetitorAnalysisServiceEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration object."""
        config = MagicMock()
        config.meltwater_api_key = "test_key"
        config.meltwater_base_url = "https://api.test.com"
        config.alert_threshold = 0.8
        return config

    @pytest.fixture
    def service(self, mock_config):
        """Create an instance of EnhancedCompetitorAnalysisService."""
        return EnhancedCompetitorAnalysisService(mock_config)

    def test_analyze_text_sentiment_with_special_characters(self, service):
        """Test sentiment analysis with special characters."""
        text = "This is GREAT!!! @company #success $$$"
        result = service._analyze_text_sentiment(text)

        assert "score" in result
        assert "category" in result

    def test_analyze_text_sentiment_with_unicode(self, service):
        """Test sentiment analysis with unicode characters."""
        text = "This is excellent news! \u2764\ufe0f Amazing results \u2728"
        result = service._analyze_text_sentiment(text)

        assert "score" in result

    def test_extract_keywords_with_numbers(self, service):
        """Test keyword extraction with numbers in text."""
        text = "Company achieved 100% growth in 2024 fiscal year"
        keywords = service._extract_keywords(text)

        assert "company" in keywords
        assert "achieved" in keywords
        assert "growth" in keywords

    def test_analyze_source_diversity_single_source(self, service):
        """Test source diversity with single source."""
        article = MagicMock(spec=GNewsArticle)
        article.source_name = "Single Source"

        sources = service._analyze_source_diversity([article])

        assert len(sources) == 1
        assert sources[0]["source_name"] == "Single Source"
        assert sources[0]["percentage"] == 100.0

    def test_calculate_volume_change_zero_first_half(self, service):
        """Test volume change when first half has zero articles."""
        volume_trend = [
            {"date": "2024-01-01", "article_count": 0},
            {"date": "2024-01-08", "article_count": 0},
            {"date": "2024-01-15", "article_count": 5},
            {"date": "2024-01-22", "article_count": 5},
        ]

        change = service._calculate_volume_change(volume_trend)
        assert change == 100.0  # Should indicate 100% increase from zero

    def test_generate_comparison_insights_tied_coverage(self, service):
        """Test insight generation when competitors have equal coverage."""
        competitor_data = [
            {
                "competitor_id": 1,
                "competitor_name": "Company A",
                "article_count": 50,
                "average_sentiment": 0.45,
                "share_of_voice": 50.0
            },
            {
                "competitor_id": 2,
                "competitor_name": "Company B",
                "article_count": 50,
                "average_sentiment": 0.15,
                "share_of_voice": 50.0
            }
        ]

        insights = service._generate_comparison_insights(competitor_data)
        # Should still generate insights about sentiment difference
        assert isinstance(insights, list)
