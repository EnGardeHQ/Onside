"""Engagement extraction service for analyzing content engagement."""
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import numpy as np
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func
from bs4 import BeautifulSoup

from src.models.link import Link, LinkSnapshot
from src.models.domain import Domain
from src.models.competitor_metrics import CompetitorMetrics
from src.config import settings

logger = logging.getLogger(__name__)

class EngagementExtractionService:
    """Service for extracting and analyzing engagement metrics from content."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the engagement extraction service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.weights = {
            'shares': 0.35,
            'likes': 0.25,
            'comments': 0.25,
            'views': 0.15
        }
    
    async def extract_engagement_metrics(self, link_id: int) -> Optional[Dict[str, Any]]:
        """Extract engagement metrics for a link.
        
        Args:
            link_id: ID of the link
            
        Returns:
            Dictionary of engagement metrics or None if error
        """
        try:
            # Get link details
            link = await self._get_link(link_id)
            if not link:
                logger.error(f"Link with ID {link_id} not found")
                return None
            
            # Get the latest snapshot
            snapshot = await self._get_latest_snapshot(link_id)
            if not snapshot:
                logger.error(f"No snapshot found for link ID {link_id}")
                return None
            
            # Extract engagement metrics from snapshot
            metrics = await self._get_competitor_metrics(link_id)
            engagement_metrics = metrics.engagement_data if metrics else {}
            
            # Calculate engagement score using verified metrics
            engagement_score = self._calculate_engagement_score(engagement_metrics)
            
            # Update competitor metrics with engagement score
            if not metrics:
                metrics = CompetitorMetrics(
                    link_id=link_id,
                    engagement_data=engagement_metrics,
                    engagement_score=engagement_score,
                    last_updated=datetime.now(timezone.utc)
                )
                self.db.add(metrics)
            else:
                metrics.engagement_data = engagement_metrics
                metrics.engagement_score = engagement_score
                metrics.last_updated = datetime.now(timezone.utc)
            
            # Commit changes
            await self.db.commit()
            
            return {
                "metrics": engagement_metrics,
                "score": engagement_score
            }
        except Exception as e:
            logger.error(f"Error extracting engagement for link {link_id}: {str(e)}")
            return None
    
    async def extract_engagement_for_links(self, link_ids: List[int]) -> Tuple[List[Any], List[Dict[str, Any]]]:
        """Extract engagement metrics for multiple links.
        
        Args:
            link_ids: List of link IDs
            
        Returns:
            Tuple of (links, errors)
        """
        if not link_ids:
            return [], [{"error": "No link IDs provided"}]
        
        links = []
        errors = []
        
        for link_id in link_ids:
            link, error = await self.extract_engagement_for_link(link_id)
            if link:
                links.append(link)
            if error:
                error["link_id"] = link_id
                errors.append(error)
        
        return links, errors
    
    async def extract_engagement_for_domain(self, domain_id: int) -> Dict[str, Any]:
        """Extract engagement metrics for all links of a domain.
        
        Args:
            domain_id: ID of the domain
            
        Returns:
            Dictionary with extraction results
        """
        try:
            # Get domain
            domain = await self._get_domain(domain_id)
            if not domain:
                logger.error(f"Domain with ID {domain_id} not found")
                return {
                    "success": False,
                    "error": f"Domain with ID {domain_id} not found"
                }
            
            # Get all links for the domain
            links = await self._get_links_for_domain(domain_id)
            if not links:
                logger.info(f"No links found for domain ID {domain_id}")
                return {
                    "success": True,
                    "links_processed": 0,
                    "successful": 0,
                    "failed": 0,
                    "average_engagement_score": 0,
                    "results": []
                }
            
            # Extract link IDs
            link_ids = [link.id for link in links]
            
            # Extract engagement for all links
            links_processed, errors = await self.extract_engagement_for_links(link_ids)
            
            # Count successful and failed extractions
            successful = len(links_processed)
            failed = len(errors)
            
            # Calculate average engagement score
            engagement_scores = [
                link.engagement_score 
                for link in links_processed 
                if link.engagement_score is not None
            ]
            
            avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0
            
            return {
                "success": True,
                "links_processed": len(link_ids),
                "successful": successful,
                "failed": failed,
                "average_engagement_score": avg_engagement,
                "links": links_processed,
                "errors": errors
            }
        except Exception as e:
            logger.error(f"Error extracting engagement for domain {domain_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def extract_engagement_for_link(self, link_id: int) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
        """Extract engagement metrics for a link.
        
        Args:
            link_id: ID of the link
            
        Returns:
            Tuple of (link, error)
        """
        try:
            # Get link details
            link = await self._get_link(link_id)
            if not link:
                logger.error(f"Link with ID {link_id} not found")
                return None, {"error": f"Link with ID {link_id} not found"}
            
            # Get the latest snapshot
            snapshot = await self._get_latest_snapshot(link_id)
            if not snapshot:
                logger.error(f"No snapshot found for link ID {link_id}")
                return None, {"error": f"No snapshot found for link ID {link_id}"}
            
            # Extract engagement metrics from snapshot
            engagement_metrics = self._extract_metrics(snapshot.html_content)
            
            # Calculate engagement score
            engagement_score = self._calculate_engagement_score(engagement_metrics)
            
            # Update link with engagement score
            link.engagement_score = engagement_score
            await self.db.commit()
            
            return link, None
        except Exception as e:
            logger.error(f"Error extracting engagement for link {link_id}: {str(e)}")
            return None, {"error": str(e)}
    
    async def _update_link_engagement_score(self, link_id: int, score: float) -> None:
        """Update the engagement score of a link.
        
        Args:
            link_id: ID of the link
            score: Engagement score to set
        """
        try:
            # Get link
            link = await self._get_link(link_id)
            if not link:
                logger.error(f"Link with ID {link_id} not found")
                return
            
            # Update score
            link.engagement_score = score
            
            # Commit changes
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error updating engagement score for link {link_id}: {str(e)}")
    
    def _extract_social_signals(self, html_content: str) -> int:
        """Extract social signals from HTML content.
        
        Args:
            html_content: HTML content to analyze
            
        Returns:
            Total count of social signals
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Extract likes, shares, comments, reactions
            total_signals = 0
            
            # Look for likes
            likes_elements = soup.select(".likes, .like, [data-testid='like']")
            for element in likes_elements:
                text = element.text.strip()
                numbers = re.findall(r'\d+', text)
                if numbers:
                    total_signals += int(numbers[0])
            
            # Look for shares
            shares_elements = soup.select(".shares, .share, [data-testid='share']")
            for element in shares_elements:
                text = element.text.strip()
                numbers = re.findall(r'\d+', text)
                if numbers:
                    total_signals += int(numbers[0])
            
            # Look for comments
            comments_elements = soup.select(".comments, .comment, [data-testid='comment']")
            for element in comments_elements:
                text = element.text.strip()
                numbers = re.findall(r'\d+', text)
                if numbers:
                    total_signals += int(numbers[0])
            
            # Look for reactions
            reactions_elements = soup.select(".reactions, .reaction, [data-testid='reaction']")
            for element in reactions_elements:
                text = element.text.strip()
                numbers = re.findall(r'\d+', text)
                if numbers:
                    total_signals += int(numbers[0])
            
            return total_signals
        except Exception as e:
            logger.error(f"Error extracting social signals: {str(e)}")
            return 0
    
    def _extract_metrics(self, html_content: str) -> Dict[str, Any]:
        """Extract engagement metrics from HTML content.
        
        Args:
            html_content: HTML content to analyze
            
        Returns:
            Dictionary of engagement metrics
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Extract likes, shares, comments, reactions
            metrics = {}
            
            # Look for likes
            likes_elements = soup.select(".likes, .like, [data-testid='like']")
            for element in likes_elements:
                text = element.text.strip()
                numbers = re.findall(r'\d+', text)
                if numbers:
                    metrics['likes'] = int(numbers[0])
            
            # Look for shares
            shares_elements = soup.select(".shares, .share, [data-testid='share']")
            for element in shares_elements:
                text = element.text.strip()
                numbers = re.findall(r'\d+', text)
                if numbers:
                    metrics['shares'] = int(numbers[0])
            
            # Look for comments
            comments_elements = soup.select(".comments, .comment, [data-testid='comment']")
            for element in comments_elements:
                text = element.text.strip()
                numbers = re.findall(r'\d+', text)
                if numbers:
                    metrics['comments'] = int(numbers[0])
            
            # Look for reactions
            reactions_elements = soup.select(".reactions, .reaction, [data-testid='reaction']")
            for element in reactions_elements:
                text = element.text.strip()
                numbers = re.findall(r'\d+', text)
                if numbers:
                    metrics['reactions'] = int(numbers[0])
            
            return metrics
        except Exception as e:
            logger.error(f"Error extracting engagement metrics: {str(e)}")
            return {}
    
    def _calculate_engagement_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate an engagement score from metrics.
        
        Args:
            metrics: Dictionary of engagement metrics
            
        Returns:
            Engagement score (0-100)
        """
        if not metrics:
            return 0.0
        
        # Extract metrics with defaults
        shares = metrics.get('shares', 0)
        likes = metrics.get('likes', 0)
        comments = metrics.get('comments', 0)
        views = metrics.get('views', 0)
        
        # If we have comment_elements but no comments, use that
        if comments == 0 and 'comment_elements' in metrics:
            comments = metrics.get('comment_elements', 0)
        
        # If we have share_buttons but no shares, use that
        if shares == 0 and 'share_buttons' in metrics:
            shares = metrics.get('share_buttons', 0)
        
        # Apply log transformation to handle skewed distributions
        # Add 1 to avoid log(0)
        log_shares = np.log1p(shares) if shares else 0
        log_likes = np.log1p(likes) if likes else 0
        log_comments = np.log1p(comments) if comments else 0
        log_views = np.log1p(views) if views else 0
        
        # Calculate weighted score
        score = (
            self.weights['shares'] * log_shares +
            self.weights['likes'] * log_likes +
            self.weights['comments'] * log_comments +
            self.weights['views'] * log_views
        )
        
        # Normalize to 0-100 range
        # These values are chosen based on typical engagement metrics
        max_score = np.log1p(1000)  # Assuming 1000 is a high engagement number
        normalized_score = (score / max_score) * 100
        
        # Ensure score is between 0 and 100
        return max(0.0, min(100.0, normalized_score))
    
    async def _get_link(self, link_id: int) -> Optional[Any]:
        """Get a link by ID.
        
        Args:
            link_id: ID of the link
            
        Returns:
            Link object or None
        """
        try:
            query = select(Link).where(Link.id == link_id)
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting link {link_id}: {str(e)}")
            return None
    
    async def _get_latest_snapshot(self, link_id: int) -> Optional[Any]:
        """Get the latest snapshot for a link.
        
        Args:
            link_id: ID of the link
            
        Returns:
            LinkSnapshot object or None
        """
        try:
            query = select(LinkSnapshot).where(LinkSnapshot.link_id == link_id).order_by(LinkSnapshot.created_at.desc())
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting latest snapshot for link {link_id}: {str(e)}")
            return None
    
    async def _get_links_for_domain(self, domain_id: int) -> List[Any]:
        """Get all links for a domain.
        
        Args:
            domain_id: ID of the domain
            
        Returns:
            List of link objects
        """
        try:
            query = select(Link).where(Link.domain_id == domain_id)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting links for domain {domain_id}: {str(e)}")
            return []
    
    async def _get_domain(self, domain_id: int) -> Optional[Any]:
        """Get a domain by ID.
        
        Args:
            domain_id: ID of the domain
            
        Returns:
            Domain object or None
        """
        try:
            query = select(Domain).where(Domain.id == domain_id)
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting domain {domain_id}: {str(e)}")
            return None
    
    async def _store_engagement_metrics(self, link_id: int, metrics: Dict[str, Any]) -> None:
        """Store engagement metrics in the database.
        
        Args:
            link_id: ID of the link
            metrics: Dictionary of engagement metrics
        """
        engagement = EngagementMetrics(
            link_id=link_id,
            metrics=metrics,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(engagement)
