"""API endpoints for link search."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models import Link, Domain, Company
from src.database.config import get_db
from src.services.link_search.link_search import LinkSearchService

router = APIRouter()

@router.get("/domain/{domain_id}")
async def search_links_for_domain(
    domain_id: int,
    max_results: int = Query(50, gt=0, le=100),
    keywords: Optional[List[str]] = Query(None),
    session: AsyncSession = Depends(get_db)
):
    """Search for links associated with a domain."""
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
    
    # Create service and search
    service = LinkSearchService(session)
    if keywords:
        links, errors = await service.search_links_by_keywords(
            domain_id=domain_id,
            keywords=keywords,
            max_results=max_results
        )
    else:
        links, errors = await service.search_links_for_domain(
            domain_id=domain_id,
            max_results=max_results
        )
    
    # Return results
    return {
        "domain_id": domain_id,
        "domain_name": domain.domain_name,
        "links_found": len(links),
        "errors": errors,
        "links": [
            {
                "id": link.id,
                "url": link.url,
                "title": link.title,
                "description": link.meta.get("snippet", ""),
                "search_score": link.meta.get("search_score", 0),
                "created_at": link.created_at,
                "last_scraped_at": link.last_scraped_at
            }
            for link in links
        ]
    }

@router.get("/company/{company_id}")
async def search_links_for_company(
    company_id: int,
    max_results: int = Query(50, gt=0, le=100),
    keywords: Optional[List[str]] = Query(None),
    session: AsyncSession = Depends(get_db)
):
    """Search for links across all domains of a company."""
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
    
    # Create service and search
    service = LinkSearchService(session)
    links, errors = await service.search_links_for_company(
        company_id=company_id,
        max_results=max_results,
        keywords=keywords
    )
    
    # Return results
    return {
        "company_id": company_id,
        "company_name": company.name,
        "links_found": len(links),
        "errors": errors,
        "links": [
            {
                "id": link.id,
                "url": link.url,
                "title": link.title,
                "description": link.meta.get("snippet", ""),
                "search_score": link.meta.get("search_score", 0),
                "domain_id": link.domain_id,
                "created_at": link.created_at,
                "last_scraped_at": link.last_scraped_at
            }
            for link in links
        ]
    }

@router.get("/keyword")
async def search_links_by_keywords(
    domain_id: int,
    keywords: List[str] = Query(..., min_items=1),
    max_results: int = Query(50, gt=0, le=100),
    session: AsyncSession = Depends(get_db)
):
    """Search for links within a domain using specific keywords."""
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
    
    # Create service and search
    service = LinkSearchService(session)
    links, errors = await service.search_links_by_keywords(
        domain_id=domain_id,
        keywords=keywords,
        max_results=max_results
    )
    
    # Return results
    return {
        "domain_id": domain_id,
        "domain_name": domain.domain_name,
        "keywords": keywords,
        "links_found": len(links),
        "errors": errors,
        "links": [
            {
                "id": link.id,
                "url": link.url,
                "title": link.title,
                "description": link.meta.get("snippet", ""),
                "search_score": link.meta.get("search_score", 0),
                "created_at": link.created_at,
                "last_scraped_at": link.last_scraped_at
            }
            for link in links
        ]
    }

@router.get("/links/{link_id}")
async def get_link_details(
    link_id: int,
    session: AsyncSession = Depends(get_db)
):
    """Get details for a specific link."""
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
    
    # Get domain details
    result = await session.execute(
        select(Domain).where(Domain.id == link.domain_id)
    )
    domain = result.scalar_one_or_none()
    
    # Return link details
    return {
        "id": link.id,
        "url": link.url,
        "title": link.title,
        "domain_id": link.domain_id,
        "domain_name": domain.domain_name if domain else None,
        "created_at": link.created_at,
        "last_scraped_at": link.last_scraped_at,
        "engagement_score": link.engagement_score,
        "meta": link.meta
    }
