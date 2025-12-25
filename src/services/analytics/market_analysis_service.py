"""
Market Analysis Service for competitor tracking and market insights
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.market import (
    Competitor,
    CompetitorContent,
    CompetitorMetrics,
    MarketSegment,
    MarketTag
)
from src.services.analytics.base_analytics import BaseAnalyticsService
import logging

logger = logging.getLogger(__name__)

class MarketAnalysisService(BaseAnalyticsService):
    """Service for analyzing market and competitor data"""

    def __init__(
        self,
        min_confidence_score: float = 0.7,
        market_share_window_days: int = 90,
        content_freshness_days: int = 30,
        min_data_points: int = 5,
        trend_weights: Optional[Dict[str, float]] = None,
        engagement_weights: Optional[Dict[str, float]] = None
    ):
        """Initialize market analysis service
        
        Args:
            min_confidence_score: Minimum confidence score for metrics
            market_share_window_days: Days to consider for market share
            content_freshness_days: Days to consider content fresh
            min_data_points: Minimum data points for trend analysis
            trend_weights: Weights for different trend metrics (e.g. {'revenue': 2.0, 'traffic': 1.0})
            engagement_weights: Weights for engagement metrics (e.g. {'views': 1.0, 'shares': 3.0})
        """
        self.min_confidence_score = min_confidence_score
        self.market_share_window_days = market_share_window_days
        self.content_freshness_days = content_freshness_days
        self.min_data_points = min_data_points
        self.trend_weights = trend_weights or {
            'revenue': 2.0,
            'market_share': 1.5,
            'traffic': 1.0,
            'engagement': 1.0
        }
        self.engagement_weights = engagement_weights or {
            'shares': 3.0,
            'comments': 2.0,
            'likes': 1.0,
            'views': 1.0
        }

    async def add_competitor(
        self,
        session: AsyncSession,
        name: str,
        domain: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        meta_data: Optional[Dict] = None
    ) -> Optional[Competitor]:
        """Add a new competitor to track"""
        try:
            # Check if competitor already exists
            existing = await session.execute(
                select(Competitor).where(Competitor.domain == domain)
            )
            if existing.scalar_one_or_none():
                logger.warning(f"Competitor with domain {domain} already exists")
                return None

            # Create competitor
            competitor = Competitor(
                name=name,
                domain=domain,
                description=description,
                meta_data=meta_data or {}
            )

            # Add tags
            if tags:
                for tag_name in tags:
                    tag = await self._get_or_create_tag(session, tag_name)
                    competitor.tags.append(tag)

            session.add(competitor)
            await session.commit()
            return competitor

        except Exception as e:
            logger.error(f"Error adding competitor: {str(e)}")
            await session.rollback()
            return None

    async def update_competitor_metrics(
        self,
        session: AsyncSession,
        competitor_id: int,
        metric_type: str,
        value: float,
        confidence_score: float,
        source: str,
        meta_data: Optional[Dict] = None
    ) -> bool:
        """Update competitor performance metrics"""
        try:
            now = datetime.now()
            start_date = now
            end_date = now + timedelta(days=1)  # Default to 1 day duration
            
            # If start_date is provided in meta_data, use it
            if meta_data and 'start_date' in meta_data:
                try:
                    start_date = datetime.fromisoformat(meta_data['start_date'])
                    end_date = start_date + timedelta(days=1)
                except (ValueError, TypeError):
                    logger.warning("Invalid start_date format in meta_data, using current time")
            
            metric = CompetitorMetrics(
                competitor_id=competitor_id,
                metric_date=now,
                start_date=start_date,
                end_date=end_date,
                metric_type=metric_type,
                value=value,
                confidence_score=confidence_score,
                source=source,
                meta_data=meta_data or {}
            )
            
            session.add(metric)
            await session.commit()
            
            # Update market share if metric type is relevant
            if metric_type in ['revenue', 'traffic', 'market_share']:
                await self._update_market_shares(session)
            
            return True

        except Exception as e:
            logger.error(f"Error updating competitor metrics: {str(e)}")
            await session.rollback()
            return False

    async def add_competitor_content(
        self,
        session: AsyncSession,
        competitor_id: int,
        url: str,
        title: str,
        content_type: str,
        publish_date: Optional[datetime] = None,
        engagement_metrics: Optional[Dict] = None,
        content_metrics: Optional[Dict] = None,
        meta_data: Optional[Dict] = None
    ) -> Optional[CompetitorContent]:
        """Add new competitor content item"""
        try:
            # Check if content already exists
            existing = await session.execute(
                select(CompetitorContent).where(CompetitorContent.url == url)
            )
            if existing.scalar_one_or_none():
                logger.warning(f"Content with URL {url} already exists")
                return None

            content = CompetitorContent(
                competitor_id=competitor_id,
                url=url,
                title=title,
                content_type=content_type,
                publish_date=publish_date or datetime.now(),
                engagement_metrics=engagement_metrics or {},
                content_metrics=content_metrics or {},
                meta_data=meta_data or {}
            )
            
            session.add(content)
            await session.commit()
            return content

        except Exception as e:
            logger.error(f"Error adding competitor content: {str(e)}")
            await session.rollback()
            return None

    async def get_market_trends(
        self,
        session: AsyncSession,
        metric_type: str,
        days: int = 30,
        segment_id: Optional[int] = None
    ) -> List[Dict]:
        """Get market trends for specific metrics"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = select(CompetitorMetrics).where(
                CompetitorMetrics.metric_type == metric_type,
                CompetitorMetrics.metric_date >= cutoff_date,
                CompetitorMetrics.confidence_score >= self.min_confidence_score
            )

            if segment_id:
                # Add segment filtering logic here
                pass

            result = await session.execute(query)
            metrics = result.scalars().all()

            # Process metrics into trends
            trends = self._calculate_market_trends(metrics)
            return trends

        except Exception as e:
            logger.error(f"Error getting market trends: {str(e)}")
            return []

    async def get_content_gaps(
        self,
        session: AsyncSession,
        competitor_ids: Optional[List[int]] = None,
        content_type: Optional[str] = None,
        days: int = 90
    ) -> List[Dict]:
        """Identify content gaps based on competitor analysis"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = select(CompetitorContent).where(
                CompetitorContent.publish_date >= cutoff_date
            )

            if competitor_ids:
                query = query.where(CompetitorContent.competitor_id.in_(competitor_ids))
            if content_type:
                query = query.where(CompetitorContent.content_type == content_type)

            result = await session.execute(query)
            content_items = result.scalars().all()

            # Analyze content distribution and identify gaps
            gaps = self._analyze_content_gaps(content_items)
            return gaps

        except Exception as e:
            logger.error(f"Error analyzing content gaps: {str(e)}")
            return []

    async def get_market_shares(self, session: AsyncSession) -> List[Dict]:
        """Calculate market shares with confidence weighting
        
        Returns:
            List of dictionaries containing competitor info and their market shares
        """
        try:
            # Get metrics within window
            window_start = datetime.now() - timedelta(days=self.market_share_window_days)
            
            # Query to get weighted revenue and confidence scores
            query = select(
                CompetitorMetrics.competitor_id,
                (func.sum(CompetitorMetrics.value * CompetitorMetrics.confidence_score)).label('weighted_revenue'),
                func.min(CompetitorMetrics.confidence_score).label('avg_confidence')  # Use min to get base confidence score
            ).where(
                CompetitorMetrics.metric_type == 'revenue',
                CompetitorMetrics.metric_date >= window_start,
                CompetitorMetrics.confidence_score >= self.min_confidence_score
            ).group_by(CompetitorMetrics.competitor_id)
            
            result = await session.execute(query)
            metrics = result.all()
            
            if not metrics:
                return []
                
            # Calculate total weighted revenue
            total_weighted_revenue = sum(m.weighted_revenue for m in metrics)
            
            # Get competitor details and calculate market shares
            market_shares = []
            for metric in metrics:
                competitor = await session.get(Competitor, metric.competitor_id)
                if competitor:
                    market_share = (metric.weighted_revenue / total_weighted_revenue * 100 
                                  if total_weighted_revenue > 0 else 0)
                    
                    market_shares.append({
                        'competitor_id': competitor.id,
                        'name': competitor.name,
                        'market_share': market_share,
                        'confidence_score': metric.avg_confidence
                    })
            
            # Sort by market share descending
            market_shares.sort(key=lambda x: x['market_share'], reverse=True)
            return market_shares
            
        except Exception as e:
            logger.error(f"Error calculating market shares: {str(e)}")
            return []

    async def _update_market_shares(self, session: AsyncSession) -> None:
        """Update market shares for all competitors based on revenue metrics"""
        try:
            market_shares = await self.get_market_shares(session)
            
            # Get all competitor IDs from market shares
            competitor_ids = {ms['competitor_id'] for ms in market_shares}
            
            # Update market shares
            for market_share in market_shares:
                competitor = await session.get(Competitor, market_share['competitor_id'])
                if competitor:
                    competitor.market_share = market_share['market_share']
                    competitor.updated_at = datetime.now()
            
            # Set market share to 0 for competitors not in results
            query = select(Competitor).where(Competitor.id.not_in(competitor_ids))
            result = await session.execute(query)
            other_competitors = result.scalars().all()
            
            for competitor in other_competitors:
                competitor.market_share = 0
                competitor.updated_at = datetime.now()
                
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error updating market shares: {str(e)}")
            await session.rollback()

    async def _get_or_create_tag(
        self,
        session: AsyncSession,
        tag_name: str
    ) -> MarketTag:
        """Get existing tag or create new one"""
        result = await session.execute(
            select(MarketTag).where(MarketTag.name == tag_name)
        )
        tag = result.scalar_one_or_none()
        
        if not tag:
            tag = MarketTag(name=tag_name)
            session.add(tag)
        
        return tag

    def _calculate_market_trends(self, metrics: List[CompetitorMetrics]) -> List[Dict]:
        """Calculate market trends from metrics with weighted scoring"""
        if not metrics or len(metrics) < self.min_data_points:
            return []

        # Group metrics by competitor and type
        competitor_metrics = {}
        for metric in metrics:
            key = (metric.competitor_id, metric.metric_type)
            if key not in competitor_metrics:
                competitor_metrics[key] = []
            competitor_metrics[key].append(metric)

        trends = []
        for (competitor_id, metric_type), competitor_data in competitor_metrics.items():
            if len(competitor_data) < self.min_data_points:
                continue

            # Sort by date
            competitor_data.sort(key=lambda x: x.metric_date)
            
            # Calculate trend with confidence weighting
            dates = np.array([m.metric_date.timestamp() for m in competitor_data])
            values = np.array([m.value * m.confidence_score for m in competitor_data])
            confidence_scores = np.array([m.confidence_score for m in competitor_data])
            
            # Calculate weighted metrics
            weighted_values = values * self.trend_weights.get(metric_type, 1.0)
            weighted_avg = np.average(weighted_values, weights=confidence_scores)
            weighted_std = np.sqrt(np.average((weighted_values - weighted_avg)**2, weights=confidence_scores))
            
            # Calculate velocity and acceleration
            velocity = np.diff(weighted_values) / np.diff(dates)
            avg_velocity = np.mean(velocity)
            
            acceleration = np.diff(velocity) if len(velocity) > 1 else np.array([0])
            avg_acceleration = np.mean(acceleration)
            
            trend = {
                'competitor_id': competitor_id,
                'metric_type': metric_type,
                'start_date': competitor_data[0].metric_date,
                'end_date': competitor_data[-1].metric_date,
                'start_value': values[0],
                'end_value': values[-1],
                'weighted_avg': float(weighted_avg),
                'weighted_std': float(weighted_std),
                'velocity': float(avg_velocity),
                'acceleration': float(avg_acceleration),
                'change_percent': ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0,
                'trend_direction': 'up' if avg_velocity > 0 else 'down',
                'volatility': weighted_std / weighted_avg if weighted_avg != 0 else 0,
                'confidence': float(np.mean(confidence_scores)),
                'trend_score': float(
                    (1 + abs(avg_velocity)) * 
                    (1 + max(0, np.sign(avg_velocity) * avg_acceleration)) * 
                    self.trend_weights.get(metric_type, 1.0)
                )
            }
            
            trends.append(trend)

        return sorted(trends, key=lambda x: x['trend_score'], reverse=True)

    def _analyze_content_gaps(self, content_items: List[CompetitorContent]) -> List[Dict]:
        """Analyze content distribution to identify gaps with engagement velocity"""
        if not content_items:
            return []

        # Group content by type
        content_by_type = {}
        for item in content_items:
            if item.content_type not in content_by_type:
                content_by_type[item.content_type] = []
            content_by_type[item.content_type].append(item)

        gaps = []
        total_content = len(content_items)
        now = datetime.now()
        
        for content_type, items in content_by_type.items():
            type_count = len(items)
            percentage = (type_count / total_content) * 100
            
            # Calculate weighted engagement scores
            engagement_scores = []
            engagement_velocities = []
            
            for item in items:
                if not item.engagement_metrics:
                    continue
                    
                # Calculate weighted engagement score
                weighted_score = sum(
                    value * self.engagement_weights.get(metric, 1.0)
                    for metric, value in item.engagement_metrics.items()
                )
                
                # Calculate engagement velocity (score per day)
                days_since_publish = (now - item.publish_date).days or 1
                velocity = weighted_score / days_since_publish
                
                engagement_scores.append(weighted_score)
                engagement_velocities.append(velocity)
            
            avg_engagement = np.mean(engagement_scores) if engagement_scores else 0
            avg_velocity = np.mean(engagement_velocities) if engagement_velocities else 0
            
            gap = {
                'content_type': content_type,
                'count': type_count,
                'percentage': percentage,
                'avg_engagement': float(avg_engagement),
                'engagement_velocity': float(avg_velocity),
                'weighted_gap_score': float(
                    (10 - percentage) * (1 + avg_velocity)  # Higher score for low percentage + high velocity
                ) if percentage < 10 else 0,
                'is_gap': percentage < 10 and avg_velocity > 0  # Consider it a gap if low percentage but high engagement
            }
            
            gaps.append(gap)

        return sorted(gaps, key=lambda x: x['weighted_gap_score'], reverse=True)
