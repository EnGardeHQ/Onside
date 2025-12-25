"""API endpoints for web scraping."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from src.models import Link, LinkSnapshot
from src.database.config import get_db
from src.services.jobs import JobManager
from src.services.web_scraper.web_scraper import WebScraperService

router = APIRouter()

@router.post("/scrape/{link_id}", status_code=status.HTTP_202_ACCEPTED)
async def scrape_link(
    link_id: int,
    session: AsyncSession = Depends(get_db)
):
    """Scrape content from a single link."""
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
    
    # Create a background job for web scraping
    job_id = await JobManager.create_job(
        "web_scraper",
        {"link_id": link_id}
    )
    
    return {"job_id": job_id}

@router.post("/scrape/batch", status_code=status.HTTP_202_ACCEPTED)
async def scrape_links_batch(
    link_ids: List[int],
    session: AsyncSession = Depends(get_db)
):
    """Scrape content from multiple links in batch."""
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
    
    # Create a background job for batch web scraping
    job_id = await JobManager.create_job(
        "web_scraper_batch",
        {"link_ids": link_ids}
    )
    
    return {"job_id": job_id}

@router.get("/content/{link_id}")
async def get_link_content(
    link_id: int,
    version: Optional[int] = Query(None, description="Snapshot version to retrieve"),
    session: AsyncSession = Depends(get_db)
):
    """Get the scraped content for a link."""
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
    
    # Get the snapshot
    query = select(LinkSnapshot).where(LinkSnapshot.link_id == link_id)
    
    if version is not None:
        # Get specific version
        result = await session.execute(
            query.where(LinkSnapshot.version == version)
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Snapshot version {version} not found for link {link_id}"
            )
    else:
        # Get latest version
        result = await session.execute(
            query.order_by(desc(LinkSnapshot.created_at)).limit(1)
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No snapshots found for link {link_id}"
            )
    
    # Return the content
    return {
        "link_id": link_id,
        "snapshot_id": snapshot.id,
        "version": snapshot.version,
        "created_at": snapshot.created_at,
        "metadata": snapshot.metadata,
        "engagement_metrics": snapshot.engagement_metrics,
        "html_content": snapshot.html_content,
        "screenshot_path": snapshot.screenshot_path
    }

@router.get("/versions/{link_id}")
async def get_link_versions(
    link_id: int,
    limit: int = Query(20, gt=0),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db)
):
    """Get all versions of scraped content for a link."""
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
    
    # Get the snapshots
    result = await session.execute(
        select(LinkSnapshot)
        .where(LinkSnapshot.link_id == link_id)
        .order_by(desc(LinkSnapshot.created_at))
        .offset(offset)
        .limit(limit)
    )
    snapshots = result.scalars().all()
    
    # Count total snapshots
    result = await session.execute(
        select(LinkSnapshot)
        .where(LinkSnapshot.link_id == link_id)
    )
    total = len(result.scalars().all())
    
    # Return the versions
    return {
        "link_id": link_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "snapshots": [
            {
                "snapshot_id": snapshot.id,
                "version": snapshot.version,
                "created_at": snapshot.created_at,
                "metadata": snapshot.metadata,
                "engagement_metrics": snapshot.engagement_metrics,
                "screenshot_path": snapshot.screenshot_path
            }
            for snapshot in snapshots
        ]
    }

@router.post("/rescrape/{link_id}", status_code=status.HTTP_202_ACCEPTED)
async def rescrape_link(
    link_id: int,
    session: AsyncSession = Depends(get_db)
):
    """Force a rescrape of a link, ignoring the recent scrape check."""
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
    
    # Create a background job for web scraping with force flag
    job_id = await JobManager.create_job(
        "web_scraper",
        {"link_id": link_id, "force": True}
    )
    
    return {"job_id": job_id}
