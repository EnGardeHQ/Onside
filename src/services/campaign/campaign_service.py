"""Campaign management service for organizing competitive analysis projects.

This service implements functionality for creating campaigns, identifying competitors,
and managing the workflow for competitive analysis.

Following Semantic Seed coding standards:
- Type hints
- Comprehensive error handling
- Detailed logging
- BDD/TDD compatible design
"""
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import joinedload

from src.models.company import Company
from src.models.competitor import Competitor
from src.models.report import Report, ReportType, ReportStatus

logger = logging.getLogger(__name__)

class CampaignService:
    """Service for managing campaigns and their associated companies/competitors.
    
    This service enables users to create campaigns for competitive analysis,
    identify relevant competitors, and manage the complete workflow from data
    collection to report generation.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize the campaign service.
        
        Args:
            db: Database session for data operations
        """
        self.db = db
        
    async def create_campaign(
        self, 
        name: str, 
        primary_company_id: int, 
        description: str = None
    ) -> Dict[str, Any]:
        """Create a new campaign with a primary company focus.
        
        Args:
            name: Name of the campaign
            primary_company_id: ID of the primary company to analyze
            description: Optional description of the campaign
            
        Returns:
            Dictionary with campaign details and success status
        """
        try:
            # Validate that the primary company exists
            stmt = select(Company).where(Company.id == primary_company_id)
            result = await self.db.execute(stmt)
            company = result.scalar_one_or_none()
            
            if not company:
                logger.error(f"Company with ID {primary_company_id} not found")
                return {
                    "success": False,
                    "error": f"Company with ID {primary_company_id} not found"
                }
            
            # Create a new report for the campaign
            report = Report(
                company_id=primary_company_id,
                type=ReportType.COMPETITOR,
                status=ReportStatus.QUEUED,
                parameters={
                    "campaign_name": name,
                    "description": description,
                    "primary_company_id": primary_company_id
                },
                created_at=datetime.now(timezone.utc)
            )
            
            self.db.add(report)
            await self.db.commit()
            await self.db.refresh(report)
            
            logger.info(f"Created campaign '{name}' with report ID {report.id}")
            
            return {
                "success": True,
                "campaign": {
                    "id": report.id,  # Using report ID as campaign ID
                    "name": name,
                    "primary_company_id": primary_company_id,
                    "primary_company_name": company.name,
                    "description": description,
                    "created_at": report.created_at.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating campaign: {str(e)}")
            return {
                "success": False,
                "error": f"Error creating campaign: {str(e)}"
            }
    
    async def identify_competitors(
        self,
        campaign_id: int,
        max_competitors: int = 5
    ) -> List[Dict[str, Any]]:
        """Identify relevant competitors for the primary company in a campaign.
        
        Uses industry classification, market presence, and keyword analysis to
        determine the most relevant competitors.
        
        Args:
            campaign_id: ID of the campaign (report ID)
            max_competitors: Maximum number of competitors to return
            
        Returns:
            List of competitor details with relevance scores
        """
        try:
            # Get the report for the campaign
            stmt = select(Report).where(Report.id == campaign_id)
            result = await self.db.execute(stmt)
            report = result.scalar_one_or_none()
            
            if not report:
                logger.error(f"Campaign with ID {campaign_id} not found")
                return []
            
            # Get primary company details
            primary_company_id = report.parameters.get("primary_company_id")
            if not primary_company_id:
                logger.error(f"Primary company ID not found in campaign {campaign_id}")
                return []
                
            stmt = select(Company).where(Company.id == primary_company_id)
            result = await self.db.execute(stmt)
            primary_company = result.scalar_one_or_none()
            
            if not primary_company:
                logger.error(f"Primary company with ID {primary_company_id} not found")
                return []
            
            # Find competitors in the same industry
            industry = primary_company.industry
            domain_keywords = self._extract_domain_keywords(primary_company.domain)
            
            stmt = select(Competitor).where(
                or_(
                    and_(
                        Competitor.company_id != primary_company_id,
                        func.lower(Competitor.description).contains(industry.lower()) if industry else False
                    ),
                    # Match by domain keywords (partial matching)
                    *[func.lower(Competitor.domain).contains(kw.lower()) for kw in domain_keywords if kw]
                )
            ).limit(max_competitors)
            
            result = await self.db.execute(stmt)
            competitors = result.scalars().all()
            
            # Calculate relevance scores
            ranked_competitors = []
            for competitor in competitors:
                relevance_score = self._calculate_relevance_score(
                    primary_company, competitor
                )
                
                ranked_competitors.append({
                    "id": competitor.id,
                    "name": competitor.name,
                    "domain": competitor.domain,
                    "description": competitor.description,
                    "relevance_score": relevance_score
                })
            
            # Sort by relevance score
            ranked_competitors.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            # Limit to max_competitors
            return ranked_competitors[:max_competitors]
            
        except Exception as e:
            logger.error(f"Error identifying competitors: {str(e)}")
            return []
    
    def _extract_domain_keywords(self, domain: str) -> List[str]:
        """Extract relevant keywords from a domain name.
        
        Args:
            domain: Domain name to extract keywords from
            
        Returns:
            List of relevant keywords
        """
        if not domain:
            return []
            
        # Remove common TLDs and split by dots and dashes
        domain = domain.lower()
        for tld in [".com", ".org", ".net", ".co", ".io"]:
            domain = domain.replace(tld, "")
            
        keywords = []
        for separator in [".", "-", "_"]:
            if separator in domain:
                parts = domain.split(separator)
                keywords.extend([p for p in parts if len(p) > 2])
                
        # If no separators, just use the domain itself
        if not keywords and len(domain) > 2:
            keywords.append(domain)
            
        return list(set(keywords))  # Remove duplicates
    
    def _calculate_relevance_score(
        self, 
        primary_company: Company, 
        competitor: Competitor
    ) -> float:
        """Calculate relevance score between a company and potential competitor.
        
        The score is based on:
        - Industry match (50%)
        - Description similarity (30%)
        - Domain similarity (20%)
        
        Args:
            primary_company: The primary company
            competitor: Potential competitor to score
            
        Returns:
            Relevance score between 0 and 1
        """
        score = 0.0
        max_score = 0.0
        
        # Industry match (50%)
        weight_industry = 0.5
        max_score += weight_industry
        if primary_company.industry and competitor.description:
            if primary_company.industry.lower() in competitor.description.lower():
                score += weight_industry
        
        # Description similarity (30%)
        weight_desc = 0.3
        max_score += weight_desc
        if primary_company.description and competitor.description:
            # Simple keyword matching for now
            primary_keywords = set(primary_company.description.lower().split())
            competitor_keywords = set(competitor.description.lower().split())
            common_keywords = primary_keywords.intersection(competitor_keywords)
            
            if primary_keywords:
                similarity = len(common_keywords) / len(primary_keywords)
                score += weight_desc * similarity
        
        # Domain similarity (20%)
        weight_domain = 0.2
        max_score += weight_domain
        if primary_company.domain and competitor.domain:
            primary_keywords = set(self._extract_domain_keywords(primary_company.domain))
            competitor_keywords = set(self._extract_domain_keywords(competitor.domain))
            
            if primary_keywords and competitor_keywords:
                # Check for any overlap in domain keywords
                common_keywords = primary_keywords.intersection(competitor_keywords)
                if common_keywords:
                    score += weight_domain
        
        # Normalize score
        return score / max_score if max_score > 0 else 0.0
