"""Enhanced Competitor Analysis Service with News Integration.

This module provides enhanced competitor analysis by integrating news data
from GNews API with existing competitive intelligence capabilities.

Features:
- News enrichment for competitor profiles
- Sentiment analysis of competitor news coverage
- Topic extraction and trend analysis
- Cross-competitor news coverage comparison
- Source diversity analysis
"""
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from textblob import TextBlob

from src.config import Config
from src.models.external_api import GNewsArticle
from src.models.market import Competitor, CompetitorMetrics
from src.repositories.gnews_repository import GNewsRepository
from src.repositories.competitor_metrics_repository import CompetitorMetricsRepository
from src.services.analytics.competitive_intelligence_service import (
    CompetitiveIntelligenceService
)

logger = logging.getLogger(__name__)


class EnhancedCompetitorAnalysisService:
    """Service for enhanced competitor analysis with news integration.

    This service extends the base competitive intelligence capabilities
    by integrating news data from GNews for richer competitor insights.

    Attributes:
        config: Application configuration
        competitive_intelligence: Base competitive intelligence service
    """

    # Stop words for topic extraction
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'it', 'its', 'they', 'them', 'their', 'this', 'that', 'these', 'those',
        'i', 'you', 'he', 'she', 'we', 'who', 'which', 'what', 'when', 'where',
        'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
        'other', 'some', 'such', 'no', 'not', 'only', 'same', 'so', 'than',
        'too', 'very', 'just', 'also', 'now', 'here', 'there', 'then', 'new',
        'says', 'said', 'will', 'after', 'before', 'about', 'over', 'into'
    }

    def __init__(self, config: Config):
        """Initialize the enhanced competitor analysis service.

        Args:
            config: Application configuration object
        """
        self.config = config
        self.competitive_intelligence = CompetitiveIntelligenceService(config)

    async def enrich_with_news(
        self,
        session: AsyncSession,
        competitor_id: int,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Enrich competitor data with news context.

        Fetches and analyzes recent news articles for a competitor,
        adding context about media coverage, sentiment, and topics.

        Args:
            session: Database session
            competitor_id: ID of the competitor to enrich
            days_back: Number of days to look back for news

        Returns:
            Dict containing enriched competitor data with news context

        Raises:
            ValueError: If competitor is not found
        """
        competitor = await self._get_competitor(session, competitor_id)
        if not competitor:
            raise ValueError(f"Competitor with id {competitor_id} not found")

        gnews_repo = GNewsRepository(session)
        start_date = datetime.utcnow() - timedelta(days=days_back)

        # Get articles for the competitor
        articles = await gnews_repo.get_articles_by_competitor(
            competitor_id=competitor_id,
            start_date=start_date,
            limit=500
        )

        # Analyze the articles
        sentiment_data = await self._analyze_article_sentiments(articles)
        topics = self._extract_topics_from_articles(articles)
        source_analysis = self._analyze_source_diversity(articles)
        volume_trend = self._calculate_volume_trend(articles, days_back)

        # Get base competitive intelligence
        base_insights = await self.competitive_intelligence.get_competitor_insights(
            session=session,
            competitor_id=competitor_id,
            days=days_back
        )

        # Store enrichment metrics
        await self._store_news_enrichment_metrics(
            session=session,
            competitor_id=competitor_id,
            sentiment_data=sentiment_data,
            article_count=len(articles),
            days_back=days_back
        )

        return {
            "competitor_id": competitor_id,
            "competitor_name": competitor.name,
            "domain": competitor.domain,
            "analysis_period": {
                "start": start_date.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "news_coverage": {
                "total_articles": len(articles),
                "sources_count": len(source_analysis),
                "average_articles_per_day": len(articles) / max(days_back, 1)
            },
            "sentiment": sentiment_data,
            "topics": topics[:20],  # Top 20 topics
            "source_diversity": source_analysis[:10],  # Top 10 sources
            "volume_trend": volume_trend,
            "base_insights": base_insights
        }

    async def analyze_news_sentiment(
        self,
        session: AsyncSession,
        competitor_id: int,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Analyze sentiment of news coverage for a competitor.

        Performs detailed sentiment analysis on news articles,
        including distribution, trends, and key article highlights.

        Args:
            session: Database session
            competitor_id: ID of the competitor
            days_back: Number of days to analyze

        Returns:
            Dict containing detailed sentiment analysis results

        Raises:
            ValueError: If competitor is not found
        """
        competitor = await self._get_competitor(session, competitor_id)
        if not competitor:
            raise ValueError(f"Competitor with id {competitor_id} not found")

        gnews_repo = GNewsRepository(session)
        start_date = datetime.utcnow() - timedelta(days=days_back)

        articles = await gnews_repo.get_articles_by_competitor(
            competitor_id=competitor_id,
            start_date=start_date,
            limit=500
        )

        if not articles:
            return self._empty_sentiment_response(
                competitor_id=competitor_id,
                competitor_name=competitor.name,
                start_date=start_date
            )

        # Analyze each article's sentiment
        article_sentiments = []
        for article in articles:
            sentiment = self._analyze_text_sentiment(
                f"{article.title} {article.description or ''}"
            )
            article_sentiments.append({
                "article": article,
                "sentiment": sentiment
            })

        # Calculate overall metrics
        scores = [s["sentiment"]["score"] for s in article_sentiments]
        overall_score = sum(scores) / len(scores)
        overall_category = self._categorize_sentiment(overall_score)
        overall_confidence = sum(
            s["sentiment"]["confidence"] for s in article_sentiments
        ) / len(article_sentiments)

        # Get distribution
        distribution = self._calculate_sentiment_distribution(article_sentiments)

        # Get top positive and negative articles
        sorted_by_sentiment = sorted(
            article_sentiments,
            key=lambda x: x["sentiment"]["score"],
            reverse=True
        )
        top_positive = sorted_by_sentiment[:5]
        top_negative = sorted_by_sentiment[-5:][::-1]

        # Calculate sentiment trend
        sentiment_trend = self._calculate_sentiment_trend(article_sentiments, days_back)

        # Extract topics with sentiment context
        topics = self._extract_topics_with_sentiment(article_sentiments)

        return {
            "competitor_id": competitor_id,
            "competitor_name": competitor.name,
            "analysis_period": {
                "start": start_date.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "overall_sentiment": {
                "score": round(overall_score, 4),
                "category": overall_category,
                "confidence": round(overall_confidence, 4)
            },
            "article_count": len(articles),
            "sentiment_distribution": distribution,
            "top_positive_articles": [
                self._article_to_dict(a["article"], a["sentiment"])
                for a in top_positive
            ],
            "top_negative_articles": [
                self._article_to_dict(a["article"], a["sentiment"])
                for a in top_negative
            ],
            "sentiment_trend": sentiment_trend,
            "key_topics": topics[:15]
        }

    async def get_news_trends(
        self,
        session: AsyncSession,
        competitor_id: int,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get news volume trends for a competitor.

        Analyzes patterns in news coverage volume, identifying
        trends, peak coverage dates, and source diversity.

        Args:
            session: Database session
            competitor_id: ID of the competitor
            days_back: Number of days to analyze

        Returns:
            Dict containing news trend analysis

        Raises:
            ValueError: If competitor is not found
        """
        competitor = await self._get_competitor(session, competitor_id)
        if not competitor:
            raise ValueError(f"Competitor with id {competitor_id} not found")

        gnews_repo = GNewsRepository(session)
        start_date = datetime.utcnow() - timedelta(days=days_back)

        articles = await gnews_repo.get_articles_by_competitor(
            competitor_id=competitor_id,
            start_date=start_date,
            limit=500
        )

        # Calculate volume trend with sentiment
        volume_trend = self._calculate_volume_trend_with_sentiment(
            articles, days_back
        )

        # Calculate volume change
        volume_change = self._calculate_volume_change(volume_trend)

        # Get trending and emerging topics
        trending_topics, emerging_topics = self._identify_trending_topics(
            articles, days_back
        )

        # Analyze source diversity
        source_diversity = self._analyze_source_diversity_detailed(articles)

        # Find peak coverage dates
        peak_dates = self._find_peak_coverage_dates(articles)

        return {
            "competitor_id": competitor_id,
            "competitor_name": competitor.name,
            "analysis_period": {
                "start": start_date.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "total_articles": len(articles),
            "volume_trend": volume_trend,
            "volume_change_percentage": round(volume_change, 2),
            "trending_topics": trending_topics[:10],
            "emerging_topics": emerging_topics[:10],
            "source_diversity": source_diversity[:15],
            "peak_coverage_dates": peak_dates[:10]
        }

    async def compare_news_coverage(
        self,
        session: AsyncSession,
        competitor_ids: List[int],
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Compare news coverage across multiple competitors.

        Analyzes and compares news coverage, sentiment, and topics
        across multiple competitors for competitive positioning.

        Args:
            session: Database session
            competitor_ids: List of competitor IDs to compare
            days_back: Number of days to analyze

        Returns:
            Dict containing comparative news analysis

        Raises:
            ValueError: If no valid competitors are found
        """
        if not competitor_ids:
            raise ValueError("At least one competitor ID is required")

        gnews_repo = GNewsRepository(session)
        start_date = datetime.utcnow() - timedelta(days=days_back)

        competitor_data = []
        total_articles = 0

        for competitor_id in competitor_ids:
            competitor = await self._get_competitor(session, competitor_id)
            if not competitor:
                logger.warning(f"Competitor {competitor_id} not found, skipping")
                continue

            articles = await gnews_repo.get_articles_by_competitor(
                competitor_id=competitor_id,
                start_date=start_date,
                limit=500
            )

            # Analyze sentiment for articles
            sentiments = [
                self._analyze_text_sentiment(
                    f"{a.title} {a.description or ''}"
                )
                for a in articles
            ]

            avg_sentiment = (
                sum(s["score"] for s in sentiments) / len(sentiments)
                if sentiments else 0.0
            )

            # Get top sources
            sources = Counter(a.source_name for a in articles)
            top_sources = [s[0] for s in sources.most_common(5)]

            # Get top topics
            all_topics = self._extract_topics_from_articles(articles)
            top_topics = [t["topic"] for t in all_topics[:5]]

            competitor_data.append({
                "competitor_id": competitor_id,
                "competitor_name": competitor.name,
                "article_count": len(articles),
                "average_sentiment": round(avg_sentiment, 4),
                "sentiment_category": self._categorize_sentiment(avg_sentiment),
                "top_sources": top_sources,
                "top_topics": top_topics
            })

            total_articles += len(articles)

        if not competitor_data:
            raise ValueError("No valid competitors found for comparison")

        # Calculate share of voice
        for comp in competitor_data:
            comp["share_of_voice"] = round(
                (comp["article_count"] / max(total_articles, 1)) * 100, 2
            )

        # Identify leaders
        coverage_leader = max(
            competitor_data, key=lambda x: x["article_count"]
        )["competitor_id"]
        sentiment_leader = max(
            competitor_data, key=lambda x: x["average_sentiment"]
        )["competitor_id"]

        # Generate insights
        insights = self._generate_comparison_insights(competitor_data)

        return {
            "analysis_period": {
                "start": start_date.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "total_articles": total_articles,
            "competitors": competitor_data,
            "coverage_leader": coverage_leader,
            "sentiment_leader": sentiment_leader,
            "insights": insights
        }

    async def refresh_competitor_news(
        self,
        session: AsyncSession,
        competitor_id: int,
        days_back: int = 30,
        analyze_sentiment: bool = True
    ) -> Dict[str, Any]:
        """Refresh news data for a competitor.

        This method would typically call the GNews API to fetch new articles.
        For now, it returns statistics about existing data.

        Args:
            session: Database session
            competitor_id: ID of the competitor
            days_back: Number of days to fetch
            analyze_sentiment: Whether to analyze sentiment

        Returns:
            Dict containing refresh operation results

        Raises:
            ValueError: If competitor is not found
        """
        competitor = await self._get_competitor(session, competitor_id)
        if not competitor:
            raise ValueError(f"Competitor with id {competitor_id} not found")

        gnews_repo = GNewsRepository(session)
        start_date = datetime.utcnow() - timedelta(days=days_back)

        # Get existing article count
        existing_count = await gnews_repo.count_articles_by_competitor(
            competitor_id=competitor_id,
            start_date=start_date
        )

        # Note: In a full implementation, this would call GNews API
        # to fetch new articles. For now, we return current state.
        return {
            "competitor_id": competitor_id,
            "competitor_name": competitor.name,
            "articles_fetched": 0,  # Would be populated by actual API call
            "articles_updated": 0,
            "total_articles": existing_count,
            "fetch_date_range": {
                "start": start_date.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "status": "success",
            "errors": []
        }

    # Private helper methods

    async def _get_competitor(
        self,
        session: AsyncSession,
        competitor_id: int
    ) -> Optional[Competitor]:
        """Get competitor by ID."""
        result = await session.execute(
            select(Competitor).where(Competitor.id == competitor_id)
        )
        return result.scalar_one_or_none()

    async def _analyze_article_sentiments(
        self,
        articles: List[GNewsArticle]
    ) -> Dict[str, Any]:
        """Analyze sentiment across a collection of articles."""
        if not articles:
            return {
                "score": 0.0,
                "category": "neutral",
                "confidence": 0.0,
                "sample_size": 0
            }

        sentiments = []
        for article in articles:
            text = f"{article.title} {article.description or ''}"
            sentiment = self._analyze_text_sentiment(text)
            sentiments.append(sentiment)

        avg_score = sum(s["score"] for s in sentiments) / len(sentiments)
        avg_confidence = sum(s["confidence"] for s in sentiments) / len(sentiments)

        return {
            "score": round(avg_score, 4),
            "category": self._categorize_sentiment(avg_score),
            "confidence": round(avg_confidence, 4),
            "sample_size": len(articles)
        }

    def _analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text using TextBlob."""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            # Confidence is based on subjectivity - more subjective = more confident
            confidence = 0.5 + (subjectivity * 0.5)

            return {
                "score": round(polarity, 4),
                "category": self._categorize_sentiment(polarity),
                "confidence": round(confidence, 4),
                "subjectivity": round(subjectivity, 4)
            }
        except Exception as e:
            logger.warning(f"Error analyzing sentiment: {e}")
            return {
                "score": 0.0,
                "category": "neutral",
                "confidence": 0.0,
                "subjectivity": 0.0
            }

    def _categorize_sentiment(self, score: float) -> str:
        """Categorize a sentiment score."""
        if score > 0.1:
            return "positive"
        elif score < -0.1:
            return "negative"
        return "neutral"

    def _extract_topics_from_articles(
        self,
        articles: List[GNewsArticle]
    ) -> List[Dict[str, Any]]:
        """Extract topics from article titles and descriptions."""
        word_counts: Counter = Counter()

        for article in articles:
            text = f"{article.title} {article.description or ''}"
            words = self._extract_keywords(text)
            word_counts.update(words)

        total = len(articles)
        topics = []

        for word, count in word_counts.most_common(50):
            topics.append({
                "topic": word,
                "count": count,
                "percentage": round((count / max(total, 1)) * 100, 2)
            })

        return topics

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text, filtering stop words."""
        # Clean and tokenize
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        # Filter stop words and short words
        keywords = [
            w for w in words
            if w not in self.STOP_WORDS and len(w) >= 4
        ]

        return keywords

    def _analyze_source_diversity(
        self,
        articles: List[GNewsArticle]
    ) -> List[Dict[str, Any]]:
        """Analyze diversity of news sources."""
        source_counts = Counter(a.source_name for a in articles)
        total = len(articles)

        sources = []
        for source, count in source_counts.most_common():
            sources.append({
                "source_name": source,
                "article_count": count,
                "percentage": round((count / max(total, 1)) * 100, 2)
            })

        return sources

    def _analyze_source_diversity_detailed(
        self,
        articles: List[GNewsArticle]
    ) -> List[Dict[str, Any]]:
        """Analyze source diversity with sentiment per source."""
        source_data: Dict[str, Dict] = defaultdict(
            lambda: {"articles": [], "sentiments": []}
        )

        for article in articles:
            text = f"{article.title} {article.description or ''}"
            sentiment = self._analyze_text_sentiment(text)
            source_data[article.source_name]["articles"].append(article)
            source_data[article.source_name]["sentiments"].append(
                sentiment["score"]
            )

        total = len(articles)
        result = []

        for source, data in source_data.items():
            count = len(data["articles"])
            avg_sentiment = (
                sum(data["sentiments"]) / len(data["sentiments"])
                if data["sentiments"] else 0.0
            )

            result.append({
                "source_name": source,
                "article_count": count,
                "percentage": round((count / max(total, 1)) * 100, 2),
                "average_sentiment": round(avg_sentiment, 4)
            })

        return sorted(result, key=lambda x: x["article_count"], reverse=True)

    def _calculate_volume_trend(
        self,
        articles: List[GNewsArticle],
        days_back: int
    ) -> List[Dict[str, Any]]:
        """Calculate news volume trend over time."""
        if not articles:
            return []

        # Group articles by date
        date_counts: Counter = Counter()
        for article in articles:
            if article.published_at:
                date_key = article.published_at.date()
                date_counts[date_key] += 1

        # Create trend data
        trend = []
        for date, count in sorted(date_counts.items()):
            trend.append({
                "date": date.isoformat(),
                "article_count": count
            })

        return trend

    def _calculate_volume_trend_with_sentiment(
        self,
        articles: List[GNewsArticle],
        days_back: int
    ) -> List[Dict[str, Any]]:
        """Calculate volume trend with average sentiment per day."""
        if not articles:
            return []

        # Group articles by date with sentiment
        date_data: Dict[str, Dict] = defaultdict(
            lambda: {"count": 0, "sentiments": []}
        )

        for article in articles:
            if article.published_at:
                date_key = article.published_at.date().isoformat()
                text = f"{article.title} {article.description or ''}"
                sentiment = self._analyze_text_sentiment(text)

                date_data[date_key]["count"] += 1
                date_data[date_key]["sentiments"].append(sentiment["score"])

        # Create trend data
        trend = []
        for date_str, data in sorted(date_data.items()):
            avg_sentiment = (
                sum(data["sentiments"]) / len(data["sentiments"])
                if data["sentiments"] else 0.0
            )

            trend.append({
                "date": date_str,
                "article_count": data["count"],
                "average_sentiment": round(avg_sentiment, 4)
            })

        return trend

    def _calculate_volume_change(
        self,
        volume_trend: List[Dict[str, Any]]
    ) -> float:
        """Calculate percentage change in volume."""
        if len(volume_trend) < 2:
            return 0.0

        # Compare first half vs second half
        midpoint = len(volume_trend) // 2
        first_half = volume_trend[:midpoint]
        second_half = volume_trend[midpoint:]

        first_avg = (
            sum(d["article_count"] for d in first_half) / len(first_half)
            if first_half else 0
        )
        second_avg = (
            sum(d["article_count"] for d in second_half) / len(second_half)
            if second_half else 0
        )

        if first_avg == 0:
            return 100.0 if second_avg > 0 else 0.0

        return ((second_avg - first_avg) / first_avg) * 100

    def _calculate_sentiment_distribution(
        self,
        article_sentiments: List[Dict]
    ) -> Dict[str, int]:
        """Calculate distribution of sentiment categories."""
        distribution = {"positive": 0, "neutral": 0, "negative": 0}

        for item in article_sentiments:
            category = item["sentiment"]["category"]
            distribution[category] = distribution.get(category, 0) + 1

        return distribution

    def _calculate_sentiment_trend(
        self,
        article_sentiments: List[Dict],
        days_back: int
    ) -> List[Dict[str, Any]]:
        """Calculate sentiment trend over time."""
        if not article_sentiments:
            return []

        # Group by week
        week_data: Dict[str, Dict] = defaultdict(
            lambda: {"scores": [], "count": 0}
        )

        for item in article_sentiments:
            article = item["article"]
            if article.published_at:
                # Get week start date
                week_start = article.published_at - timedelta(
                    days=article.published_at.weekday()
                )
                week_key = week_start.date().isoformat()

                week_data[week_key]["scores"].append(item["sentiment"]["score"])
                week_data[week_key]["count"] += 1

        # Create trend data
        trend = []
        for week_str, data in sorted(week_data.items()):
            avg_score = sum(data["scores"]) / len(data["scores"])
            trend.append({
                "date": week_str,
                "score": round(avg_score, 4),
                "count": data["count"]
            })

        return trend

    def _extract_topics_with_sentiment(
        self,
        article_sentiments: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Extract topics with associated sentiment."""
        topic_sentiments: Dict[str, List[float]] = defaultdict(list)

        for item in article_sentiments:
            article = item["article"]
            sentiment_score = item["sentiment"]["score"]

            text = f"{article.title} {article.description or ''}"
            keywords = self._extract_keywords(text)

            for keyword in keywords:
                topic_sentiments[keyword].append(sentiment_score)

        # Calculate topic metrics
        topics = []
        total_articles = len(article_sentiments)

        for topic, sentiments in topic_sentiments.items():
            count = len(sentiments)
            avg_sentiment = sum(sentiments) / len(sentiments)

            topics.append({
                "topic": topic,
                "count": count,
                "percentage": round((count / max(total_articles, 1)) * 100, 2),
                "average_sentiment": round(avg_sentiment, 4)
            })

        return sorted(topics, key=lambda x: x["count"], reverse=True)

    def _identify_trending_topics(
        self,
        articles: List[GNewsArticle],
        days_back: int
    ) -> Tuple[List[Dict], List[Dict]]:
        """Identify trending and emerging topics."""
        if not articles:
            return [], []

        # Split articles into halves
        midpoint_date = datetime.utcnow() - timedelta(days=days_back // 2)

        first_half = [a for a in articles if a.published_at and a.published_at < midpoint_date]
        second_half = [a for a in articles if a.published_at and a.published_at >= midpoint_date]

        # Extract topics from each half
        first_topics = self._extract_topics_from_articles(first_half)
        second_topics = self._extract_topics_from_articles(second_half)

        # Create lookup for first half
        first_topic_map = {t["topic"]: t["count"] for t in first_topics}
        second_topic_map = {t["topic"]: t["count"] for t in second_topics}

        # Trending: topics that increased significantly
        trending = []
        for topic_data in second_topics:
            topic = topic_data["topic"]
            second_count = topic_data["count"]
            first_count = first_topic_map.get(topic, 0)

            if first_count > 0 and second_count > first_count * 1.5:
                trending.append({
                    "topic": topic,
                    "count": second_count,
                    "percentage": topic_data["percentage"],
                    "growth": round(
                        ((second_count - first_count) / first_count) * 100, 2
                    )
                })

        # Emerging: topics that appear only in second half
        emerging = []
        for topic_data in second_topics:
            topic = topic_data["topic"]
            if topic not in first_topic_map and topic_data["count"] >= 3:
                emerging.append(topic_data)

        return (
            sorted(trending, key=lambda x: x["count"], reverse=True),
            sorted(emerging, key=lambda x: x["count"], reverse=True)
        )

    def _find_peak_coverage_dates(
        self,
        articles: List[GNewsArticle]
    ) -> List[Dict[str, Any]]:
        """Find dates with peak news coverage."""
        if not articles:
            return []

        # Group by date
        date_articles: Dict[str, List[GNewsArticle]] = defaultdict(list)
        for article in articles:
            if article.published_at:
                date_key = article.published_at.date().isoformat()
                date_articles[date_key].append(article)

        # Find peaks (dates with above-average coverage)
        counts = [len(arts) for arts in date_articles.values()]
        if not counts:
            return []

        avg_count = sum(counts) / len(counts)
        threshold = avg_count * 1.5

        peaks = []
        for date_str, arts in date_articles.items():
            count = len(arts)
            if count >= threshold:
                # Try to identify reason (most common topic)
                topics = self._extract_topics_from_articles(arts)
                reason = topics[0]["topic"] if topics else "unknown"

                peaks.append({
                    "date": date_str,
                    "article_count": count,
                    "reason": reason
                })

        return sorted(peaks, key=lambda x: x["article_count"], reverse=True)

    def _generate_comparison_insights(
        self,
        competitor_data: List[Dict]
    ) -> List[str]:
        """Generate insights from competitor comparison."""
        insights = []

        if len(competitor_data) < 2:
            return ["Insufficient data for comparison"]

        # Sort by coverage
        by_coverage = sorted(
            competitor_data,
            key=lambda x: x["article_count"],
            reverse=True
        )

        # Sort by sentiment
        by_sentiment = sorted(
            competitor_data,
            key=lambda x: x["average_sentiment"],
            reverse=True
        )

        # Coverage leader insight
        leader = by_coverage[0]
        runner_up = by_coverage[1]

        if leader["article_count"] > runner_up["article_count"]:
            diff_pct = round(
                ((leader["article_count"] - runner_up["article_count"]) /
                 max(runner_up["article_count"], 1)) * 100
            )
            insights.append(
                f"{leader['competitor_name']} has {diff_pct}% more news coverage "
                f"than {runner_up['competitor_name']}"
            )

        # Sentiment leader insight
        if by_sentiment[0]["average_sentiment"] > by_sentiment[-1]["average_sentiment"] + 0.2:
            insights.append(
                f"{by_sentiment[0]['competitor_name']} has significantly more "
                f"positive news sentiment than competitors"
            )

        # Share of voice insight
        top_sov = max(competitor_data, key=lambda x: x["share_of_voice"])
        if top_sov["share_of_voice"] > 50:
            insights.append(
                f"{top_sov['competitor_name']} dominates news coverage with "
                f"{top_sov['share_of_voice']}% share of voice"
            )

        return insights

    def _article_to_dict(
        self,
        article: GNewsArticle,
        sentiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert article to dictionary with sentiment."""
        return {
            "id": article.id,
            "article_id": article.article_id,
            "title": article.title,
            "description": article.description,
            "url": article.url,
            "image_url": article.image_url,
            "published_at": (
                article.published_at.isoformat()
                if article.published_at else None
            ),
            "source_name": article.source_name,
            "source_url": article.source_url,
            "query_term": article.query_term,
            "language": article.language,
            "country": article.country,
            "sentiment": {
                "score": sentiment["score"],
                "category": sentiment["category"],
                "confidence": sentiment["confidence"]
            }
        }

    def _empty_sentiment_response(
        self,
        competitor_id: int,
        competitor_name: str,
        start_date: datetime
    ) -> Dict[str, Any]:
        """Return empty sentiment response when no articles are found."""
        return {
            "competitor_id": competitor_id,
            "competitor_name": competitor_name,
            "analysis_period": {
                "start": start_date.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "overall_sentiment": {
                "score": 0.0,
                "category": "neutral",
                "confidence": 0.0
            },
            "article_count": 0,
            "sentiment_distribution": {
                "positive": 0,
                "neutral": 0,
                "negative": 0
            },
            "top_positive_articles": [],
            "top_negative_articles": [],
            "sentiment_trend": [],
            "key_topics": []
        }

    async def _store_news_enrichment_metrics(
        self,
        session: AsyncSession,
        competitor_id: int,
        sentiment_data: Dict[str, Any],
        article_count: int,
        days_back: int
    ) -> None:
        """Store news enrichment metrics in the database."""
        try:
            metrics_repo = CompetitorMetricsRepository(session)

            metric = CompetitorMetrics(
                competitor_id=competitor_id,
                metric_type="news_sentiment",
                start_date=datetime.utcnow() - timedelta(days=days_back),
                end_date=datetime.utcnow(),
                metric_date=datetime.utcnow(),
                sentiment_score=sentiment_data.get("score", 0.0),
                mentions_count=article_count,
                confidence_score=sentiment_data.get("confidence", 0.0),
                meta_data={
                    "sentiment_category": sentiment_data.get("category", "neutral"),
                    "sample_size": sentiment_data.get("sample_size", 0),
                    "source": "gnews"
                }
            )

            await metrics_repo.create_metric(metric)
            logger.info(
                f"Stored news enrichment metrics for competitor {competitor_id}"
            )
        except Exception as e:
            logger.error(f"Error storing news metrics: {e}")
            # Don't raise - metrics storage failure shouldn't fail the operation
