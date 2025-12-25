"""API endpoints for engagement extraction."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from src.models import Link, Domain, Company
from src.database.config import get_db
from src.services.jobs import JobManager
from src.services.engagement_extraction.engagement_extraction import EngagementExtractionService

router = APIRouter()

@router.post("/extract/{link_id}", status_code=status.HTTP_202_ACCEPTED)
async def extract_engagement_metrics(
    link_id: int,
    session: AsyncSession = Depends(get_db)
):
    """Extract engagement metrics for a single link."""
    # Check if link exists
    result = await session.execute(
        select(Link).where(Link.id == link_id)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    # Create a background job for engagement extraction
    job_id = await JobManager.create_job(
        "engagement_extraction",
        {"link_id": link_id}
    )
    
    return {"job_id": job_id}

@router.post("/extract/batch", status_code=status.HTTP_202_ACCEPTED)
async def extract_engagement_batch(
    link_ids: List[int],
    session: AsyncSession = Depends(get_db)
):
    """Extract engagement metrics for multiple links in batch."""
    if not link_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No link IDs provided"
        )
    
    if len(link_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Maximum 100 links can be processed in a single batch"
        )
    
    # Check if links exist
    result = await session.execute(
        select(Link).where(Link.id.in_(link_ids))
    )
    links = result.scalars().all()
    found_ids = {link.id for link in links}
    missing_ids = set(link_ids) - found_ids
    
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Links not found: {missing_ids}"
        )
    
    # Create a background job for batch engagement extraction
    job_id = await JobManager.create_job(
        "engagement_extraction_batch",
        {"link_ids": link_ids}
    )
    
    return {"job_id": job_id}

@router.post("/extract/domain/{domain_id}", status_code=status.HTTP_202_ACCEPTED)
async def extract_engagement_for_domain(
    domain_id: int,
    max_links: int = Query(100, gt=0, le=1000),
    session: AsyncSession = Depends(get_db)
):
    """Extract engagement metrics for all links of a domain."""
    # Check if domain exists
    result = await session.execute(
        select(Domain).where(Domain.id == domain_id)
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found"
        )
    
    # Create a background job for domain engagement extraction
    job_id = await JobManager.create_job(
        "engagement_extraction_domain",
        {"domain_id": domain_id, "max_links": max_links}
    )
    
    return {"job_id": job_id}

@router.post("/extract/company/{company_id}", status_code=status.HTTP_202_ACCEPTED)
async def extract_engagement_for_company(
    company_id: int,
    max_links: int = Query(100, gt=0, le=1000),
    session: AsyncSession = Depends(get_db)
):
    """Extract engagement metrics for all links across all domains of a company."""
    # Check if company exists
    result = await session.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Create a background job for company engagement extraction
    job_id = await JobManager.create_job(
        "engagement_extraction_company",
        {"company_id": company_id, "max_links": max_links}
    )
    
    return {"job_id": job_id}

@router.get("/metrics/{link_id}")
async def get_engagement_metrics(
    link_id: int,
    session: AsyncSession = Depends(get_db)
):
    """Get the engagement metrics for a link."""
    # Check if link exists
    result = await session.execute(
        select(Link).where(Link.id == link_id)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    # Create service
    service = EngagementExtractionService(session)
    
    # Get the latest metrics
    metrics_result = await service.get_latest_metrics(link_id)
    if not metrics_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No engagement metrics found for this link"
        )
    
    # Return the metrics
    return {
        "link_id": link_id,
        "url": link.url,
        "title": link.title,
        "engagement_score": link.engagement_score,
        "last_updated": metrics_result["timestamp"],
        "metrics": metrics_result["metrics"]
    }

@router.get("/domain/{domain_id}/summary")
async def get_domain_engagement_summary(
    domain_id: int,
    session: AsyncSession = Depends(get_db)
):
    """Get a summary of engagement metrics for all links of a domain."""
    # Check if domain exists
    result = await session.execute(
        select(Domain).where(Domain.id == domain_id)
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found"
        )
    
    # Get links with engagement scores
    result = await session.execute(
        select(Link)
        .where(Link.domain_id == domain_id)
        .where(Link.engagement_score.is_not(None))
        .order_by(desc(Link.engagement_score))
    )
    links = result.scalars().all()
    
    if not links:
        return {
            "domain_id": domain_id,
            "domain_name": domain.domain_name,
            "total_links_with_metrics": 0,
            "average_engagement_score": 0,
            "top_links": []
        }
    
    # Calculate average engagement score
    average_score = sum(link.engagement_score for link in links) / len(links)
    
    # Return the summary
    return {
        "domain_id": domain_id,
        "domain_name": domain.domain_name,
        "total_links_with_metrics": len(links),
        "average_engagement_score": average_score,
        "top_links": [
            {
                "id": link.id,
                "url": link.url,
                "title": link.title,
                "engagement_score": link.engagement_score,
                "last_scraped_at": link.last_scraped_at
            }
            for link in links[:10]  # Top 10 links
        ]
    }
