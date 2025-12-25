from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime
import logging
from fastapi import HTTPException
from src.models.seo import ContentAsset, Subject
from src.services.ai.semantic_service import SemanticService
from src.services.seo.trend_service import TrendService
from src.services.analytics.google_analytics import GoogleAnalyticsService
from src.services.analytics.adobe_analytics import AdobeAnalyticsService
from src.services.analytics import AnalyticsService

logger = logging.getLogger(__name__)

class EngagementIndexService:
    def __init__(self):
        """Initialize the EngagementIndexService"""
        self.weights = {
            "search_relevance": 0.25,
            "popularity": 0.2,
            "seo_performance": 0.15,
            "social_engagement": 0.15,
            "video_engagement": 0.1,
            "podcast_engagement": 0.1,
            "image_quality": 0.05
        }
        
        # Initialize analytics services
        self.analytics_service = AnalyticsService()
        self.ga_service = GoogleAnalyticsService()
        self.adobe_service = AdobeAnalyticsService()
        self.trend_service = TrendService()

    async def calculate_engagement_index(self, content_asset: ContentAsset,
                                      market: str,
                                      persona: Dict) -> Dict:
        """Calculate the Contrend Engagement Index (EI)"""
        if not content_asset:
            raise ValueError("Content asset cannot be None")

        if not market:
            raise ValueError("Market cannot be None")

        if not persona:
            raise ValueError("Persona cannot be None")

        try:
            # 1. Collect multi-source engagement data
            search_scores = await self._get_search_engine_signals(content_asset)
            popularity_scores = await self._get_popularity_signals(content_asset)
            seo_scores = await self._get_seo_performance(content_asset)
            social_scores = await self._get_social_engagement(content_asset)
            video_scores = await self._get_video_engagement(content_asset)
            podcast_scores = await self._get_podcast_engagement(content_asset)
            image_scores = await self._analyze_image_quality(content_asset)

            # 2. Apply market population index adjustment
            market_adjustment = await self._get_market_population_index(market)

            # 3. Calculate weighted scores
            weighted_scores = {
                "search_relevance": search_scores * self.weights["search_relevance"],
                "popularity": popularity_scores * self.weights["popularity"],
                "seo_performance": seo_scores * self.weights["seo_performance"],
                "social_engagement": min(social_scores * self.weights["social_engagement"], 0.08),
                "video_engagement": video_scores * self.weights["video_engagement"],
                "podcast_engagement": podcast_scores * self.weights["podcast_engagement"],
                "image_quality": image_scores * self.weights["image_quality"]
            }

            # 4. Calculate base EI score
            base_ei = sum(weighted_scores.values()) * market_adjustment

            # 5. Apply persona-specific adjustments
            persona_adjusted_ei = await self._adjust_for_persona(base_ei, persona)

            # 6. Get content classifications
            classifications = await self._classify_content(content_asset)

            # 7. Calculate business impact
            business_impact = await self._calculate_business_impact(
                content_asset,
                persona_adjusted_ei
            )

            return {
                "engagement_index": round(persona_adjusted_ei, 2),
                "component_scores": weighted_scores,
                "classifications": classifications,
                "business_impact": business_impact,
                "metadata": {
                    "market": market,
                    "persona": persona,
                    "timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error calculating engagement index: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating engagement index: {str(e)}"
            )

    async def _get_search_engine_signals(self, content_asset: ContentAsset) -> float:
        """Get relevance scores from multiple search engines"""
        engines = ["google", "naver", "yahoo", "baidu", "bing", "alexa"]
        scores = []
        
        for engine in engines:
            try:
                score = await self._fetch_search_engine_score(engine, content_asset)
                scores.append(score)
            except Exception as e:
                logger.warning(f"Error getting {engine} score: {str(e)}")
                
        return np.mean(scores) if scores else 0.0

    async def _get_popularity_signals(self, content_asset: ContentAsset) -> float:
        """Get popularity scores from search engines"""
        try:
            google_news = await self._fetch_google_news_score(content_asset)
            semrush = await self._fetch_semrush_popularity(content_asset)
            return np.mean([google_news, semrush])
        except Exception as e:
            logger.error(f"Error getting popularity signals: {str(e)}")
            return 0.0

    async def _get_seo_performance(self, content_asset: ContentAsset) -> float:
        """Get SEO performance metrics for the content asset"""
        try:
            # Get SEO metrics from various sources
            seo_metrics = {
                "keyword_density": await self._analyze_keyword_density(content_asset),
                "meta_score": await self._analyze_meta_tags(content_asset),
                "backlink_score": await self._get_backlink_score(content_asset),
                "load_time": await self._get_page_load_time(content_asset),
                "mobile_friendly": await self._check_mobile_friendly(content_asset)
            }
            
            # Calculate weighted average
            weights = {
                "keyword_density": 0.2,
                "meta_score": 0.2,
                "backlink_score": 0.3,
                "load_time": 0.15,
                "mobile_friendly": 0.15
            }
            
            seo_score = sum(score * weights[metric] for metric, score in seo_metrics.items())
            return min(seo_score, 100.0)
            
        except Exception as e:
            logger.error(f"Error getting SEO performance: {str(e)}")
            return 0.0

    async def _fetch_search_engine_score(self, engine: str, content_asset: ContentAsset) -> float:
        """Fetch search engine ranking score for the content asset"""
        try:
            # Mock scores for different search engines
            mock_scores = {
                "google": 85.0,
                "bing": 80.0,
                "yahoo": 75.0,
                "baidu": 70.0,
                "naver": 65.0,
                "alexa": 60.0
            }
            return mock_scores.get(engine.lower(), 0.0)
        except Exception as e:
            logger.error(f"Error fetching {engine} score: {str(e)}")
            return 0.0

    async def _fetch_google_news_score(self, content_asset: ContentAsset) -> float:
        """Fetch Google News popularity score for the content asset"""
        try:
            # Mock Google News score
            return 75.0
        except Exception as e:
            logger.error(f"Error fetching Google News score: {str(e)}")
            return 0.0

    async def _classify_content(self, content_asset: ContentAsset) -> Dict:
        """Classify content based on various attributes"""
        try:
            return {
                "content_type": content_asset.content_type,
                "primary_topic": content_asset.topic,
                "target_audience": content_asset.persona.get("type", "Unknown"),
                "industry_focus": content_asset.persona.get("industry", "General"),
                "complexity_level": await self._assess_content_complexity(content_asset),
                "content_quality": await self._assess_content_quality(content_asset)
            }
        except Exception as e:
            logger.error(f"Error classifying content: {str(e)}")
            return {}

    async def calculate_opportunity_index(self, content_asset: ContentAsset,
                                       competitor_data: Dict,
                                       landscape_data: Dict) -> Dict:
        """Calculate the Opportunity Index (OI)"""
        try:
            # 1. Compare EI scores
            client_ei = await self.calculate_engagement_index(
                content_asset,
                content_asset.market,
                content_asset.persona
            )
            
            ei_comparison = {
                "client_ei": client_ei["engagement_index"],
                "competitor_ei": np.mean(competitor_data["ei_scores"]),
                "landscape_ei": np.mean(landscape_data["ei_scores"])
            }

            # 2. Calculate content volume metrics
            volume_metrics = self._calculate_volume_metrics(
                content_asset,
                competitor_data,
                landscape_data
            )

            # 3. Analyze trends
            trend_analysis = await self.trend_service.get_trend_data(content_asset.topic)

            # 4. Calculate OI score
            oi_score = self._calculate_oi_score(
                ei_comparison,
                volume_metrics,
                trend_analysis
            )

            return {
                "opportunity_index": round(oi_score, 2),
                "recommendations": await self._generate_recommendations(
                    content_asset,
                    ei_comparison,
                    volume_metrics,
                    trend_analysis
                ),
                "metrics": {
                    "ei_comparison": ei_comparison,
                    "volume_metrics": volume_metrics,
                    "trend_analysis": trend_analysis
                }
            }

        except Exception as e:
            logger.error(f"Error calculating opportunity index: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating opportunity index: {str(e)}"
            )

    async def _calculate_business_impact(self, content_asset: ContentAsset, ei_score: float) -> Dict:
        """Calculate business impact metrics"""
        try:
            # Get analytics data
            analytics = await self.analytics_service.get_content_metrics(content_asset.url)

            # Project future metrics
            projected_visitors = await self._project_visitors(ei_score, analytics)
            projected_conversions = await self._project_conversions(projected_visitors, analytics)
            projected_revenue = await self._project_revenue(projected_conversions, analytics)

            return {
                "projected_visitors": projected_visitors,
                "projected_conversions": projected_conversions,
                "projected_revenue": projected_revenue,
                "roi_estimate": await self._calculate_roi(projected_revenue, content_asset),
                "impact_score": await self._calculate_impact_score(
                    ei_score,
                    projected_visitors,
                    projected_conversions,
                    projected_revenue
                )
            }
        except Exception as e:
            logger.error(f"Error calculating business impact: {str(e)}")
            return {}

    async def _get_market_population_index(self, market: str) -> float:
        """Get market population index adjustment"""
        try:
            # Mock market population indices
            market_indices = {
                "US": 1.0,  # Base market
                "UK": 0.8,
                "JP": 0.9,
                "DE": 0.85,
                "FR": 0.75,
                "AU": 0.7,
                "CA": 0.75,
                "IN": 0.95
            }
            return market_indices.get(market, 0.7)  # Default to 0.7 for unknown markets
        except Exception as e:
            logger.error(f"Error getting market population index: {str(e)}")
            return 1.0

    async def _adjust_for_persona(self, base_ei: float, persona: Dict) -> float:
        """Apply persona-specific adjustments to the EI score"""
        try:
            # Define adjustment factors for different persona types
            type_adjustments = {
                "Technical Professional": 1.1,
                "Business Executive": 0.9,
                "Marketing Manager": 1.0,
                "Content Creator": 1.05,
                "Sales Professional": 0.95
            }

            # Define adjustment factors for different industries
            industry_adjustments = {
                "Technology": 1.1,
                "Finance": 0.95,
                "Healthcare": 1.0,
                "Retail": 0.9,
                "Manufacturing": 0.85
            }

            # Get adjustments based on persona attributes
            type_adj = type_adjustments.get(persona.get("type", ""), 1.0)
            industry_adj = industry_adjustments.get(persona.get("industry", ""), 1.0)

            # Apply adjustments
            adjusted_ei = base_ei * type_adj * industry_adj

            return min(100.0, max(0.0, adjusted_ei))
        except Exception as e:
            logger.error(f"Error adjusting for persona: {str(e)}")
            return base_ei

    async def _assess_content_complexity(self, content_asset: ContentAsset) -> str:
        """Assess content complexity level"""
        try:
            # Mock complexity assessment
            return "Intermediate"
        except Exception as e:
            logger.error(f"Error assessing content complexity: {str(e)}")
            return "Unknown"

    async def _assess_content_quality(self, content_asset: ContentAsset) -> str:
        """Assess content quality level"""
        try:
            # Mock quality assessment
            return "High"
        except Exception as e:
            logger.error(f"Error assessing content quality: {str(e)}")
            return "Unknown"

    async def _project_conversions(self, visitors: int, analytics: Dict) -> int:
        """Project number of conversions based on visitors"""
        try:
            # Mock conversion rate of 2%
            return int(visitors * 0.02)
        except Exception as e:
            logger.error(f"Error projecting conversions: {str(e)}")
            return 0

    async def _project_revenue(self, conversions: int, analytics: Dict) -> float:
        """Project revenue based on conversions"""
        try:
            # Mock average revenue per conversion of $100
            return conversions * 100.0
        except Exception as e:
            logger.error(f"Error projecting revenue: {str(e)}")
            return 0.0

    async def _calculate_roi(self, projected_revenue: float, content_asset: ContentAsset) -> float:
        """Calculate ROI estimate"""
        try:
            # Mock production cost of $1000 per content asset
            production_cost = 1000.0
            roi = (projected_revenue - production_cost) / production_cost
            return max(0.0, roi)
        except Exception as e:
            logger.error(f"Error calculating ROI: {str(e)}")
            return 0.0

    async def _calculate_impact_score(self, ei_score: float,
                                    visitors: int,
                                    conversions: int,
                                    revenue: float) -> float:
        """Calculate overall business impact score"""
        try:
            # Normalize metrics
            normalized_ei = ei_score / 100.0
            normalized_visitors = min(visitors / 10000.0, 1.0)
            normalized_conversions = min(conversions / 200.0, 1.0)
            normalized_revenue = min(revenue / 20000.0, 1.0)

            # Calculate weighted score
            weights = {
                "ei": 0.3,
                "visitors": 0.2,
                "conversions": 0.25,
                "revenue": 0.25
            }

            impact_score = (
                normalized_ei * weights["ei"] +
                normalized_visitors * weights["visitors"] +
                normalized_conversions * weights["conversions"] +
                normalized_revenue * weights["revenue"]
            ) * 100.0

            return max(0.0, min(100.0, impact_score))
        except Exception as e:
            logger.error(f"Error calculating impact score: {str(e)}")
            return 0.0

    async def _get_social_engagement(self, content_asset: ContentAsset) -> float:
        """Get social engagement metrics for the content asset"""
        try:
            # Get social metrics from various platforms
            social_metrics = {
                "facebook": await self._get_facebook_engagement(content_asset),
                "twitter": await self._get_twitter_engagement(content_asset),
                "linkedin": await self._get_linkedin_engagement(content_asset),
                "instagram": await self._get_instagram_engagement(content_asset)
            }
            
            # Calculate weighted average
            weights = {
                "facebook": 0.3,
                "twitter": 0.2,
                "linkedin": 0.3,
                "instagram": 0.2
            }
            
            social_score = sum(score * weights[platform] for platform, score in social_metrics.items())
            return min(social_score, 100.0)
            
        except Exception as e:
            logger.error(f"Error getting social engagement: {str(e)}")
            return 0.0

    async def _get_video_engagement(self, content_asset: ContentAsset) -> float:
        """Get video engagement metrics for the content asset"""
        try:
            # Get video metrics from various platforms
            video_metrics = {
                "youtube": await self._get_youtube_engagement(content_asset),
                "vimeo": await self._get_vimeo_engagement(content_asset),
                "tiktok": await self._get_tiktok_engagement(content_asset)
            }
            
            # Calculate weighted average
            weights = {
                "youtube": 0.5,
                "vimeo": 0.3,
                "tiktok": 0.2
            }
            
            video_score = sum(score * weights[platform] for platform, score in video_metrics.items())
            return min(video_score, 100.0)
            
        except Exception as e:
            logger.error(f"Error getting video engagement: {str(e)}")
            return 0.0

    async def _get_podcast_engagement(self, content_asset: ContentAsset) -> float:
        """Get podcast engagement metrics for the content asset"""
        try:
            # Get podcast metrics from various platforms
            podcast_metrics = {
                "spotify": await self._get_spotify_engagement(content_asset),
                "apple": await self._get_apple_podcasts_engagement(content_asset),
                "google": await self._get_google_podcasts_engagement(content_asset)
            }
            
            # Calculate weighted average
            weights = {
                "spotify": 0.4,
                "apple": 0.4,
                "google": 0.2
            }
            
            podcast_score = sum(score * weights[platform] for platform, score in podcast_metrics.items())
            return min(podcast_score, 100.0)
            
        except Exception as e:
            logger.error(f"Error getting podcast engagement: {str(e)}")
            return 0.0

    async def _analyze_image_quality(self, content_asset: ContentAsset) -> float:
        """Analyze image quality metrics for the content asset"""
        try:
            # Get image quality metrics
            image_metrics = {
                "resolution": await self._check_image_resolution(content_asset),
                "format": await self._check_image_format(content_asset),
                "size": await self._check_image_size(content_asset),
                "alt_text": await self._check_alt_text(content_asset)
            }
            
            # Calculate weighted average
            weights = {
                "resolution": 0.3,
                "format": 0.2,
                "size": 0.2,
                "alt_text": 0.3
            }
            
            image_score = sum(score * weights[metric] for metric, score in image_metrics.items())
            return min(image_score, 100.0)
            
        except Exception as e:
            logger.error(f"Error analyzing image quality: {str(e)}")
            return 0.0

    async def _get_facebook_engagement(self, content_asset: ContentAsset) -> float:
        return 85.0

    async def _get_twitter_engagement(self, content_asset: ContentAsset) -> float:
        return 80.0

    async def _get_linkedin_engagement(self, content_asset: ContentAsset) -> float:
        return 90.0

    async def _get_instagram_engagement(self, content_asset: ContentAsset) -> float:
        return 75.0

    async def _get_youtube_engagement(self, content_asset: ContentAsset) -> float:
        return 85.0

    async def _get_vimeo_engagement(self, content_asset: ContentAsset) -> float:
        return 70.0

    async def _get_tiktok_engagement(self, content_asset: ContentAsset) -> float:
        return 65.0

    async def _get_spotify_engagement(self, content_asset: ContentAsset) -> float:
        return 80.0

    async def _get_apple_podcasts_engagement(self, content_asset: ContentAsset) -> float:
        return 75.0

    async def _get_google_podcasts_engagement(self, content_asset: ContentAsset) -> float:
        return 70.0

    async def _check_image_resolution(self, content_asset: ContentAsset) -> float:
        return 90.0

    async def _check_image_format(self, content_asset: ContentAsset) -> float:
        return 85.0

    async def _check_image_size(self, content_asset: ContentAsset) -> float:
        return 80.0

    async def _check_alt_text(self, content_asset: ContentAsset) -> float:
        return 95.0

    async def _project_visitors(self, ei_score: float, analytics: Dict) -> int:
        """Project number of visitors based on engagement index score"""
        try:
            # Mock projection calculation
            base_visitors = 1000
            multiplier = ei_score / 50.0  # Higher EI means more projected visitors
            return int(base_visitors * multiplier)
        except Exception as e:
            logger.error(f"Error projecting visitors: {str(e)}")
            return 0

    def _calculate_volume_metrics(self, content_asset: ContentAsset,
                                competitor_data: Dict,
                                landscape_data: Dict) -> Dict:
        """Calculate content volume metrics"""
        try:
            return {
                "competitor_volume": competitor_data["content_volume"],
                "landscape_volume": landscape_data["content_volume"],
                "volume_gap": landscape_data["content_volume"] - competitor_data["content_volume"],
                "volume_opportunity": (landscape_data["content_volume"] - competitor_data["content_volume"]) / landscape_data["content_volume"]
            }
        except Exception as e:
            logger.error(f"Error calculating volume metrics: {str(e)}")
            return {}

    def _calculate_oi_score(self, ei_comparison: Dict,
                           volume_metrics: Dict,
                           trend_analysis: Dict) -> float:
        """Calculate Opportunity Index score"""
        try:
            # Mock OI calculation
            ei_weight = 0.4
            volume_weight = 0.3
            trend_weight = 0.3

            ei_score = (ei_comparison["landscape_ei"] - ei_comparison["client_ei"]) / 100.0
            volume_score = volume_metrics["volume_opportunity"]
            trend_score = trend_analysis.get("growth_rate", 0.0) / 100.0

            oi_score = (
                ei_score * ei_weight +
                volume_score * volume_weight +
                trend_score * trend_weight
            ) * 100.0

            return max(0.0, min(100.0, oi_score))
        except Exception as e:
            logger.error(f"Error calculating OI score: {str(e)}")
            return 0.0

    async def _generate_recommendations(self, content_asset: ContentAsset,
                                     ei_comparison: Dict,
                                     volume_metrics: Dict,
                                     trend_analysis: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        try:
            recommendations = []

            # Add recommendations based on EI comparison
            if ei_comparison["client_ei"] < ei_comparison["competitor_ei"]:
                recommendations.append("Improve content quality to match competitor standards")

            # Add recommendations based on volume metrics
            if volume_metrics["volume_opportunity"] > 0.3:
                recommendations.append("Increase content production to capture market share")

            # Add recommendations based on trends
            if trend_analysis.get("growth_rate", 0.0) > 50:
                recommendations.append("Focus on trending topics in your content strategy")

            return recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
