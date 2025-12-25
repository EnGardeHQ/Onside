from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import numpy as np
from src.models.user import User
from src.models.content import Content
from src.models.engagement import EngagementMetrics
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from src.database.utils import get_db_session
from sqlalchemy import select

class RecommendationType(Enum):
    SIMILAR = "similar"
    PERSONALIZED = "personalized"
    TRENDING = "trending"

@dataclass
class RecommendationScore:
    content_id: int
    score: float
    confidence: float
    metadata: Dict

@dataclass
class ContentSimilarity:
    content_id: int
    score: float
    similarity_type: str
    metadata: Dict

class ContentRecommendationService:
    def __init__(self):
        self.model_version = "1.0.0"
        # Initialize ML models and recommendation engines here
        pass
    
    async def generate_recommendations(
        self,
        historical_content: List[Content],
        engagement_metrics: List[EngagementMetrics],
        target_platform: Optional[str],
        target_audience: Optional[str],
        count: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Generate content recommendations based on historical performance."""
        
        # Analyze historical performance
        performance_data = self._analyze_historical_performance(
            historical_content,
            engagement_metrics
        )
        
        # Generate content ideas
        content_ideas = self._generate_content_ideas(
            performance_data,
            target_platform,
            target_audience,
            count
        )
        
        # Score and rank recommendations
        ranked_recommendations = self._rank_recommendations(
            content_ideas,
            performance_data,
            target_platform,
            target_audience
        )
        
        # Add timing suggestions
        recommendations = self._add_timing_suggestions(
            ranked_recommendations,
            performance_data,
            target_platform
        )
        
        return recommendations[:count]
    
    async def predict_engagement(
        self,
        recommendation: Dict[str, Any],
        platform: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        """Predict engagement metrics for a content recommendation."""
        
        # Generate predictions for various metrics
        predictions = {
            "engagement_rate": self._predict_engagement_rate(recommendation, platform),
            "reach": self._predict_reach(recommendation, platform),
            "conversion_rate": self._predict_conversion_rate(recommendation, platform),
            "virality_score": self._predict_virality(recommendation, platform)
        }
        
        # Add confidence scores
        predictions["confidence_scores"] = {
            metric: self._calculate_prediction_confidence(value, metric)
            for metric, value in predictions.items()
        }
        
        return predictions
    
    def get_model_version(self) -> str:
        """Get the current model version."""
        return self.model_version
    
    async def get_similar_content(self, content_id: int) -> List[ContentSimilarity]:
        """Get similar content based on content similarity."""
        if content_id < 0:
            raise ValueError("Content ID must be positive")
            
        async with get_db_session() as session:
            result = await session.execute(select(Content))
            similar_content = result.scalars().all()
            if not similar_content:
                return []
            
            similarities = []
            for content in similar_content:
                if content.id != content_id and content.metadata:
                    similarities.append(ContentSimilarity(
                        content_id=content_id,
                        score=0.8,  # Mock score, in real app would use NLP
                        similarity_type="category",
                        metadata=content.metadata
                    ))
            return similarities

    async def get_personalized_recommendations(self, user_id: int) -> List[RecommendationScore]:
        """Get personalized recommendations for a user."""
        if user_id < 0:
            raise ValueError("User ID must be positive")
            
        async with get_db_session() as session:
            result = await session.execute(select(Content))
            recommended_content = result.scalars().all()
            if not recommended_content:
                return []
            
            recommendations = []
            for content in recommended_content:
                if content.metadata:
                    recommendations.append(RecommendationScore(
                        content_id=content.id,
                        score=0.9,  # Mock score, in real app would use ML model
                        confidence=0.8,
                        metadata=content.metadata
                    ))
            return recommendations

    async def get_trending_content(self) -> List[RecommendationScore]:
        """Get trending content."""
        async with get_db_session() as session:
            result = await session.execute(select(Content))
            trending_content = result.scalars().all()
            if not trending_content:
                return []
            
            recommendations = []
            for content in trending_content:
                if content.metadata and 'engagement_score' in content.metadata:
                    recommendations.append(RecommendationScore(
                        content_id=content.id,
                        score=content.metadata['engagement_score'],
                        confidence=0.8,
                        metadata=content.metadata
                    ))
            return recommendations

    async def get_recommendations_by_type(self, user_id: int, recommendation_type: RecommendationType) -> List[RecommendationScore]:
        """Get recommendations by specific type."""
        if user_id < 0:
            raise ValueError("User ID must be positive")
            
        async with get_db_session() as session:
            result = await session.execute(select(Content))
            content_items = result.scalars().all()
            if not content_items:
                return []
            
            recommendations = []
            for content in content_items:
                if content.metadata:
                    recommendations.append(RecommendationScore(
                        content_id=content.id,
                        score=0.85,  # Mock score, in real app would use specific scoring logic
                        confidence=0.8,
                        metadata=content.metadata
                    ))
            return recommendations
    
    def _analyze_historical_performance(
        self,
        historical_content: List[Content],
        engagement_metrics: List[EngagementMetrics]
    ) -> Dict[str, Any]:
        """Analyze historical content performance patterns."""
        
        # Group metrics by content
        content_metrics = {}
        for content in historical_content:
            metrics = [m for m in engagement_metrics if m.content_id == content.id]
            content_metrics[content.id] = {
                "content": content,
                "metrics": metrics,
                "total_engagement": sum(m.value for m in metrics)
            }
        
        return {
            "content_metrics": content_metrics,
            "performance_patterns": self._extract_performance_patterns(content_metrics),
            "audience_preferences": self._analyze_audience_preferences(content_metrics),
            "timing_patterns": self._analyze_timing_patterns(content_metrics)
        }
    
    def _generate_content_ideas(
        self,
        performance_data: Dict[str, Any],
        target_platform: Optional[str],
        target_audience: Optional[str],
        count: int
    ) -> List[Dict[str, Any]]:
        """Generate content ideas based on performance data."""
        
        # Extract successful patterns
        patterns = performance_data["performance_patterns"]
        preferences = performance_data["audience_preferences"]
        
        # Generate ideas based on patterns
        ideas = []
        
        # Add ideas based on top-performing content types
        ideas.extend(self._generate_type_based_ideas(patterns, preferences))
        
        # Add ideas based on audience preferences
        ideas.extend(self._generate_audience_based_ideas(preferences, target_audience))
        
        # Add ideas based on platform-specific patterns
        if target_platform:
            ideas.extend(self._generate_platform_specific_ideas(patterns, target_platform))
        
        return ideas
    
    def _rank_recommendations(
        self,
        content_ideas: List[Dict[str, Any]],
        performance_data: Dict[str, Any],
        target_platform: Optional[str],
        target_audience: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Score and rank content recommendations."""
        
        ranked_ideas = []
        for idea in content_ideas:
            # Calculate various scores
            engagement_score = self._calculate_engagement_potential(
                idea,
                performance_data,
                target_platform
            )
            
            audience_fit_score = self._calculate_audience_fit(
                idea,
                performance_data,
                target_audience
            )
            
            platform_fit_score = self._calculate_platform_fit(
                idea,
                performance_data,
                target_platform
            )
            
            # Combine scores
            total_score = (
                engagement_score * 0.4 +
                audience_fit_score * 0.3 +
                platform_fit_score * 0.3
            )
            
            ranked_ideas.append({
                **idea,
                "scores": {
                    "engagement_potential": engagement_score,
                    "audience_fit": audience_fit_score,
                    "platform_fit": platform_fit_score,
                    "total_score": total_score
                }
            })
        
        # Sort by total score
        return sorted(
            ranked_ideas,
            key=lambda x: x["scores"]["total_score"],
            reverse=True
        )
    
    def _add_timing_suggestions(
        self,
        recommendations: List[Dict[str, Any]],
        performance_data: Dict[str, Any],
        target_platform: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Add posting time suggestions to recommendations."""
        
        timing_patterns = performance_data["timing_patterns"]
        
        for rec in recommendations:
            rec["suggested_timing"] = self._get_optimal_timing(
                rec,
                timing_patterns,
                target_platform
            )
        
        return recommendations

    def _extract_performance_patterns(self, content_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patterns from historical content performance."""
        if not content_metrics:
            return {
                "top_content_types": [],
                "engagement_trends": {},
                "platform_performance": {}
            }
        
        patterns = {
            "top_content_types": [],
            "engagement_trends": {},
            "platform_performance": {}
        }
        
        # Analyze content types
        content_type_performance = {}
        for content_data in content_metrics.values():
            content_type = content_data["content"].content_type
            if content_type not in content_type_performance:
                content_type_performance[content_type] = []
            content_type_performance[content_type].append(content_data["total_engagement"])
        
        # Calculate average performance by content type
        for content_type, engagements in content_type_performance.items():
            avg_engagement = sum(engagements) / len(engagements)
            patterns["top_content_types"].append({
                "type": content_type,
                "avg_engagement": avg_engagement
            })
        
        # Sort by average engagement
        patterns["top_content_types"].sort(key=lambda x: x["avg_engagement"], reverse=True)
        
        return patterns

    def _analyze_audience_preferences(self, content_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze audience preferences from content performance."""
        if not content_metrics:
            return {
                "preferred_topics": [],
                "content_preferences": {},
                "engagement_patterns": {}
            }
        
        preferences = {
            "preferred_topics": [],
            "content_preferences": {},
            "engagement_patterns": {}
        }
        
        # Analyze content metadata for topics
        topic_engagement = {}
        for content_data in content_metrics.values():
            metadata = content_data["content"].content_metadata
            if "topics" in metadata:
                for topic in metadata["topics"]:
                    if topic not in topic_engagement:
                        topic_engagement[topic] = []
                    topic_engagement[topic].append(content_data["total_engagement"])
        
        # Calculate average engagement by topic
        for topic, engagements in topic_engagement.items():
            avg_engagement = sum(engagements) / len(engagements)
            preferences["preferred_topics"].append({
                "topic": topic,
                "avg_engagement": avg_engagement
            })
        
        # Sort by average engagement
        preferences["preferred_topics"].sort(key=lambda x: x["avg_engagement"], reverse=True)
        
        return preferences

    def _analyze_timing_patterns(self, content_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze timing patterns in content performance."""
        if not content_metrics:
            return {
                "best_days": [],
                "best_times": [],
                "seasonal_trends": {}
            }
        
        patterns = {
            "best_days": [],
            "best_times": [],
            "seasonal_trends": {}
        }
        
        # Analyze posting times
        day_performance = {}
        hour_performance = {}
        for content_data in content_metrics.values():
            created_at = content_data["content"].created_at
            day = created_at.strftime("%A")
            hour = created_at.hour
            
            if day not in day_performance:
                day_performance[day] = []
            day_performance[day].append(content_data["total_engagement"])
            
            if hour not in hour_performance:
                hour_performance[hour] = []
            hour_performance[hour].append(content_data["total_engagement"])
        
        # Calculate average performance by day
        for day, engagements in day_performance.items():
            avg_engagement = sum(engagements) / len(engagements)
            patterns["best_days"].append({
                "day": day,
                "avg_engagement": avg_engagement
            })
        
        # Calculate average performance by hour
        for hour, engagements in hour_performance.items():
            avg_engagement = sum(engagements) / len(engagements)
            patterns["best_times"].append({
                "hour": hour,
                "avg_engagement": avg_engagement
            })
        
        # Sort by average engagement
        patterns["best_days"].sort(key=lambda x: x["avg_engagement"], reverse=True)
        patterns["best_times"].sort(key=lambda x: x["avg_engagement"], reverse=True)
        
        return patterns

    def _generate_type_based_ideas(self, patterns: Dict[str, Any], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate content ideas based on successful content types."""
        ideas = []
        
        for content_type in patterns["top_content_types"]:
            idea = {
                "content_type": content_type["type"],
                "suggested_topics": preferences["preferred_topics"][:3],
                "engagement_potential": content_type["avg_engagement"]
            }
            ideas.append(idea)
        
        return ideas

    def _generate_audience_based_ideas(self, preferences: Dict[str, Any], target_audience: Optional[str]) -> List[Dict[str, Any]]:
        """Generate content ideas based on audience preferences."""
        ideas = []
        
        for topic in preferences["preferred_topics"]:
            idea = {
                "topic": topic["topic"],
                "target_audience": target_audience,
                "engagement_potential": topic["avg_engagement"]
            }
            ideas.append(idea)
        
        return ideas

    def _generate_platform_specific_ideas(self, patterns: Dict[str, Any], target_platform: str) -> List[Dict[str, Any]]:
        """Generate platform-specific content ideas."""
        ideas = []
        
        platform_patterns = patterns.get("platform_performance", {}).get(target_platform, {})
        if platform_patterns:
            for content_type in platform_patterns.get("successful_types", []):
                idea = {
                    "platform": target_platform,
                    "content_type": content_type,
                    "suggested_format": platform_patterns.get("preferred_format")
                }
                ideas.append(idea)
        
        return ideas

    def _calculate_engagement_potential(self, idea: Dict[str, Any], performance_data: Dict[str, Any], target_platform: Optional[str]) -> float:
        """Calculate potential engagement score for a content idea."""
        base_score = 0.5  # Default score
        
        # Adjust based on historical performance
        if "engagement_potential" in idea:
            base_score = min(1.0, idea["engagement_potential"] / 1000)  # Normalize to 0-1
        
        # Adjust for platform fit if specified
        if target_platform and "platform" in idea:
            if idea["platform"] == target_platform:
                base_score *= 1.2  # Boost score for platform-specific content
        
        return min(1.0, base_score)

    def _calculate_audience_fit(self, idea: Dict[str, Any], performance_data: Dict[str, Any], target_audience: Optional[str]) -> float:
        """Calculate how well the content idea fits the target audience."""
        base_score = 0.5  # Default score
        
        if target_audience and "target_audience" in idea:
            if idea["target_audience"] == target_audience:
                base_score = 0.8  # High score for matching audience
        
        # Adjust based on topic preferences if available
        if "topic" in idea:
            for pref_topic in performance_data["audience_preferences"]["preferred_topics"]:
                if pref_topic["topic"] == idea["topic"]:
                    base_score *= 1.2  # Boost score for preferred topics
        
        return min(1.0, base_score)

    def _calculate_platform_fit(self, idea: Dict[str, Any], performance_data: Dict[str, Any], target_platform: Optional[str]) -> float:
        """Calculate how well the content idea fits the target platform."""
        base_score = 0.5  # Default score
        
        if target_platform and "platform" in idea:
            if idea["platform"] == target_platform:
                base_score = 0.8  # High score for matching platform
        
        # Adjust based on content type suitability
        if "content_type" in idea and target_platform:
            platform_patterns = performance_data["performance_patterns"].get("platform_performance", {}).get(target_platform, {})
            if idea["content_type"] in platform_patterns.get("successful_types", []):
                base_score *= 1.2  # Boost score for successful content types
        
        return min(1.0, base_score)

    def _get_optimal_timing(self, recommendation: Dict[str, Any], timing_patterns: Dict[str, Any], platform: Optional[str]) -> Dict[str, Any]:
        """Get optimal posting time for a recommendation."""
        if not timing_patterns["best_days"] or not timing_patterns["best_times"]:
            return {
                "best_day": None,
                "best_time": None,
                "confidence": 0.0
            }
        
        best_day = timing_patterns["best_days"][0]["day"]
        best_time = timing_patterns["best_times"][0]["hour"]
        
        return {
            "best_day": best_day,
            "best_time": best_time,
            "confidence": 0.8  # High confidence when based on actual data
        }

    def _predict_engagement_rate(self, recommendation: Dict[str, Any], platform: Optional[str]) -> float:
        """Predict engagement rate for a recommendation."""
        base_rate = 0.05  # 5% base engagement rate
        
        # Adjust based on content type
        if "content_type" in recommendation:
            content_type_multipliers = {
                "video": 1.5,
                "image": 1.3,
                "article": 1.0,
                "link": 0.8
            }
            base_rate *= content_type_multipliers.get(recommendation["content_type"], 1.0)
        
        # Adjust based on platform
        if platform:
            platform_multipliers = {
                "instagram": 1.4,
                "twitter": 1.2,
                "facebook": 1.0,
                "linkedin": 0.9
            }
            base_rate *= platform_multipliers.get(platform, 1.0)
        
        return min(1.0, base_rate)

    def _predict_reach(self, recommendation: Dict[str, Any], platform: Optional[str]) -> int:
        """Predict reach for a recommendation."""
        base_reach = 1000  # Base reach
        
        # Adjust based on platform
        if platform:
            platform_multipliers = {
                "facebook": 2.0,
                "instagram": 1.8,
                "twitter": 1.5,
                "linkedin": 1.2
            }
            base_reach *= platform_multipliers.get(platform, 1.0)
        
        return int(base_reach)

    def _predict_conversion_rate(self, recommendation: Dict[str, Any], platform: Optional[str]) -> float:
        """Predict conversion rate for a recommendation."""
        base_rate = 0.02  # 2% base conversion rate
        
        # Adjust based on content type
        if "content_type" in recommendation:
            content_type_multipliers = {
                "video": 1.3,
                "article": 1.2,
                "image": 1.0,
                "link": 0.9
            }
            base_rate *= content_type_multipliers.get(recommendation["content_type"], 1.0)
        
        return min(0.1, base_rate)  # Cap at 10%

    def _predict_virality(self, recommendation: Dict[str, Any], platform: Optional[str]) -> float:
        """Predict virality score for a recommendation."""
        base_score = 0.3  # Base virality score
        
        # Adjust based on content type
        if "content_type" in recommendation:
            content_type_multipliers = {
                "video": 1.5,
                "image": 1.3,
                "article": 1.0,
                "link": 0.8
            }
            base_score *= content_type_multipliers.get(recommendation["content_type"], 1.0)
        
        return min(1.0, base_score)

    def _calculate_prediction_confidence(self, value: float, metric: str) -> float:
        """Calculate confidence score for a prediction."""
        # Base confidence levels for different metrics
        base_confidences = {
            "engagement_rate": 0.7,
            "reach": 0.6,
            "conversion_rate": 0.5,
            "virality_score": 0.4
        }
        
        return base_confidences.get(metric, 0.5)
