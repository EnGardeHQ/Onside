"""Integrated workflow for web scraping, link search, and engagement extraction.

This module implements the complete workflow for collecting competitor data
through web scraping, link discovery, and engagement analysis.

Following Semantic Seed coding standards:
- Comprehensive error handling
- Detailed logging
- Type hints
- BDD/TDD compatible design
"""
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.web_scraper.web_scraper import WebScraperService
from src.services.link_search.link_search import LinkSearchService
from src.services.engagement_extraction.engagement_extraction import EngagementExtractionService
from src.models.link import Link, Domain, Company
from src.models.competitor import Competitor

logger = logging.getLogger(__name__)

async def scrape_company_data(
    web_scraper_service: WebScraperService,
    link_search_service: LinkSearchService,
    engagement_extraction_service: EngagementExtractionService,
    company_id: int,
    max_links: int = 10
) -> Dict[str, Any]:
    """Execute the complete web scraping workflow for a company.
    
    This function orchestrates:
    1. Get company details
    2. Find or create domain record
    3. Search for relevant links using LinkSearchService
    4. Scrape content from each link using WebScraperService
    5. Extract engagement metrics using EngagementExtractionService
    
    Args:
        web_scraper_service: Initialized WebScraperService
        link_search_service: Initialized LinkSearchService
        engagement_extraction_service: Initialized EngagementExtractionService
        company_id: ID of company to scrape
        max_links: Maximum number of links to process
        
    Returns:
        Dictionary with workflow results
    """
    try:
        db = web_scraper_service.session
        
        # Step 1: Get company details
        company = await _get_company(db, company_id)
        if not company:
            logger.error(f"Company with ID {company_id} not found")
            return {
                "success": False,
                "error": f"Company with ID {company_id} not found"
            }
        
        # Step 2: Find or create domain
        domain = await _get_or_create_domain(db, company)
        
        # Step 3: Search for relevant links
        industry_keywords = company.industry.split() if company.industry else []
        name_keywords = company.name.split()
        search_keywords = list(set(industry_keywords + name_keywords))
        
        links_result, errors = await link_search_service.search_links_for_domain(
            domain_id=domain.id,
            max_results=max_links,
            keywords=search_keywords[:5]  # Limit to 5 keywords for better results
        )
        
        if errors:
            logger.warning(f"Errors during link search: {errors}")
        
        if not links_result:
            logger.warning(f"No links found for company {company.name} (ID: {company_id})")
            return {
                "success": False,
                "error": f"No links found for company {company.name}"
            }
        
        # Step 4 & 5: Scrape content and extract engagement metrics
        links_scraped = 0
        engagement_metrics_extracted = 0
        
        for link in links_result[:max_links]:
            # Scrape content
            scrape_result = await web_scraper_service.scrape_link(link.id)
            if scrape_result.get("success"):
                links_scraped += 1
                
                # Extract engagement metrics
                engagement_result = await engagement_extraction_service.extract_engagement_metrics(link.id)
                if engagement_result:
                    engagement_metrics_extracted += 1
            else:
                logger.warning(f"Failed to scrape link {link.url}: {scrape_result.get('error')}")
        
        return {
            "success": True,
            "company_id": company_id,
            "company_name": company.name,
            "domain": domain.name,  # Using 'name' as per verified schema
            "links_scraped": links_scraped,
            "engagement_metrics_extracted": engagement_metrics_extracted
        }
        
    except Exception as e:
        logger.error(f"Error in scraping workflow for company {company_id}: {str(e)}")
        return {
            "success": False,
            "company_id": company_id,
            "error": f"Workflow error: {str(e)}"
        }

async def scrape_competitors_data(
    web_scraper_service: WebScraperService,
    link_search_service: LinkSearchService,
    engagement_extraction_service: EngagementExtractionService,
    competitors: List[Dict[str, Any]],
    max_links_per_competitor: int = 5
) -> Dict[str, Any]:
    """Execute the complete web scraping workflow for a list of competitors.
    
    Args:
        web_scraper_service: Initialized WebScraperService
        link_search_service: Initialized LinkSearchService  
        engagement_extraction_service: Initialized EngagementExtractionService
        competitors: List of competitor details with IDs
        max_links_per_competitor: Maximum links to process per competitor
        
    Returns:
        Dictionary with workflow results
    """
    try:
        results = []
        
        for competitor in competitors:
            competitor_id = competitor["id"]
            result = await scrape_company_data(
                web_scraper_service,
                link_search_service,
                engagement_extraction_service,
                company_id=competitor_id,
                max_links=max_links_per_competitor
            )
            results.append(result)
        
        # Count successful scrapes
        successful = sum(1 for r in results if r.get("success"))
        
        return {
            "success": True,
            "total_competitors": len(competitors),
            "successful_scrapes": successful,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in scraping workflow for competitors: {str(e)}")
        return {
            "success": False,
            "error": f"Workflow error: {str(e)}"
        }

async def _get_company(db: AsyncSession, company_id: int) -> Optional[Company]:
    """Get company by ID."""
    stmt = select(Company).where(Company.id == company_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def _get_or_create_domain(db: AsyncSession, company: Company) -> Domain:
    """Get or create domain for a company."""
    # Check if domain exists
    stmt = select(Domain).where(Domain.name == company.domain)
    result = await db.execute(stmt)
    domain = result.scalar_one_or_none()
    
    if not domain:
        # Create new domain following verified schema
        domain = Domain(
            name=company.domain,  # Using 'name' as per verified schema
            company_id=company.id,
            meta_data={  # Adding metadata for BDD/TDD tracking
                'source': 'scraping_workflow',
                'created_at': datetime.now().isoformat(),
                'company_name': company.name
            }
        )
        db.add(domain)
        await db.commit()
        await db.refresh(domain)
        
    return domain
