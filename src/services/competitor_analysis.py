"""
Competitor Analysis Service for OnSide application.

This module provides business logic for identifying and analyzing competitors.
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
import tldextract

from src.models.company import Company
from src.models.competitor import Competitor
from src.models.domain import Domain
from src.repositories.company_repository import CompanyRepository
from src.repositories.competitor_repository import CompetitorRepository
from src.repositories.domain_repository import DomainRepository
from src.services.ai.llm_service import LLMService
from src.services.seo.seo_service import SEOService
from src.services.data.data_enrichment import DataEnrichmentService
from src.exceptions import DomainValidationError

logger = logging.getLogger(__name__)

class CompetitorAnalysisService:
    """Service for competitor identification and analysis."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the service with a database session.
        
        Args:
            db: Database session
        """
        self.db = db
        self.company_repo = CompanyRepository(db)
        self.competitor_repo = CompetitorRepository(db)
        self.domain_repo = DomainRepository(db)
        self.llm_service = LLMService()
        self.seo_service = SEOService()
        self.data_enrichment = DataEnrichmentService()
    
    async def identify_competitors(
        self,
        company_id: int,
        max_competitors: int = 10,
        min_relevance_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Identify potential competitors for a company.
        
        Args:
            company_id: ID of the company to find competitors for
            max_competitors: Maximum number of competitors to return
            min_relevance_score: Minimum relevance score (0-1) for a competitor to be included
            
        Returns:
            List of potential competitors with relevance scores
        """
        # Get the company details
        company = await self.company_repo.get_by_id(company_id)
        if not company:
            raise ValueError(f"Company with ID {company_id} not found")
        
        # Get the company's domains
        company_domains = await self.domain_repo.get_by_company(company_id)
        if not company_domains:
            raise ValueError(f"No domains found for company {company_id}")
        
        # Get primary domain
        primary_domain = next((d for d in company_domains if d.is_primary), company_domains[0])
        
        # Step 1: Find competitors through SEO analysis
        seo_competitors = await self._find_competitors_via_seo(primary_domain.domain)
        
        # Step 2: Find competitors through industry analysis
        industry_competitors = await self._find_competitors_via_industry(company)
        
        # Step 3: Combine and deduplicate competitors
        all_competitors = await self._combine_competitors(
            seo_competitors, 
            industry_competitors,
            exclude_domains=[d.domain for d in company_domains]
        )
        
        # Step 4: Calculate relevance scores
        scored_competitors = await self._score_competitors(
            all_competitors, 
            company,
            primary_domain.domain
        )
        
        # Filter by minimum relevance score and limit results
        filtered_competitors = [
            c for c in scored_competitors 
            if c['relevance_score'] >= min_relevance_score
        ][:max_competitors]
        
        # Sort by relevance score (descending)
        filtered_competitors.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return filtered_competitors
    
    async def _find_competitors_via_seo(self, domain: str) -> List[Dict[str, Any]]:
        """Find competitors through SEO analysis.
        
        Args:
            domain: Domain to find competitors for
            
        Returns:
            List of potential competitors from SEO analysis
        """
        try:
            # Get competing domains from SEO data
            competitors = await self.seo_service.get_competing_domains(domain)
            return [
                {
                    'domain': comp['domain'],
                    'name': comp.get('name', ''),
                    'source': 'seo_analysis',
                    'metadata': {
                        'common_keywords': comp.get('common_keywords', []),
                        'overlap_score': comp.get('overlap_score', 0)
                    }
                }
                for comp in competitors
            ]
        except Exception as e:
            logger.error(f"Error finding competitors via SEO for {domain}: {str(e)}")
            return []
    
    async def _find_competitors_via_industry(self, company: Company) -> List[Dict[str, Any]]:
        """Find competitors through industry analysis.
        
        Args:
            company: Company to find competitors for
            
        Returns:
            List of potential competitors from industry analysis
        """
        try:
            # Use the data enrichment service to find similar companies
            similar_companies = await self.data_enrichment.find_similar_companies(
                company_name=company.name,
                industry=company.industry,
                location=company.location,
                size_range=f"{company.employee_count_min}-{company.employee_count_max}"
                if company.employee_count_min and company.employee_count_max
                else None,
            )
            
            return [
                {
                    'domain': comp.get('domain', ''),
                    'name': comp.get('name', ''),
                    'source': 'industry_analysis',
                    'metadata': {
                        'similarity_score': comp.get('similarity_score', 0),
                        'industry': comp.get('industry', '')
                    }
                }
                for comp in similar_companies
                if comp.get('domain')
            ]
        except Exception as e:
            logger.error(f"Error finding competitors via industry for {company.name}: {str(e)}")
            return []
    
    async def _combine_competitors(
        self, 
        *competitor_lists: List[Dict[str, Any]],
        exclude_domains: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Combine and deduplicate competitor lists.
        
        Args:
            *competitor_lists: Lists of competitors to combine
            exclude_domains: List of domains to exclude
            
        Returns:
            Combined and deduplicated list of competitors
        """
        exclude_domains = set(exclude_domains or [])
        seen_domains = set()
        result = []
        
        for competitor_list in competitor_lists:
            for competitor in competitor_list:
                domain = competitor.get('domain', '').lower().strip()
                if not domain or domain in seen_domains or domain in exclude_domains:
                    continue
                
                seen_domains.add(domain)
                result.append(competitor)
        
        return result
    
    async def _score_competitors(
        self, 
        competitors: List[Dict[str, Any]],
        company: Company,
        primary_domain: str
    ) -> List[Dict[str, Any]]:
        """Calculate relevance scores for competitors.
        
        Args:
            competitors: List of competitors to score
            company: The company to compare against
            primary_domain: The company's primary domain
            
        Returns:
            List of competitors with relevance scores
        """
        if not competitors:
            return []
        
        # Get domain metrics in bulk for better performance
        domains = [c['domain'] for c in competitors]
        domain_metrics = await self.seo_service.get_domain_metrics_batch(domains)
        
        # Get company's domain metrics for comparison
        try:
            company_metrics = await self.seo_service.get_domain_metrics(primary_domain)
        except Exception as e:
            logger.error(f"Error getting company metrics for {primary_domain}: {str(e)}")
            company_metrics = {}
        
        # Score each competitor
        scored_competitors = []
        for competitor in competitors:
            domain = competitor['domain']
            metrics = domain_metrics.get(domain, {})
            
            # Calculate relevance score (0-1)
            relevance_score = self._calculate_relevance_score(
                competitor, 
                metrics, 
                company_metrics,
                company
            )
            
            # Add to results
            scored_competitors.append({
                **competitor,
                'relevance_score': relevance_score,
                'metrics': metrics
            })
        
        return scored_competitors
    
    def _calculate_relevance_score(
        self,
        competitor: Dict[str, Any],
        competitor_metrics: Dict[str, Any],
        company_metrics: Dict[str, Any],
        company: Company
    ) -> float:
        """Calculate a relevance score for a competitor.
        
        Args:
            competitor: Competitor data
            competitor_metrics: SEO metrics for the competitor
            company_metrics: SEO metrics for the company
            company: Company to compare against
            
        Returns:
            Relevance score between 0 and 1
        """
        score = 0.0
        total_weight = 0.0
        
        # 1. Industry similarity (if available)
        if 'metadata' in competitor and 'industry' in competitor['metadata']:
            industry_similarity = 0.7 if competitor['metadata']['industry'] == company.industry else 0.1
            score += industry_similarity * 0.3
            total_weight += 0.3
        
        # 2. Domain authority comparison
        if 'domain_authority' in competitor_metrics and 'domain_authority' in company_metrics:
            da_diff = abs(competitor_metrics['domain_authority'] - company_metrics['domain_authority'])
            # Score decreases as the difference increases (max difference is ~100)
            da_score = max(0, 1 - (da_diff / 50))  # 50 is the max reasonable difference
            score += da_score * 0.4
            total_weight += 0.4
        
        # 3. Common keywords (from SEO analysis)
        if 'metadata' in competitor and 'common_keywords' in competitor['metadata']:
            common_keywords = len(competitor['metadata']['common_keywords'])
            # Assuming 0-50 common keywords is a reasonable range
            keyword_score = min(1.0, common_keywords / 10)
            score += keyword_score * 0.3
            total_weight += 0.3
        
        # 4. Traffic comparison (if available)
        if 'monthly_traffic' in competitor_metrics and 'monthly_traffic' in company_metrics:
            # Calculate traffic ratio (closer to 1 is better)
            traffic_ratio = min(
                competitor_metrics['monthly_traffic'] / max(1, company_metrics['monthly_traffic']),
                company_metrics['monthly_traffic'] / max(1, competitor_metrics['monthly_traffic'])
            )
            score += traffic_ratio * 0.3
            total_weight += 0.3
        
        # Normalize the score if we have any weights
        if total_weight > 0:
            score = score / total_weight
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
