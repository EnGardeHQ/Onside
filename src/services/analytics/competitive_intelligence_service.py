from datetime import datetime, timedelta
from typing import List, Dict, Optional
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.models.market import Competitor, CompetitorMetrics
from src.integrations.meltwater import MeltwaterClient
from src.config import Config

class CompetitiveIntelligenceService:
    """Service for gathering and analyzing competitive intelligence data"""

    def __init__(self, config: Config):
        """Initialize the competitive intelligence service"""
        self.meltwater_client = MeltwaterClient(
            api_key=config.meltwater_api_key,
            base_url=config.meltwater_base_url
        )
        self.alert_threshold = config.alert_threshold
        
    async def track_competitor_mentions(
        self,
        session: AsyncSession,
        competitor_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Track mentions and sentiment for a competitor across various sources"""
        competitor = await self._get_competitor(session, competitor_id)
        if not competitor:
            raise ValueError(f"Competitor with id {competitor_id} not found")
            
        # Get mentions from Meltwater
        mentions = await self.meltwater_client.get_mentions(
            search_terms=[competitor.name, competitor.domain],
            start_date=start_date,
            end_date=end_date
        )
        
        # Analyze mentions
        analysis = await self._analyze_mentions(mentions)
        
        # Store results
        await self._store_competitor_metrics(
            session,
            competitor_id,
            analysis,
            start_date,
            end_date
        )
        
        return analysis
        
    async def get_competitor_insights(
        self,
        session: AsyncSession,
        competitor_id: int,
        days: int = 30
    ) -> Dict:
        """Get insights about a competitor's performance and trends"""
        metrics = await self._get_competitor_metrics(session, competitor_id, days)
        
        return {
            "mention_trend": self._calculate_mention_trend(metrics),
            "sentiment_analysis": self._analyze_sentiment_trend(metrics),
            "key_topics": await self._extract_key_topics(metrics),
            "market_position": await self._analyze_market_position(session, competitor_id)
        }
        
    async def set_up_competitor_alerts(
        self,
        session: AsyncSession,
        competitor_id: int,
        alert_config: Dict
    ) -> bool:
        """Configure alerts for significant competitor activities"""
        competitor = await self._get_competitor(session, competitor_id)
        if not competitor:
            raise ValueError(f"Competitor with id {competitor_id} not found")
            
        # Set up Meltwater alerts
        alert_id = await self.meltwater_client.create_alert(
            search_terms=[competitor.name, competitor.domain],
            config=alert_config
        )
        
        # Store alert configuration
        if not competitor.meta_data:
            competitor.meta_data = {}
        competitor.meta_data["alerts"] = {
            "meltwater_alert_id": alert_id,
            "config": alert_config
        }
        await session.commit()
        
        return True
        
    async def _get_competitor(
        self,
        session: AsyncSession,
        competitor_id: int
    ) -> Optional[Competitor]:
        """Get competitor by ID"""
        result = await session.execute(
            select(Competitor).where(Competitor.id == competitor_id)
        )
        return result.scalar_one_or_none()
        
    async def _store_competitor_metrics(
        self,
        session: AsyncSession,
        competitor_id: int,
        analysis: Dict,
        start_date: datetime,
        end_date: datetime
    ) -> None:
        """Store competitor metrics in the database"""
        metrics = CompetitorMetrics(
            competitor_id=competitor_id,
            start_date=start_date,
            end_date=end_date,
            metric_date=datetime.now(),
            metric_type="mention_analysis",
            mentions_count=analysis["total_mentions"],
            sentiment_score=analysis["sentiment_score"],
            engagement_rate=analysis["engagement_rate"],
            meta_data=analysis["details"]
        )
        session.add(metrics)
        await session.commit()
        
    async def _get_competitor_metrics(
        self,
        session: AsyncSession,
        competitor_id: int,
        days: int
    ) -> List[CompetitorMetrics]:
        """Get competitor metrics for the specified time period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        result = await session.execute(
            select(CompetitorMetrics)
            .where(
                CompetitorMetrics.competitor_id == competitor_id,
                CompetitorMetrics.start_date >= cutoff_date
            )
            .order_by(CompetitorMetrics.start_date)
        )
        return result.scalars().all()
        
    def _calculate_mention_trend(self, metrics: List[CompetitorMetrics]) -> Dict:
        """Calculate trend in competitor mentions"""
        if not metrics:
            return {"trend": 0, "confidence": 0}
            
        mentions = [m.mentions_count for m in metrics]
        dates = [m.start_date.timestamp() for m in metrics]
        
        # Calculate trend using linear regression
        slope, intercept = np.polyfit(dates, mentions, 1)
        confidence = np.corrcoef(dates, mentions)[0, 1]
        
        return {
            "trend": slope,
            "confidence": abs(confidence)
        }
        
    def _analyze_sentiment_trend(self, metrics: List[CompetitorMetrics]) -> Dict:
        """Analyze trend in sentiment scores"""
        if not metrics:
            return {"trend": 0, "confidence": 0}
            
        sentiments = [m.sentiment_score for m in metrics]
        dates = [m.start_date.timestamp() for m in metrics]
        
        # Calculate trend using linear regression
        slope, intercept = np.polyfit(dates, sentiments, 1)
        confidence = np.corrcoef(dates, sentiments)[0, 1]
        
        return {
            "trend": slope,
            "confidence": abs(confidence)
        }
        
    async def _extract_key_topics(self, metrics: List[CompetitorMetrics]) -> List[Dict]:
        """Extract key topics from competitor mentions"""
        all_topics = []
        for metric in metrics:
            if "topics" in metric.meta_data:
                all_topics.extend(metric.meta_data["topics"])
                
        # Group and count topics
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
        # Sort by frequency
        sorted_topics = sorted(
            topic_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {"topic": topic, "count": count}
            for topic, count in sorted_topics[:10]
        ]
        
    async def _analyze_market_position(
        self,
        session: AsyncSession,
        competitor_id: int
    ) -> Dict:
        """Analyze competitor's market position"""
        # Get competitor's current market share
        competitor = await self._get_competitor(session, competitor_id)
        if not competitor:
            return {}
            
        # Get recent metrics
        recent_metrics = await self._get_competitor_metrics(
            session,
            competitor_id,
            days=30
        )
        
        return {
            "market_share": competitor.market_share,
            "mention_share": self._calculate_mention_share(recent_metrics),
            "sentiment_position": self._calculate_sentiment_position(recent_metrics)
        }
        
    async def _analyze_mentions(self, mentions: List[Dict]) -> Dict:
        """Analyze mentions to extract insights"""
        if not mentions:
            return {
                "total_mentions": 0,
                "sentiment_score": 0,
                "engagement_rate": 0,
                "details": {
                    "sources": {},
                    "topics": [],
                    "peak_times": []
                }
            }

        # Basic metrics
        total_mentions = len(mentions)
        sentiment_scores = [m["sentiment"] for m in mentions if "sentiment" in m]
        engagement_rates = [m["engagement"] for m in mentions if "engagement" in m]

        # Calculate averages
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        avg_engagement = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0

        # Analyze sources
        sources = {}
        for m in mentions:
            if "source" in m:
                sources[m["source"]] = sources.get(m["source"], 0) + 1

        # Analyze topics
        topics = set()
        for m in mentions:
            if "topics" in m and isinstance(m["topics"], list):
                topics.update(m["topics"])

        # Get peak times
        peak_times = self._analyze_peak_times(mentions)

        return {
            "total_mentions": total_mentions,
            "sentiment_score": avg_sentiment,
            "engagement_rate": avg_engagement,
            "details": {
                "sources": sources,
                "topics": list(topics),
                "peak_times": peak_times
            }
        }
        
    def _analyze_sources(self, mentions: List[Dict]) -> Dict:
        """Analyze distribution of mention sources"""
        sources = {}
        for mention in mentions:
            source = mention.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1
        return sources
        
    def _extract_topics(self, mentions: List[Dict]) -> List[str]:
        """Extract common topics from mentions"""
        topics = []
        for mention in mentions:
            if "topics" in mention:
                topics.extend(mention["topics"])
        return list(set(topics))
        
    def _analyze_peak_times(self, mentions: List[Dict]) -> List[Dict]:
        """Analyze peak times of mentions"""
        # Convert string timestamps to datetime objects if needed
        times = []
        for m in mentions:
            if "timestamp" in m:
                if isinstance(m["timestamp"], str):
                    try:
                        # Assuming ISO format timestamps
                        times.append(datetime.fromisoformat(m["timestamp"].replace('Z', '+00:00')))
                    except ValueError:
                        continue
                else:
                    times.append(m["timestamp"])
        
        if not times:
            return []

        times.sort()

        # Group by hour and find peaks
        hour_counts = {}
        for t in times:
            hour = t.replace(minute=0, second=0, microsecond=0)
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        # Find peak hours (hours with most mentions)
        if not hour_counts:
            return []

        max_mentions = max(hour_counts.values())
        peak_hours = [
            {
                "hour": hour.strftime("%H:00"),
                "count": count,
                "is_peak": count == max_mentions
            }
            for hour, count in sorted(hour_counts.items())
        ]

        return peak_hours

    def _calculate_mention_share(self, metrics: List[CompetitorMetrics]) -> float:
        """Calculate competitor's share of mentions"""
        if not metrics:
            return 0.0
        
        # For now, just return the latest mention count as a percentage
        latest_metric = metrics[-1]
        return latest_metric.mentions_count / 1000  # Assuming 1000 total industry mentions
        
    def _calculate_sentiment_position(self, metrics: List[CompetitorMetrics]) -> float:
        """Calculate competitor's sentiment position"""
        if not metrics:
            return 0.0
        
        # For now, just return the latest sentiment score
        latest_metric = metrics[-1]
        return latest_metric.sentiment_score
