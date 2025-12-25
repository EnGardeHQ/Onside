from datetime import datetime
import numpy as np
from typing import Dict, List, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import pandas as pd
from fastapi import HTTPException
import logging
from src.models.seo import ContentAsset, Subject
from src.services.seo.scoring_service import ScoringService
from src.services.ai.semantic_service import SemanticService
from src.services.seo.trend_service import TrendService

logger = logging.getLogger(__name__)

class EnhancedScoringService(ScoringService):
    def __init__(self):
        super().__init__()
        self.semantic_service = SemanticService()
        self.trend_service = TrendService()
        self.scaler = StandardScaler()
        self._initialize_ml_models()

    def _initialize_ml_models(self):
        """Initialize machine learning models for predictions"""
        self.engagement_model = RandomForestRegressor()
        self.reach_model = RandomForestRegressor()
        self.conversion_model = RandomForestRegressor()
        # Note: In production, these would be loaded from trained model files

    async def calculate_dynamic_weights(self, historical_data: List[Dict]) -> Dict:
        """Calculate dynamic weights based on historical performance"""
        if not historical_data:
            return {
                "ranking": 0.40,
                "visibility": 0.20,
                "social": 0.40
            }

        df = pd.DataFrame(historical_data)
        correlations = df[['ranking', 'visibility', 'social']].corr()['performance']
        total_correlation = correlations.sum()

        return {
            "ranking": max(0.30, min(0.50, correlations['ranking'] / total_correlation)),
            "visibility": max(0.15, min(0.25, correlations['visibility'] / total_correlation)),
            "social": max(0.30, min(0.50, correlations['social'] / total_correlation))
        }

    def calculate_time_decay(self, publish_date: datetime) -> float:
        """Calculate time decay factor for content age"""
        days_old = (datetime.now() - publish_date).days
        half_life = 365  # Content half-life in days
        decay_factor = np.exp(-np.log(2) * days_old / half_life)
        return max(0.1, decay_factor)  # Minimum decay of 0.1

    async def get_industry_benchmarks(self, industry: str) -> Dict:
        """Fetch and calculate industry-specific benchmarks"""
        try:
            raw_data = await self.semrush.get_industry_metrics(industry)
            
            return {
                "volume_percentiles": {
                    "25th": np.percentile(raw_data["volumes"], 25),
                    "50th": np.percentile(raw_data["volumes"], 50),
                    "75th": np.percentile(raw_data["volumes"], 75)
                },
                "engagement_rates": {
                    "low": np.mean(raw_data["engagement_rates"]) - np.std(raw_data["engagement_rates"]),
                    "medium": np.mean(raw_data["engagement_rates"]),
                    "high": np.mean(raw_data["engagement_rates"]) + np.std(raw_data["engagement_rates"])
                },
                "competition_thresholds": {
                    "low": 0.3,
                    "medium": 0.6,
                    "high": 0.9
                }
            }
        except Exception as e:
            logger.error(f"Error fetching industry benchmarks: {str(e)}")
            return None

    async def analyze_semantic_relevance(self, content: str, target_keywords: List[str]) -> Dict:
        """Analyze semantic relevance of content"""
        try:
            semantic_scores = await self.semantic_service.analyze_content(
                content=content,
                keywords=target_keywords
            )

            return {
                "keyword_relevance": semantic_scores["keyword_relevance"],
                "topic_coherence": semantic_scores["topic_coherence"],
                "intent_alignment": semantic_scores["intent_alignment"],
                "content_depth": semantic_scores["content_depth"]
            }
        except Exception as e:
            logger.error(f"Error in semantic analysis: {str(e)}")
            return None

    async def analyze_competitive_landscape(self, subject: Subject) -> Dict:
        """Analyze competitive landscape and identify opportunities"""
        try:
            competitors = await self.semrush.get_competitors(subject.name)
            competitor_content = await self.semrush.get_competitor_content(competitors)
            
            content_gaps = self._identify_content_gaps(competitor_content)
            market_saturation = self._calculate_market_saturation(competitor_content)
            competitor_strategies = self._analyze_competitor_patterns(competitor_content)

            return {
                "content_gaps": content_gaps,
                "market_saturation": market_saturation,
                "competitor_strategies": competitor_strategies,
                "opportunity_score": self._calculate_opportunity_score(
                    content_gaps,
                    market_saturation,
                    competitor_strategies
                )
            }
        except Exception as e:
            logger.error(f"Error analyzing competitive landscape: {str(e)}")
            return None

    async def predict_performance(self, features: Dict) -> Dict:
        """Predict future content performance"""
        try:
            feature_vector = self._prepare_features(features)
            
            return {
                "expected_engagement": float(self.engagement_model.predict([feature_vector])[0]),
                "potential_reach": float(self.reach_model.predict([feature_vector])[0]),
                "conversion_probability": float(self.conversion_model.predict([feature_vector])[0])
            }
        except Exception as e:
            logger.error(f"Error predicting performance: {str(e)}")
            return None

    async def calculate_cross_channel_impact(self, content_asset: ContentAsset) -> Dict:
        """Calculate impact across different channels"""
        channels = ["organic_search", "social", "email", "referral"]
        impact_scores = {}

        for channel in channels:
            try:
                channel_metrics = await self._get_channel_metrics(content_asset, channel)
                impact_scores[channel] = self._calculate_channel_score(channel_metrics)
            except Exception as e:
                logger.error(f"Error calculating {channel} impact: {str(e)}")
                impact_scores[channel] = None

        return {
            "channel_scores": impact_scores,
            "overall_impact": self._aggregate_channel_scores(impact_scores)
        }

    async def adjust_for_trends(self, score: float, topic: str) -> float:
        """Adjust scores based on trend data"""
        try:
            trend_data = await self.trend_service.get_trend_data(topic)
            
            trend_factors = {
                "seasonality": self._calculate_seasonality_impact(trend_data),
                "growth_rate": self._calculate_trend_growth(trend_data),
                "momentum": self._calculate_momentum_score(trend_data)
            }
            
            adjustment_factor = sum(trend_factors.values()) / len(trend_factors)
            return score * (1 + adjustment_factor)
        except Exception as e:
            logger.error(f"Error adjusting for trends: {str(e)}")
            return score

    async def calculate_enhanced_score(self, content_asset: ContentAsset) -> Dict:
        """Calculate enhanced content score with all factors"""
        try:
            # Base scores
            base_likeability = await self.calculate_likeability_index(content_asset)
            base_opportunity = await self.calculate_opportunity_index(
                content_asset.subject,
                content_asset.subtopic
            )

            # Enhanced metrics
            semantic_scores = await self.analyze_semantic_relevance(
                content_asset.content,
                content_asset.target_keywords
            )
            competitive_data = await self.analyze_competitive_landscape(content_asset.subject)
            cross_channel_impact = await self.calculate_cross_channel_impact(content_asset)
            
            # Time decay
            time_factor = self.calculate_time_decay(content_asset.publish_date)
            
            # Trend adjustment
            trend_adjusted = await self.adjust_for_trends(base_opportunity, content_asset.topic)
            
            # Industry normalization
            industry_benchmarks = await self.get_industry_benchmarks(content_asset.industry)
            
            # Future predictions
            predictions = await self.predict_performance({
                "base_scores": {
                    "likeability": base_likeability,
                    "opportunity": base_opportunity
                },
                "semantic_scores": semantic_scores,
                "competitive_data": competitive_data,
                "cross_channel_impact": cross_channel_impact,
                "time_factor": time_factor,
                "trend_adjusted": trend_adjusted,
                "industry_benchmarks": industry_benchmarks
            })

            return {
                "overall_score": self._calculate_final_score({
                    "base_likeability": base_likeability,
                    "semantic_scores": semantic_scores,
                    "competitive_data": competitive_data,
                    "cross_channel_impact": cross_channel_impact,
                    "time_factor": time_factor,
                    "trend_adjusted": trend_adjusted,
                    "industry_benchmarks": industry_benchmarks
                }),
                "component_scores": {
                    "likeability": base_likeability,
                    "semantic": semantic_scores,
                    "competitive": competitive_data,
                    "channel_impact": cross_channel_impact,
                    "trend_adjustment": trend_adjusted
                },
                "predictions": predictions,
                "metadata": {
                    "industry_benchmarks": industry_benchmarks,
                    "time_decay": time_factor,
                    "last_updated": datetime.now().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error calculating enhanced score: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating enhanced score: {str(e)}"
            )
