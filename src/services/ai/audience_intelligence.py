from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import numpy as np
from src.models.user import User
from src.models.content import Content
from src.models.engagement import EngagementMetrics
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from src.database.utils import get_db_session
from sqlalchemy import select

@dataclass
class AudienceSegment:
    id: int
    name: str
    description: str
    size: int
    engagement_score: float
    characteristics: Dict
    created_at: datetime

@dataclass
class EngagementMetrics:
    views: int
    likes: int
    shares: int
    comments: int
    content_id: int

@dataclass
class DemographicProfile:
    metrics: Dict[str, Dict]
    segments: List[Dict]
    insights: List[str]
    updated_at: datetime

@dataclass
class InterestProfile:
    top_interests: List[str]
    interest_clusters: List[Dict]
    interest_scores: Dict[str, float]
    trending_topics: List[str]
    updated_at: datetime

@dataclass
class BehaviorPattern:
    patterns: List[Dict]
    metrics: Dict[str, Dict]
    insights: List[str]
    updated_at: datetime

class AudienceIntelligenceError(Exception):
    pass

class AudienceIntelligenceService:
    def __init__(self):
        # Initialize any ML models or external services here
        pass
        
    async def generate_insights(
        self,
        content_items: List[Content],
        engagement_metrics: List[EngagementMetrics],
        db: Session
    ) -> Dict[str, Any]:
        """Generate comprehensive audience insights from content and engagement data."""
        
        try:
            # Group metrics by content
            content_metrics = self._group_metrics_by_content(content_items, engagement_metrics)
            
            # Analyze engagement patterns
            engagement_patterns = self._analyze_engagement_patterns(content_metrics)
            
            # Analyze content performance
            content_performance = self._analyze_content_performance(content_metrics)
            
            # Identify audience segments
            audience_segments = self._identify_audience_segments(content_metrics)
            
            return {
                "engagement_patterns": engagement_patterns,
                "content_performance": content_performance,
                "audience_segments": audience_segments,
                "key_findings": self._generate_key_findings(
                    engagement_patterns,
                    content_performance,
                    audience_segments
                )
            }
        except Exception as e:
            raise AudienceIntelligenceError(f"Error generating insights: {str(e)}")
    
    async def analyze_trends(
        self,
        content_items: List[Content],
        engagement_metrics: List[EngagementMetrics],
        lookback_days: int,
        db: Session
    ) -> Dict[str, Any]:
        """Analyze audience engagement trends over time."""
        
        try:
            # Group metrics by time periods
            time_periods = self._group_metrics_by_time(
                content_items,
                engagement_metrics,
                lookback_days
            )
            
            # Analyze trend patterns
            trend_patterns = self._analyze_trend_patterns(time_periods)
            
            # Identify emerging trends
            emerging_trends = self._identify_emerging_trends(time_periods)
            
            # Calculate trend confidence
            confidence = self._calculate_trend_confidence(trend_patterns)
            
            return {
                "trend_patterns": trend_patterns,
                "emerging_trends": emerging_trends,
                "confidence": confidence,
                "recommendations": self._generate_trend_recommendations(
                    trend_patterns,
                    emerging_trends
                )
            }
        except Exception as e:
            raise AudienceIntelligenceError(f"Error analyzing trends: {str(e)}")

    def _group_metrics_by_content(
        self,
        content_items: List[Content],
        engagement_metrics: List[EngagementMetrics]
    ) -> Dict[int, Dict[str, Any]]:
        """Group engagement metrics by content ID."""
        content_metrics = {}
        
        for content in content_items:
            metrics = [m for m in engagement_metrics if m.content_id == content.id]
            content_metrics[content.id] = {
                "content": content,
                "metrics": metrics,
                "total_engagement": sum(m.views + m.likes + m.shares + m.comments for m in metrics)
            }
        
        return content_metrics
    
    def _group_metrics_by_time(
        self,
        content_items: List[Content],
        engagement_metrics: List[EngagementMetrics],
        lookback_days: int
    ) -> Dict[str, Dict[str, Any]]:
        """Group metrics by time periods."""
        time_periods = {}
        period_size = timedelta(days=1)  # Daily periods
        
        for content in content_items:
            period_key = content.created_at.strftime("%Y-%m-%d")
            if period_key not in time_periods:
                time_periods[period_key] = {
                    "content": [],
                    "metrics": [],
                    "total_engagement": 0
                }
            
            period_metrics = [m for m in engagement_metrics if m.content_id == content.id]
            time_periods[period_key]["content"].append(content)
            time_periods[period_key]["metrics"].extend(period_metrics)
            time_periods[period_key]["total_engagement"] += sum(m.views + m.likes + m.shares + m.comments for m in period_metrics)
        
        return time_periods
    
    def _analyze_engagement_patterns(
        self,
        content_metrics: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze patterns in audience engagement."""
        patterns = {
            "peak_engagement_times": self._find_peak_engagement_times(content_metrics),
            "content_type_performance": self._analyze_content_type_performance(content_metrics),
            "platform_performance": self._analyze_platform_performance(content_metrics)
        }
        return patterns
    
    def _analyze_content_performance(
        self,
        content_metrics: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze content performance metrics."""
        return {
            "top_performing": self._identify_top_performing(content_metrics),
            "engagement_distribution": self._calculate_engagement_distribution(content_metrics),
            "performance_by_type": self._analyze_performance_by_type(content_metrics)
        }
    
    def _identify_audience_segments(
        self,
        content_metrics: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Identify and analyze audience segments."""
        return {
            "segments": self._cluster_audience_segments(content_metrics),
            "segment_preferences": self._analyze_segment_preferences(content_metrics),
            "engagement_patterns": self._analyze_segment_engagement(content_metrics)
        }
    
    def _generate_key_findings(
        self,
        engagement_patterns: Dict[str, Any],
        content_performance: Dict[str, Any],
        audience_segments: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate key insights and findings from the analysis."""
        findings = []
        
        # Add engagement pattern findings
        findings.extend(self._extract_engagement_findings(engagement_patterns))
        
        # Add content performance findings
        findings.extend(self._extract_performance_findings(content_performance))
        
        # Add audience segment findings
        findings.extend(self._extract_segment_findings(audience_segments))
        
        return findings

    def _find_peak_engagement_times(
        self,
        content_metrics: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Find peak times for audience engagement."""
        peak_times = {
            "daily": {},
            "weekly": {},
            "monthly": {}
        }
        
        for content_id, data in content_metrics.items():
            for metric in data["metrics"]:
                hour = metric.content_id
                day = metric.content_id
                month = metric.content_id
                
                peak_times["daily"][hour] = peak_times["daily"].get(hour, 0) + metric.views + metric.likes + metric.shares + metric.comments
                peak_times["weekly"][day] = peak_times["weekly"].get(day, 0) + metric.views + metric.likes + metric.shares + metric.comments
                peak_times["monthly"][month] = peak_times["monthly"].get(month, 0) + metric.views + metric.likes + metric.shares + metric.comments
        
        # Handle empty metrics
        if not peak_times["daily"]:
            return {
                "daily": None,
                "weekly": None,
                "monthly": None
            }
        
        return {
            "daily": max(peak_times["daily"].items(), key=lambda x: x[1])[0],
            "weekly": max(peak_times["weekly"].items(), key=lambda x: x[1])[0],
            "monthly": max(peak_times["monthly"].items(), key=lambda x: x[1])[0]
        }

    def _analyze_content_type_performance(
        self,
        content_metrics: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze performance by content type."""
        type_performance = {}
        
        for content_id, data in content_metrics.items():
            content_type = data["content"].content_type
            if content_type not in type_performance:
                type_performance[content_type] = {
                    "total_engagement": 0,
                    "count": 0,
                    "avg_engagement": 0
                }
            
            type_performance[content_type]["total_engagement"] += data["total_engagement"]
            type_performance[content_type]["count"] += 1
        
        # Calculate averages
        for content_type in type_performance:
            type_performance[content_type]["avg_engagement"] = (
                type_performance[content_type]["total_engagement"] /
                type_performance[content_type]["count"]
            )
        
        return type_performance

    def _analyze_platform_performance(
        self,
        content_metrics: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze performance across different platforms."""
        platform_performance = {}
        
        for content_id, data in content_metrics.items():
            for metric in data["metrics"]:
                platform = metric.content_id
                if platform not in platform_performance:
                    platform_performance[platform] = {
                        "total_engagement": 0,
                        "metrics": {}
                    }
                
                if metric.content_id not in platform_performance[platform]["metrics"]:
                    platform_performance[platform]["metrics"][metric.content_id] = 0
                
                platform_performance[platform]["total_engagement"] += metric.views + metric.likes + metric.shares + metric.comments
                platform_performance[platform]["metrics"][metric.content_id] += metric.views + metric.likes + metric.shares + metric.comments
        
        return platform_performance

    def _identify_top_performing(
        self,
        content_metrics: Dict[int, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify top performing content."""
        content_list = [
            {
                "content_id": content_id,
                "total_engagement": data["total_engagement"],
                "content_type": data["content"].content_type,
                "created_at": data["content"].created_at
            }
            for content_id, data in content_metrics.items()
        ]
        
        return sorted(
            content_list,
            key=lambda x: x["total_engagement"],
            reverse=True
        )[:5]  # Return top 5

    def _calculate_engagement_distribution(
        self,
        content_metrics: Dict[int, Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate the distribution of engagement metrics."""
        all_engagement = [data["total_engagement"] for data in content_metrics.values()]
        
        if not all_engagement:
            return {
                "mean": 0,
                "median": 0,
                "std_dev": 0
            }
        
        return {
            "mean": float(np.mean(all_engagement)),
            "median": float(np.median(all_engagement)),
            "std_dev": float(np.std(all_engagement))
        }

    def _analyze_performance_by_type(
        self,
        content_metrics: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Analyze performance metrics by content type."""
        type_metrics = {}
        
        for content_id, data in content_metrics.items():
            content_type = data["content"].content_type
            if content_type not in type_metrics:
                type_metrics[content_type] = []
            type_metrics[content_type].append(data["total_engagement"])
        
        return {
            content_type: {
                "mean": float(np.mean(values)),
                "median": float(np.median(values)),
                "std_dev": float(np.std(values))
            }
            for content_type, values in type_metrics.items()
            if values  # Only include types with data
        }

    def _cluster_audience_segments(
        self,
        content_metrics: Dict[int, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Cluster audience into segments based on engagement patterns."""
        # For now, return a simple segmentation based on engagement levels
        engagement_levels = {
            "high": [],
            "medium": [],
            "low": []
        }
        
        all_engagement = [data["total_engagement"] for data in content_metrics.values()]
        if not all_engagement:
            return []
        
        mean_engagement = np.mean(all_engagement)
        std_dev = np.std(all_engagement)
        
        for content_id, data in content_metrics.items():
            if data["total_engagement"] > mean_engagement + std_dev:
                engagement_levels["high"].append(content_id)
            elif data["total_engagement"] < mean_engagement - std_dev:
                engagement_levels["low"].append(content_id)
            else:
                engagement_levels["medium"].append(content_id)
        
        return [
            {
                "name": f"{level}_engagement",
                "size": len(content_ids),
                "content_ids": content_ids
            }
            for level, content_ids in engagement_levels.items()
        ]

    def _analyze_trend_patterns(
        self,
        time_periods: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze patterns in engagement trends."""
        daily_engagement = []
        dates = sorted(time_periods.keys())
        
        for date in dates:
            daily_engagement.append(time_periods[date]["total_engagement"])
        
        if not daily_engagement:
            return {
                "trend": "no_data",
                "growth_rate": 0,
                "volatility": 0
            }
        
        # Calculate trend metrics
        growth_rate = (
            (daily_engagement[-1] - daily_engagement[0]) / daily_engagement[0]
            if daily_engagement[0] != 0 else 0
        )
        volatility = float(np.std(daily_engagement) / np.mean(daily_engagement)) if len(daily_engagement) > 1 else 0
        
        return {
            "trend": "up" if growth_rate > 0.1 else "down" if growth_rate < -0.1 else "stable",
            "growth_rate": growth_rate,
            "volatility": volatility
        }

    def _identify_emerging_trends(
        self,
        time_periods: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify emerging trends in audience behavior."""
        trends = []
        dates = sorted(time_periods.keys())
        
        if len(dates) < 2:
            return trends
        
        # Compare recent performance to historical
        recent_period = time_periods[dates[-1]]
        historical_avg = np.mean([
            time_periods[date]["total_engagement"]
            for date in dates[:-1]
        ])
        
        if recent_period["total_engagement"] > historical_avg * 1.5:
            trends.append({
                "type": "engagement_spike",
                "magnitude": recent_period["total_engagement"] / historical_avg,
                "date": dates[-1]
            })
        
        return trends

    def _calculate_trend_confidence(
        self,
        trend_patterns: Dict[str, Any]
    ) -> float:
        """Calculate confidence in trend analysis."""
        # Simple confidence calculation based on volatility
        if "volatility" not in trend_patterns:
            return 0.5
        
        # Higher volatility = lower confidence
        confidence = 1.0 - min(trend_patterns["volatility"], 1.0)
        return max(0.1, confidence)  # Ensure minimum confidence of 10%

    def _generate_trend_recommendations(
        self,
        trend_patterns: Dict[str, Any],
        emerging_trends: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on trend analysis."""
        recommendations = []
        
        if trend_patterns.get("trend") == "up":
            recommendations.append({
                "type": "capitalize_growth",
                "description": "Engagement is trending upward. Consider increasing content frequency."
            })
        elif trend_patterns.get("trend") == "down":
            recommendations.append({
                "type": "address_decline",
                "description": "Engagement is declining. Review content strategy and audience feedback."
            })
        
        if emerging_trends:
            recommendations.append({
                "type": "leverage_trends",
                "description": "New engagement patterns detected. Adapt content strategy accordingly."
            })
        
        return recommendations

    def _generate_key_findings(
        self,
        engagement_patterns: Dict[str, Any],
        content_performance: Dict[str, Any],
        audience_segments: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate key findings from the analysis."""
        findings = []
        
        # Add findings about peak engagement times
        if "peak_engagement_times" in engagement_patterns:
            findings.append({
                "category": "timing",
                "finding": f"Peak engagement occurs at {engagement_patterns['peak_engagement_times'].get('daily')}:00"
            })
        
        # Add findings about content performance
        if "top_performing" in content_performance:
            top_content = content_performance["top_performing"]
            if top_content:
                findings.append({
                    "category": "content",
                    "finding": f"Top performing content type: {top_content[0]['content_type']}"
                })
        
        return findings

    def _analyze_segment_preferences(
        self,
        content_metrics: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze content preferences for each audience segment."""
        preferences = {}
        
        # Group content by type
        type_metrics = {}
        for content_id, data in content_metrics.items():
            content_type = data["content"].content_type
            if content_type not in type_metrics:
                type_metrics[content_type] = []
            type_metrics[content_type].append(data["total_engagement"])
        
        # Calculate preferences
        for content_type, engagements in type_metrics.items():
            if engagements:
                preferences[content_type] = {
                    "avg_engagement": float(np.mean(engagements)),
                    "popularity": len(engagements),
                    "engagement_trend": "up" if engagements[-1] > np.mean(engagements) else "down"
                }
        
        return preferences

    def _analyze_segment_engagement(
        self,
        content_metrics: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze engagement patterns for each audience segment."""
        patterns = {
            "frequency": self._calculate_engagement_frequency(content_metrics),
            "intensity": self._calculate_engagement_intensity(content_metrics),
            "consistency": self._calculate_engagement_consistency(content_metrics)
        }
        return patterns

    def _calculate_engagement_frequency(
        self,
        content_metrics: Dict[int, Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate how often each segment engages."""
        engagement_counts = {}
        total_content = len(content_metrics)
        
        for content_id, data in content_metrics.items():
            for metric in data["metrics"]:
                metric_type = metric.content_id
                if metric_type not in engagement_counts:
                    engagement_counts[metric_type] = 0
                engagement_counts[metric_type] += 1
        
        return {
            metric_type: count / total_content
            for metric_type, count in engagement_counts.items()
        } if total_content > 0 else {}

    def _calculate_engagement_intensity(
        self,
        content_metrics: Dict[int, Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate the intensity of engagement for each segment."""
        total_engagement = sum(data["total_engagement"] for data in content_metrics.values())
        content_count = len(content_metrics)
        
        if content_count == 0:
            return {"average_intensity": 0.0}
        
        return {
            "average_intensity": total_engagement / content_count
        }

    def _calculate_engagement_consistency(
        self,
        content_metrics: Dict[int, Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate how consistent engagement is over time."""
        engagement_values = [data["total_engagement"] for data in content_metrics.values()]
        
        if not engagement_values:
            return {"consistency_score": 0.0}
        
        mean_engagement = np.mean(engagement_values)
        std_dev = np.std(engagement_values)
        
        # Calculate coefficient of variation (lower means more consistent)
        consistency = 1.0 - (std_dev / mean_engagement if mean_engagement > 0 else 0)
        
        return {
            "consistency_score": max(0.0, min(1.0, consistency))
        }

    def _extract_segment_findings(
        self,
        audience_segments: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Extract key findings about audience segments."""
        findings = []
        
        if "segments" in audience_segments:
            segments = audience_segments["segments"]
            if segments:
                # Add finding about largest segment
                largest_segment = max(segments, key=lambda x: x["size"])
                findings.append({
                    "category": "segments",
                    "finding": f"Largest audience segment: {largest_segment['name']} ({largest_segment['size']} users)"
                })
        
        if "segment_preferences" in audience_segments:
            preferences = audience_segments["segment_preferences"]
            if preferences:
                # Add finding about most popular content type
                most_popular = max(preferences.items(), key=lambda x: x[1]["popularity"])
                findings.append({
                    "category": "preferences",
                    "finding": f"Most popular content type: {most_popular[0]}"
                })
        
        return findings

    async def analyze_audience_demographics(self) -> DemographicProfile:
        """Analyze audience demographics."""
        try:
            async with get_db_session() as session:
                result = await session.execute(select(User))
                users = result.scalars().all()
                if not users:
                    return DemographicProfile(
                        metrics={},
                        segments=[],
                        insights=[],
                        updated_at=datetime.utcnow()
                    )
                
                age_distribution = {}
                location_distribution = {}
                segments = []
                insights = []
                
                for user in users:
                    if hasattr(user, 'metadata') and isinstance(user.metadata, dict):
                        age = user.metadata.get('age')
                        location = user.metadata.get('location')
                        
                        if age:
                            age_group = f"{(age // 10) * 10}-{((age // 10) * 10) + 9}"
                            age_distribution[age_group] = age_distribution.get(age_group, 0) + 1
                        
                        if location:
                            location_distribution[location] = location_distribution.get(location, 0) + 1
                        
                        segments.append({
                            'id': user.id,
                            'age': age,
                            'location': location
                        })
                
                # Generate insights
                if age_distribution:
                    most_common_age = max(age_distribution.items(), key=lambda x: x[1])[0]
                    insights.append(f"Most users are in the {most_common_age} age group")
                
                if location_distribution:
                    most_common_location = max(location_distribution.items(), key=lambda x: x[1])[0]
                    insights.append(f"Largest user base is in {most_common_location}")
                
                return DemographicProfile(
                    metrics={
                        'age_distribution': age_distribution,
                        'location_distribution': location_distribution
                    },
                    segments=segments,
                    insights=insights,
                    updated_at=datetime.utcnow()
                )
        except Exception as e:
            raise AudienceIntelligenceError(f"Error analyzing audience demographics: {str(e)}")

    async def get_audience_segments(self) -> List[Dict]:
        """Get audience segments."""
        try:
            async with get_db_session() as session:
                user_result = await session.execute(select(User))
                users = user_result.scalars().all()
                
                if not users:
                    return []
                
                segments = []
                for user in users:
                    if hasattr(user, 'metadata') and isinstance(user.metadata, dict):
                        segment = {
                            'user_id': user.id,
                            'demographics': {
                                'age': user.metadata.get('age'),
                                'location': user.metadata.get('location')
                            },
                            'interests': user.metadata.get('interests', []),
                            'engagement_level': 'high' if user.metadata.get('engagement_score', 0) > 0.7 else 'low'
                        }
                        segments.append(segment)
                
                return segments
        except Exception as e:
            raise AudienceIntelligenceError(f"Error getting audience segments: {str(e)}")

    async def get_engagement_metrics(self) -> List[EngagementMetrics]:
        """Get engagement metrics."""
        try:
            async with get_db_session() as session:
                result = await session.execute(select(Content))
                content = result.scalars().all()
                
                metrics = []
                for item in content:
                    if hasattr(item, 'metadata') and isinstance(item.metadata, dict) and 'engagement_metrics' in item.metadata:
                        eng_metrics = item.metadata['engagement_metrics']
                        metric = EngagementMetrics(
                            content_id=item.id,
                            views=eng_metrics.get('views', 0),
                            likes=eng_metrics.get('likes', 0),
                            shares=eng_metrics.get('shares', 0),
                            comments=eng_metrics.get('comments', 0)
                        )
                        metrics.append(metric)
                return metrics or []
        except Exception as e:
            raise AudienceIntelligenceError(f"Error getting engagement metrics: {str(e)}")

    async def get_audience_recommendations(self) -> List[Dict]:
        """Get audience recommendations."""
        try:
            async with get_db_session() as session:
                result = await session.execute(select(User))
                users = result.scalars().all()
                
                if not users:
                    return []
                
                recommendations = []
                for user in users:
                    if hasattr(user, 'metadata') and isinstance(user.metadata, dict):
                        interests = user.metadata.get('interests', [])
                        engagement_score = user.metadata.get('engagement_score', 0)
                        
                        if interests and engagement_score > 0.7:
                            recommendations.append({
                                'user_id': user.id,
                                'interests': interests,
                                'engagement_score': engagement_score,
                                'recommendation': 'Consider creating content targeting these interests'
                            })
                
                return recommendations
        except Exception as e:
            raise AudienceIntelligenceError(f"Error getting audience recommendations: {str(e)}")

    async def analyze_audience_interests(self) -> InterestProfile:
        """Analyze audience interests."""
        try:
            async with get_db_session() as session:
                result = await session.execute(select(User))
                users = result.scalars().all()
                if not users:
                    return InterestProfile(
                        top_interests=[],
                        interest_clusters=[],
                        interest_scores={},
                        trending_topics=[],
                        updated_at=datetime.utcnow()
                    )
                
                all_interests = []
                interest_count = {}
                
                for user in users:
                    if hasattr(user, 'metadata') and isinstance(user.metadata, dict) and 'interests' in user.metadata:
                        interests = user.metadata['interests']
                        all_interests.extend(interests)
                        for interest in interests:
                            interest_count[interest] = interest_count.get(interest, 0) + 1
                
                top_interests = sorted(interest_count.items(), key=lambda x: x[1], reverse=True)[:5]
                interest_scores = {interest: count/len(users) for interest, count in interest_count.items()}
                
                # Create interest clusters based on co-occurrence
                interest_clusters = []
                if all_interests:
                    interest_clusters = [
                        {
                            'name': f'Cluster_{i}',
                            'interests': list(set(all_interests[i:i+3]))
                        }
                        for i in range(0, len(all_interests), 3)
                    ][:3]  # Limit to top 3 clusters
                
                # Identify trending topics
                trending_topics = [interest for interest, _ in top_interests[:3]]
                
                return InterestProfile(
                    top_interests=[interest for interest, _ in top_interests],
                    interest_clusters=interest_clusters,
                    interest_scores=interest_scores,
                    trending_topics=trending_topics,
                    updated_at=datetime.utcnow()
                )
        except Exception as e:
            raise AudienceIntelligenceError(f"Error analyzing audience interests: {str(e)}")

    async def analyze_engagement_patterns(self) -> BehaviorPattern:
        try:
            async with get_db_session() as session:
                result = await session.execute(select(Content))
                content = result.scalars().all()
                if not content:
                    return BehaviorPattern(
                        patterns=[],
                        metrics={},
                        insights=[],
                        updated_at=datetime.utcnow()
                    )
                
                patterns = []
                total_views = 0
                total_likes = 0
                total_shares = 0
                insights = []
                
                for item in content:
                    if hasattr(item, 'metadata') and isinstance(item.metadata, dict) and 'engagement_metrics' in item.metadata:
                        metrics = item.metadata['engagement_metrics']
                        total_views += metrics.get('views', 0)
                        total_likes += metrics.get('likes', 0)
                        total_shares += metrics.get('shares', 0)
                        
                        pattern_type = 'high_engagement' if metrics.get('views', 0) > 500 else 'low_engagement'
                        patterns.append({
                            'content_id': item.id,
                            'metrics': metrics,
                            'type': pattern_type
                        })
                        
                        if pattern_type == 'high_engagement':
                            insights.append(f"Content {item.id} shows high engagement with {metrics.get('views', 0)} views")
                
                avg_views = total_views / len(content) if content else 0
                avg_likes = total_likes / len(content) if content else 0
                avg_shares = total_shares / len(content) if content else 0
                
                if avg_views > 1000:
                    insights.append("Overall high view count across content")
                if avg_likes / avg_views > 0.1:
                    insights.append("Strong like-to-view ratio indicating engaged audience")
                
                return BehaviorPattern(
                    patterns=patterns,
                    metrics={
                        'avg_views': avg_views,
                        'avg_likes': avg_likes,
                        'avg_shares': avg_shares
                    },
                    insights=insights,
                    updated_at=datetime.utcnow()
                )
        except Exception as e:
            raise AudienceIntelligenceError(f"Error analyzing engagement patterns: {str(e)}")
