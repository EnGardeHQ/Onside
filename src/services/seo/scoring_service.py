import logging
from typing import Dict, List, Optional
import numpy as np
from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.models.seo import Subject, Subtopic, ContentAsset
from src.services.seo.semrush_service import SemrushService
from src.services.seo.serp_service import SerpService

logger = logging.getLogger(__name__)

class ScoringService:
    def __init__(self, semrush_service: Optional[SemrushService] = None, serp_service: Optional[SerpService] = None):
        self.semrush = semrush_service or SemrushService()
        self.serp = serp_service or SerpService()

    async def calculate_likeability_index(self, content_asset: ContentAsset) -> float:
        """
        Calculate Likeability Index based on:
        - Google ranking (40%)
        - Google Search visibility (20%)
        - Social Likes (15%)
        - Social Shares (15%)
        - LinkedIn engagement (10%)
        
        Scale: 0-100 points
        """
        try:
            # Get SERP data
            serp_data = await self.serp.analyze_serp([content_asset.url])
            google_ranking = serp_data.get("position", 100)
            search_visibility = serp_data.get("visibility", 0)

            # Extract social metrics
            social_metrics = content_asset.social_engagement or {}
            likes = social_metrics.get("likes", 0)
            shares = social_metrics.get("shares", 0)
            linkedin_engagement = social_metrics.get("linkedin", 0)

            # Calculate component scores (0-100 scale)
            ranking_score = max(0, 100 - google_ranking)  # Lower ranking = higher score
            visibility_score = min(100, search_visibility * 100)
            likes_score = min(100, (likes / 1000) * 100)  # Normalize to 100
            shares_score = min(100, (shares / 500) * 100)  # Normalize to 100
            linkedin_score = min(100, (linkedin_engagement / 200) * 100)  # Normalize to 100
            
            # Apply weights
            weights = {
                "ranking": 0.40,
                "visibility": 0.20,
                "likes": 0.15,
                "shares": 0.15,
                "linkedin": 0.10
            }
            
            likeability_score = (
                ranking_score * weights["ranking"] +
                visibility_score * weights["visibility"] +
                likes_score * weights["likes"] +
                shares_score * weights["shares"] +
                linkedin_score * weights["linkedin"]
            )
            
            return round(likeability_score, 2)

        except Exception as e:
            logger.error(f"Error calculating likeability index: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating likeability index: {str(e)}"
            )

    async def calculate_opportunity_index(self, subject: Subject, subtopic: Subtopic) -> float:
        """
        Calculate Opportunity Potential Index (OPI) using the enhanced formula:
        OPI = (I' + α) / (C' + β + 1)
        
        where:
        I' = normalized interest score
        C' = normalized competition level
        α = 1 (sensitivity constant)
        β = 1 (competition adjustment constant)
        """
        try:
            # Get keyword data
            keyword_data = await self.semrush.get_keyword_data(subtopic.name)
            
            # Calculate Interest Score (I)
            search_volume = subtopic.search_volume or keyword_data.get("search_volume", 0)
            engagement = keyword_data.get("engagement", 0)
            interest_score = np.log1p(search_volume) + engagement
            
            # Calculate Competition Level (C)
            competition = subtopic.competition or keyword_data.get("competition", 1.0)
            content_saturation = keyword_data.get("content_saturation", 0)
            competition_score = (competition + content_saturation) / 2
            
            # Normalize scores using z-score
            def normalize(value, mean, std):
                return (value - mean) / (std if std > 0 else 1)
            
            # Get mean and std from historical data or use reasonable defaults
            i_mean, i_std = 5.0, 2.0  # These should be calculated from historical data
            c_mean, c_std = 0.5, 0.2  # These should be calculated from historical data
            
            i_normalized = normalize(interest_score, i_mean, i_std)
            c_normalized = normalize(competition_score, c_mean, c_std)
            
            # Calculate enhanced OPI
            alpha = 1
            beta = 1
            opi = (i_normalized + alpha) / (c_normalized + beta + 1)
            
            # Scale to 0-100 range with adjusted scaling
            scaled_opi = min(100, max(0, opi * 25 + 25))  # Adjusted scaling factor
            
            return round(scaled_opi, 2)

        except Exception as e:
            logger.error(f"Error calculating opportunity index: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating opportunity index: {str(e)}"
            )

    async def calculate_niche_potential(self, subject: Subject) -> float:
        """
        Calculate Niche Potential Index (NPI) using the formula:
        NPI = I² / (C + 1)²
        
        where:
        I = Interest Score
        C = Competition Level
        """
        try:
            # Get market data
            market_data = await self.semrush.analyze_topic(subject.name)
            
            # Calculate Interest Score (I)
            topics = market_data.get("topics", [])
            total_volume = sum(topic.get("search_volume", 0) for topic in topics)
            avg_engagement = np.mean([topic.get("engagement", 0) for topic in topics])
            
            # Use log scale for volume to prevent domination by large numbers
            interest_score = (np.log1p(total_volume) / 10) + avg_engagement
            
            # Calculate Competition Level (C)
            competitors = await self.semrush.get_competitors(subject.name)
            competition_level = len(competitors) / 100  # Normalize by max expected competitors
            content_density = np.mean([topic.get("competition", 0) for topic in topics])
            
            # Weight competition level more heavily
            competition_score = (competition_level * 0.7 + content_density * 0.3)
            
            # Calculate NPI with adjusted formula for better scaling
            npi = (interest_score ** 2) / ((competition_score * 2 + 1) ** 2)
            
            # Scale to 0-100 range with more conservative scaling
            scaled_npi = min(100, max(0, npi * 5))  # Reduced scaling factor
            
            return round(scaled_npi, 2)

        except Exception as e:
            logger.error(f"Error calculating niche potential: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating niche potential: {str(e)}"
            )

    async def segment_market(self, subject: Subject) -> Dict:
        """
        Perform market segmentation into four categories:
        1. Client and competitors
        2. Other competitors and consultancies
        3. Government - Associations and Institutions
        4. Publisher and Independent websites
        """
        try:
            # Get topic and competitor data
            topic_data = await self.semrush.analyze_topic(subject.name)
            competitor_data = await self.semrush.get_competitors(subject.name)
            
            # Initialize segment buckets
            segments = {
                "client_competitors": [],
                "other_competitors": [],
                "government_institutions": [],
                "publishers_independent": []
            }
            
            # Helper function to classify domain type
            def classify_domain(domain: str) -> str:
                if domain in competitor_data:
                    return "client_competitors"
                elif domain.endswith((".gov", ".edu", ".org")):
                    return "government_institutions"
                elif any(x in domain for x in ["news", "blog", "media", "press"]):
                    return "publishers_independent"
                else:
                    return "other_competitors"
            
            for topic in topic_data.get("topics", []):
                domain = topic.get("domain", "")
                segment = classify_domain(domain)
                
                # Calculate engagement score
                engagement_score = (
                    topic.get("search_volume", 0) * 0.4 +
                    topic.get("social_signals", 0) * 0.6
                )
                
                segments[segment].append({
                    "domain": domain,
                    "topic": topic.get("topic", ""),
                    "engagement_score": engagement_score
                })
            
            # Sort each segment by engagement score
            for segment in segments:
                segments[segment] = sorted(
                    segments[segment],
                    key=lambda x: x["engagement_score"],
                    reverse=True
                )[:200]  # Top 200 per segment
            
            return segments

        except Exception as e:
            logger.error(f"Error performing market segmentation: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error performing market segmentation: {str(e)}"
            )

    async def analyze_content_by_dimension(self, content_assets: List[ContentAsset], dimension: str) -> Dict:
        """
        Analyze content assets by dimension (Topic, Style, or Format) and calculate
        likeability scores for each category.
        """
        try:
            if dimension not in ["topic", "style", "format"]:
                raise ValueError(f"Invalid dimension: {dimension}")

            dimension_scores = {}
            
            for asset in content_assets:
                # Get the dimension value (topic, style, or format)
                if dimension == "topic":
                    category = asset.topic
                elif dimension == "style":
                    category = asset.style
                elif dimension == "format":
                    category = asset.format
                
                # Calculate likeability score for the asset
                score = await self.calculate_likeability_index(asset)
                
                # Add to dimension scores
                if category not in dimension_scores:
                    dimension_scores[category] = {
                        "total_score": 0,
                        "count": 0,
                        "assets": []
                    }
                
                dimension_scores[category]["total_score"] += score
                dimension_scores[category]["count"] += 1
                dimension_scores[category]["assets"].append({
                    "url": asset.url,
                    "score": score
                })
            
            # Calculate average scores and sort assets
            for category in dimension_scores:
                avg_score = (
                    dimension_scores[category]["total_score"] /
                    dimension_scores[category]["count"]
                )
                dimension_scores[category]["average_score"] = round(avg_score, 2)
                dimension_scores[category]["assets"].sort(
                    key=lambda x: x["score"],
                    reverse=True
                )
            
            return dimension_scores

        except ValueError as e:
            # Re-raise ValueError for invalid dimensions
            raise e
        except Exception as e:
            logger.error(f"Error analyzing content by dimension: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing content by dimension: {str(e)}"
            )
