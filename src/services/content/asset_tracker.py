import logging
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from src.models.seo import ContentAsset, Subject
from src.services.seo.semrush_service import SemrushService
from src.services.seo.serp_service import SerpService

logger = logging.getLogger(__name__)

class ContentAssetTracker:
    def __init__(self, semrush_service: SemrushService, serp_service: SerpService):
        self.semrush_service = semrush_service
        self.serp_service = serp_service

    async def track_content_asset(
        self,
        db: Session,
        subject_id: int,
        url: str,
        topic: str,
        style: str,
        format: str
    ) -> ContentAsset:
        """
        Track a new content asset and analyze its performance
        """
        try:
            # Check if subject exists
            subject = db.query(Subject).filter(Subject.id == subject_id).first()
            if not subject:
                raise HTTPException(status_code=404, detail="Subject not found")

            # Create content asset
            content_asset = ContentAsset(
                subject_id=subject_id,
                url=url,
                topic=topic,
                style=style,
                format=format,
                social_engagement={}  # Will be updated by social media service
            )
            
            db.add(content_asset)
            await db.commit()
            await db.refresh(content_asset)

            # Track initial rankings
            rankings = await self.serp_service.track_content_rankings(
                db,
                content_asset.id,
                location="United States"  # Make this configurable
            )

            return content_asset

        except Exception as e:
            logger.error(f"Error tracking content asset: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error tracking content asset: {str(e)}"
            )

    async def update_content_metrics(
        self,
        db: Session,
        content_asset_id: int
    ) -> ContentAsset:
        """
        Update metrics for an existing content asset
        """
        try:
            content_asset = db.query(ContentAsset).filter(
                ContentAsset.id == content_asset_id
            ).first()
            
            if not content_asset:
                raise HTTPException(status_code=404, detail="Content asset not found")

            # Update rankings
            rankings = await self.serp_service.track_content_rankings(
                db,
                content_asset.id
            )

            # Calculate likeability score
            likeability_score = await self._calculate_likeability_score(
                content_asset,
                rankings
            )
            
            content_asset.likeability_score = likeability_score
            await db.commit()
            
            return content_asset

        except Exception as e:
            logger.error(f"Error updating content metrics: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error updating content metrics: {str(e)}"
            )

    async def _calculate_likeability_score(
        self,
        content_asset: ContentAsset,
        rankings: Dict[str, Optional[int]]
    ) -> float:
        """
        Calculate likeability score based on rankings and engagement
        Score ranges from 0-100
        """
        # Weights for different factors
        RANKING_WEIGHT = 0.4
        SOCIAL_WEIGHT = 0.6
        
        # Calculate ranking score (0-100)
        valid_rankings = [r for r in rankings.values() if r is not None]
        if valid_rankings:
            avg_ranking = sum(valid_rankings) / len(valid_rankings)
            ranking_score = max(0, 100 - (avg_ranking * 2))  # Position 1 = 98, Position 50 = 0
        else:
            ranking_score = 0
        
        # Calculate social score (0-100)
        social_metrics = content_asset.social_engagement or {}
        total_engagement = sum(social_metrics.values())
        social_score = min(100, total_engagement / 100)  # 10000 engagements = 100 score
        
        # Calculate final score
        final_score = (ranking_score * RANKING_WEIGHT) + (social_score * SOCIAL_WEIGHT)
        
        return round(final_score, 2)

    async def get_competitor_content(
        self,
        db: Session,
        subject_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get top performing competitor content for a subject
        """
        try:
            subject = db.query(Subject).filter(Subject.id == subject_id).first()
            if not subject:
                raise HTTPException(status_code=404, detail="Subject not found")

            # Get competitor analysis from SEMRush
            competitor_data = await self.semrush_service.get_competitors(subject.name)
            
            competitor_content = []
            for competitor in competitor_data[:limit]:
                # Get top content from each competitor
                domain = competitor.get("domain")
                if domain:
                    domain_data = await self.semrush_service.analyze_domain(domain)
                    top_pages = domain_data.get("top_pages", [])
                    
                    for page in top_pages:
                        competitor_content.append({
                            "url": page.get("url"),
                            "domain": domain,
                            "traffic": page.get("traffic"),
                            "keywords": page.get("keywords"),
                            "ranking": page.get("ranking")
                        })
            
            # Sort by traffic
            competitor_content.sort(key=lambda x: x.get("traffic", 0), reverse=True)
            
            return competitor_content[:limit]

        except Exception as e:
            logger.error(f"Error getting competitor content: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting competitor content: {str(e)}"
            )

    async def get_metrics(self, url: str) -> Dict:
        """
        Get metrics for a content URL
        """
        try:
            # Get domain analytics
            domain = url.split('/')[2]  # Extract domain from URL
            domain_analytics = await self.semrush_service.analyze_domain(domain)
            
            # Get SERP data
            serp_data = await self.serp_service.analyze_serp([url])
            
            return {
                "domain_analytics": domain_analytics,
                "serp_data": serp_data,
                "url": url
            }

        except Exception as e:
            logger.error(f"Error getting content metrics: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting content metrics: {str(e)}"
            )
