"""
Temporal Analysis Service for analyzing content engagement over time
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.models.content import Content, ContentEngagementHistory
from src.models.trend import TrendAnalysis
from src.database.session import get_session
import logging
from fastapi import HTTPException
from src.utils.time import get_time_window
from src.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

class TemporalAnalysisService:
    """Service for analyzing temporal aspects of content"""

    def __init__(
        self,
        decay_factor: float = 0.1,
        max_content_age_days: int = 365,
        trend_window_days: int = 30,
        min_data_points: int = 5
    ):
        """Initialize temporal analysis service"""
        self.decay_factor = decay_factor
        self.max_content_age_days = max_content_age_days
        self.trend_window_days = trend_window_days
        self.min_data_points = min_data_points

    async def calculate_content_decay(self, content_date: datetime) -> float:
        """Calculate content decay score based on age."""
        age_days = (datetime.now() - content_date).days
        if age_days >= self.max_content_age_days:
            return 0.0
        decay_score = np.exp(-self.decay_factor * age_days / self.max_content_age_days)
        return max(0.0, min(1.0, decay_score))

    async def update_content_engagement(
        self,
        session: AsyncSession,
        content_id: int,
        views: int = 0,
        shares: int = 0,
        comments: int = 0,
        likes: int = 0
    ) -> bool:
        """Record new engagement metrics for content."""
        try:
            engagement = ContentEngagementHistory(
                content_id=content_id,
                timestamp=datetime.now(),
                views=views,
                shares=shares,
                comments=comments,
                likes=likes
            )

            session.add(engagement)
            await session.commit()

            # Update trend analysis after new engagement data
            await self.analyze_content_trends(session, content_id)
            return True

        except Exception as e:
            logger.error(f"Error updating content engagement: {str(e)}")
            await session.rollback()
            return False

    async def get_engagement_history(
        self,
        session: AsyncSession,
        content_id: int,
        days: Optional[int] = None
    ) -> List[ContentEngagementHistory]:
        """Get engagement history for content."""
        try:
            query = select(ContentEngagementHistory).where(
                ContentEngagementHistory.content_id == content_id
            )

            if days:
                cutoff_date = datetime.now() - timedelta(days=days)
                query = query.where(ContentEngagementHistory.timestamp >= cutoff_date)

            query = query.order_by(ContentEngagementHistory.timestamp.desc())
            result = await session.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error retrieving engagement history: {str(e)}")
            return []

    async def analyze_content_trends(
        self,
        session: AsyncSession,
        content_id: int
    ) -> Optional[Dict]:
        """Analyze engagement trends for specific content."""
        try:
            # Get recent engagement history
            history = await self.get_engagement_history(
                session,
                content_id,
                days=self.trend_window_days
            )

            if len(history) < self.min_data_points:
                return None

            # Get the content instance
            content = await session.execute(
                select(Content).where(Content.id == content_id)
            )
            content = content.scalar_one_or_none()
            if not content:
                return None

            # Prepare data for analysis
            timestamps = np.array([h.timestamp.timestamp() for h in history])
            metrics = {
                'views': np.array([h.views for h in history]),
                'shares': np.array([h.shares for h in history]),
                'comments': np.array([h.comments for h in history]),
                'likes': np.array([h.likes for h in history])
            }

            # Calculate trends
            trends = {}
            for metric, values in metrics.items():
                slope, score = await self._calculate_trend(timestamps, values)
                trends[metric] = {
                    'slope': float(slope),
                    'confidence': float(score)
                }

            # Store trend analysis results
            trend_analysis = TrendAnalysis(
                trend_type="engagement",
                timestamp=datetime.now(),
                trend_data=trends,
                trend_score=max(
                    trend_info['confidence']
                    for trend_info in trends.values()
                )
            )
            trend_analysis.contents.append(content)

            session.add(trend_analysis)
            await session.commit()

            return trends

        except Exception as e:
            logger.error(f"Error analyzing content trends: {str(e)}")
            await session.rollback()
            return None

    async def _calculate_trend(
        self,
        timestamps: np.ndarray,
        values: np.ndarray
    ) -> Tuple[float, float]:
        """Calculate trend slope and confidence score."""
        try:
            # Normalize time values to [0, 1] range
            t_min, t_max = timestamps.min(), timestamps.max()
            t_norm = (timestamps - t_min) / (t_max - t_min) if t_max > t_min else timestamps

            # Fit linear regression
            coefficients = np.polyfit(t_norm, values, 1)
            slope = coefficients[0]

            # Calculate R-squared score
            y_pred = np.polyval(coefficients, t_norm)
            correlation_matrix = np.corrcoef(values, y_pred)
            r_squared = correlation_matrix[0, 1] ** 2

            return slope, r_squared

        except Exception as e:
            logger.error(f"Error calculating trend: {str(e)}")
            return 0.0, 0.0

    async def get_trending_content(
        self,
        session: AsyncSession,
        min_confidence: float = 0.7,
        limit: int = 10
    ) -> List[Dict]:
        """Get list of trending content based on engagement metrics."""
        try:
            # Get recent trend analyses
            cutoff_date = datetime.now() - timedelta(days=self.trend_window_days)
            query = select(TrendAnalysis).where(
                TrendAnalysis.timestamp >= cutoff_date
            ).order_by(TrendAnalysis.timestamp.desc())

            result = await session.execute(query)
            trend_analyses = result.scalars().all()

            # Filter and sort trending content
            trending = []
            for analysis in trend_analyses:
                # Skip if no trend data or no associated content
                if not analysis.trend_data or not analysis.contents:
                    continue

                # Get confidence scores for each metric
                confidence_scores = [
                    metric['confidence']
                    for metric in analysis.trend_data.values()
                ]

                # Calculate average confidence score
                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                if avg_confidence < min_confidence:
                    continue

                # Get the first associated content (assuming one-to-one for now)
                content = analysis.contents[0]

                # Add to trending list
                trending.append({
                    'content_id': content.id,
                    'title': content.title,
                    'trend_data': analysis.trend_data,
                    'trend_score': analysis.trend_score,
                    'confidence': avg_confidence
                })

            # Sort by trend score and limit results
            trending.sort(key=lambda x: x['trend_score'], reverse=True)
            return trending[:limit]

        except Exception as e:
            logger.error(f"Error getting trending content: {str(e)}")
            return []

    async def detect_realtime_trends(
        self,
        session: AsyncSession,
        time_window_minutes: int = 30,
        min_engagement_threshold: int = 10,
        content_filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Detect real-time trends within a short time window."""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
            
            # Build base query for recent engagement
            query = select(ContentEngagementHistory).where(
                ContentEngagementHistory.timestamp >= cutoff_time
            )
            
            # Apply content filters if provided
            if content_filters:
                query = query.join(Content).where(
                    *(getattr(Content, key) == value 
                      for key, value in content_filters.items())
                )
            
            # Get recent engagement data
            result = await session.execute(query)
            engagements = result.scalars().all()
            
            # Group by content and calculate engagement velocity
            content_velocities = {}
            for engagement in engagements:
                if engagement.content_id not in content_velocities:
                    content_velocities[engagement.content_id] = {
                        'total_engagement': 0,
                        'timestamps': [],
                        'engagement_values': []
                    }
                
                # Calculate total engagement for this data point
                total_engagement = (
                    engagement.views +
                    engagement.shares * 3 +  # Weight shares more heavily
                    engagement.comments * 2 +  # Weight comments more heavily
                    engagement.likes
                )
                
                content_velocities[engagement.content_id]['total_engagement'] += total_engagement
                content_velocities[engagement.content_id]['timestamps'].append(
                    engagement.timestamp.timestamp()
                )
                content_velocities[engagement.content_id]['engagement_values'].append(
                    total_engagement
                )
            
            # Calculate velocity and acceleration for each content
            trending_content = []
            for content_id, data in content_velocities.items():
                if data['total_engagement'] < min_engagement_threshold:
                    continue
                
                if len(data['timestamps']) >= 2:
                    timestamps = np.array(data['timestamps'])
                    values = np.array(data['engagement_values'])
                    
                    # Calculate velocity (engagement rate)
                    velocity = np.diff(values) / np.diff(timestamps)
                    avg_velocity = np.mean(velocity)
                    
                    # Calculate acceleration (change in engagement rate)
                    acceleration = 0.0
                    if len(velocity) >= 2:
                        acceleration = np.mean(np.diff(velocity))
                    
                    # Calculate trending score (negative velocity means decreasing engagement)
                    trending_score = abs(avg_velocity) * (1 + max(0, np.sign(avg_velocity) * acceleration))
                    
                    trending_content.append({
                        'content_id': content_id,
                        'total_engagement': data['total_engagement'],
                        'velocity': float(avg_velocity),
                        'acceleration': float(acceleration),
                        'trending_score': float(trending_score)
                    })
            
            # Sort by trending score
            trending_content.sort(key=lambda x: x['trending_score'], reverse=True)
            return trending_content
            
        except Exception as e:
            logger.error(f"Error detecting real-time trends: {str(e)}")
            return []

    async def filter_content_by_performance(
        self,
        session: AsyncSession,
        performance_metrics: Dict[str, float],
        content_filters: Optional[Dict] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Filter content based on performance metrics and additional criteria."""
        try:
            # Build base query
            query = select(Content)
            
            # Apply content filters
            if content_filters:
                for key, value in content_filters.items():
                    query = query.where(getattr(Content, key) == value)
            
            # Get content
            result = await session.execute(query)
            contents = result.scalars().all()
            
            content_scores = []
            for content in contents:
                # Get recent engagement metrics
                engagement_history = await self.get_engagement_history(
                    session,
                    content.id,
                    days=self.trend_window_days
                )
                
                if not engagement_history:
                    continue
                
                # Calculate performance score based on metrics
                score = 0.0
                latest = engagement_history[0]
                
                if 'view_weight' in performance_metrics:
                    score += latest.views * performance_metrics['view_weight']
                if 'share_weight' in performance_metrics:
                    score += latest.shares * performance_metrics['share_weight']
                if 'comment_weight' in performance_metrics:
                    score += latest.comments * performance_metrics['comment_weight']
                if 'like_weight' in performance_metrics:
                    score += latest.likes * performance_metrics['like_weight']
                
                # Apply time decay
                decay = await self.calculate_content_decay(content.created_at)
                score *= decay
                
                content_scores.append({
                    'content_id': content.id,
                    'title': content.title,
                    'score': score,
                    'metrics': {
                        'views': latest.views,
                        'shares': latest.shares,
                        'comments': latest.comments,
                        'likes': latest.likes
                    },
                    'decay_factor': decay
                })
            
            # Sort by score and return top results
            content_scores.sort(key=lambda x: x['score'], reverse=True)
            return content_scores[:limit]
            
        except Exception as e:
            logger.error(f"Error filtering content by performance: {str(e)}")
            return []

    async def analyze_content_trends_new(
        self,
        content_id: int,
        timeframe: str,
        session: AsyncSession
    ) -> Dict:
        """Analyze trends for specific content over time."""
        content = await self._get_content(content_id, session)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        time_window = get_time_window(timeframe)
        engagement_data = await self._get_engagement_data(content, time_window, session)
        
        trend_analysis = TrendAnalysis(
            trend_type="engagement",
            timestamp=datetime.utcnow(),
            trend_data=engagement_data,
            trend_score=self._calculate_trend_score(engagement_data),
            trend_metadata={
                "timeframe": timeframe,
                "metrics": ["views", "likes", "shares", "comments"]
            }
        )
        
        session.add(trend_analysis)
        await session.flush()
        
        # Create the many-to-many relationship
        content.trends.append(trend_analysis)
        await session.commit()
        
        return {
            "content_id": content_id,
            "trend_analysis": {
                "trend_score": trend_analysis.trend_score,
                "engagement_data": engagement_data
            }
        }

    async def _get_content(self, content_id: int, session: AsyncSession) -> Optional[Content]:
        """Get content by ID."""
        stmt = select(Content).where(Content.id == content_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_engagement_data(
        self,
        content: Content,
        time_window: timedelta,
        session: AsyncSession
    ) -> List[Dict]:
        """Get engagement data for content within time window."""
        stmt = select(ContentEngagementHistory).where(
            ContentEngagementHistory.content_id == content.id,
            ContentEngagementHistory.timestamp >= datetime.utcnow() - time_window
        ).order_by(ContentEngagementHistory.timestamp)
        
        result = await session.execute(stmt)
        engagement_history = result.scalars().all()
        
        return [{
            "timestamp": history.timestamp.isoformat(),
            "views": history.views,
            "likes": history.likes,
            "shares": history.shares,
            "comments": history.comments,
            "engagement_score": history.engagement_score
        } for history in engagement_history]

    def _calculate_trend_score(self, engagement_data: List[Dict]) -> float:
        """Calculate trend score from engagement data."""
        if not engagement_data:
            return 0.0
            
        # Calculate trend score based on engagement metrics
        total_engagement = sum(
            data["engagement_score"]
            for data in engagement_data
        )
        return total_engagement / len(engagement_data)

    async def get_trending_content_new(
        self,
        timeframe: str,
        session: AsyncSession,
        limit: int = 10
    ) -> List[Dict]:
        """Get trending content based on engagement metrics."""
        time_window = get_time_window(timeframe)
        current_time = datetime.utcnow()
        
        # Get content with high engagement in the time window
        stmt = select(Content).join(
            ContentEngagementHistory
        ).where(
            ContentEngagementHistory.timestamp >= current_time - time_window
        ).group_by(
            Content.id
        ).order_by(
            func.sum(ContentEngagementHistory.engagement_score).desc()
        ).limit(limit)
        
        result = await session.execute(stmt)
        trending_content = result.scalars().all()
        
        return [{
            "content_id": content.id,
            "title": content.title,
            "engagement_score": content.engagement_score,
            "trend_score": content.trend_score
        } for content in trending_content]
