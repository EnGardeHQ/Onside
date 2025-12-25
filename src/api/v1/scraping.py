"""API endpoints for Web Scraping.

This module provides REST API endpoints for web scraping operations,
content versioning, and scraping schedule management.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from src.database.config import get_db
from src.auth.security import get_current_user
from src.models.user import User
from src.models.scraped_content import ScrapedContent, ScrapingSchedule, ContentChange
from src.services.web_scraping_service import WebScrapingService
from src.schemas.web_scraping import (
    ScrapeRequest,
    ScrapedContentResponse,
    ScrapedContentDetailResponse,
    ScrapedContentListResponse,
    ContentVersionResponse,
    ContentDiffResponse,
    ScrapingScheduleCreate,
    ScrapingScheduleUpdate,
    ScrapingScheduleResponse,
    ScrapingScheduleListResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scraping", tags=["scraping"])


async def scrape_url_task(
    url: str,
    company_id: Optional[int],
    competitor_id: Optional[int],
    capture_screenshot: bool,
    wait_for_selector: Optional[str],
    timeout: int,
    db: AsyncSession
):
    """Background task for scraping URL."""
    try:
        scraper = WebScrapingService()
        await scraper.scrape_url(
            url=url,
            db=db,
            company_id=company_id,
            competitor_id=competitor_id,
            capture_screenshot=capture_screenshot,
            wait_for_selector=wait_for_selector,
            timeout=timeout
        )
    except Exception as e:
        logger.error(f"Error scraping URL {url}: {str(e)}")


@router.post("/scrape", response_model=ScrapedContentResponse, status_code=status.HTTP_202_ACCEPTED)
async def initiate_scraping(
    scrape_request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initiate web scraping for a URL.

    Args:
        scrape_request: Scraping configuration
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Authenticated user

    Returns:
        Accepted response with scraping initiated

    Note:
        Scraping happens asynchronously in the background
    """
    try:
        # Add scraping task to background
        background_tasks.add_task(
            scrape_url_task,
            url=scrape_request.url,
            company_id=scrape_request.company_id,
            competitor_id=scrape_request.competitor_id,
            capture_screenshot=scrape_request.capture_screenshot,
            wait_for_selector=scrape_request.wait_for_selector,
            timeout=scrape_request.timeout,
            db=db
        )

        return {
            "message": "Scraping initiated",
            "url": scrape_request.url,
            "status": "processing"
        }

    except Exception as e:
        logger.error(f"Error initiating scraping: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate scraping: {str(e)}"
        )


@router.get("/content", response_model=ScrapedContentListResponse)
async def list_scraped_content(
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    competitor_id: Optional[int] = Query(None, description="Filter by competitor ID"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List scraped content with filtering.

    Args:
        company_id: Optional company ID filter
        competitor_id: Optional competitor ID filter
        domain: Optional domain filter
        page: Page number
        page_size: Items per page
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of scraped content
    """
    try:
        # Build query
        query = select(ScrapedContent)

        # Apply filters
        filters = []
        if company_id:
            filters.append(ScrapedContent.company_id == company_id)
        if competitor_id:
            filters.append(ScrapedContent.competitor_id == competitor_id)
        if domain:
            filters.append(ScrapedContent.domain.ilike(f"%{domain}%"))

        if filters:
            query = query.where(and_(*filters))

        # Order by created_at descending
        query = query.order_by(desc(ScrapedContent.created_at))

        # Get total count
        count_query = select(ScrapedContent)
        if filters:
            count_query = count_query.where(and_(*filters))

        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await db.execute(query)
        content = result.scalars().all()

        return {
            "content": content,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        logger.error(f"Error listing scraped content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scraped content: {str(e)}"
        )


@router.get("/content/{content_id}", response_model=ScrapedContentDetailResponse)
async def get_scraped_content(
    content_id: int = Path(..., description="Content ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get scraped content details including text/HTML content.

    Args:
        content_id: Content ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Scraped content details

    Raises:
        HTTPException: If content not found
    """
    try:
        result = await db.execute(
            select(ScrapedContent).where(ScrapedContent.id == content_id)
        )
        content = result.scalar_one_or_none()

        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scraped content not found"
            )

        return content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scraped content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scraped content: {str(e)}"
        )


@router.get("/content/{content_id}/versions", response_model=list[ContentVersionResponse])
async def get_content_versions(
    content_id: int = Path(..., description="Content ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get version history for scraped content.

    Args:
        content_id: Content ID
        db: Database session
        current_user: Authenticated user

    Returns:
        List of content versions

    Raises:
        HTTPException: If content not found
    """
    try:
        # Get original content
        result = await db.execute(
            select(ScrapedContent).where(ScrapedContent.id == content_id)
        )
        content = result.scalar_one_or_none()

        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scraped content not found"
            )

        # Get all versions for this URL
        result = await db.execute(
            select(ScrapedContent).where(
                ScrapedContent.url == content.url
            ).order_by(desc(ScrapedContent.version))
        )
        versions = result.scalars().all()

        # Format response
        version_list = []
        for i, version in enumerate(versions):
            has_changes = i < len(versions) - 1  # All except the first version have changes
            version_list.append({
                "id": version.id,
                "version": version.version,
                "content_hash": version.content_hash or "",
                "created_at": version.created_at,
                "has_changes": has_changes
            })

        return version_list

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting content versions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content versions: {str(e)}"
        )


@router.get("/content/{content_id}/diff", response_model=ContentDiffResponse)
async def compare_content_versions(
    content_id: int = Path(..., description="Content ID"),
    compare_to: int = Query(..., description="Version ID to compare to"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare two versions of scraped content.

    Args:
        content_id: Content ID (new version)
        compare_to: Content ID to compare to (old version)
        db: Database session
        current_user: Authenticated user

    Returns:
        Content diff comparison

    Raises:
        HTTPException: If content versions not found
    """
    try:
        # Get both versions
        result = await db.execute(
            select(ScrapedContent).where(ScrapedContent.id == content_id)
        )
        new_version = result.scalar_one_or_none()

        result = await db.execute(
            select(ScrapedContent).where(ScrapedContent.id == compare_to)
        )
        old_version = result.scalar_one_or_none()

        if not new_version or not old_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both content versions not found"
            )

        # Check if they're from the same URL
        if new_version.url != old_version.url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot compare versions from different URLs"
            )

        # Check for changes
        has_changed = new_version.has_changed(old_version)

        # Look for existing change record
        result = await db.execute(
            select(ContentChange).where(
                and_(
                    ContentChange.old_version_id == old_version.id,
                    ContentChange.new_version_id == new_version.id
                )
            )
        )
        change = result.scalar_one_or_none()

        return {
            "url": new_version.url,
            "old_version": old_version.version,
            "new_version": new_version.version,
            "has_changed": has_changed,
            "change_percentage": change.change_percentage if change else None,
            "diff_summary": change.change_summary if change else None,
            "diff_data": change.diff_data if change else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing content versions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare content versions: {str(e)}"
        )


@router.post("/schedules", response_model=ScrapingScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_scraping_schedule(
    schedule_data: ScrapingScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a scraping schedule.

    Args:
        schedule_data: Schedule configuration
        db: Database session
        current_user: Authenticated user

    Returns:
        Created scraping schedule
    """
    try:
        schedule = ScrapingSchedule(
            name=schedule_data.name,
            url=schedule_data.url,
            company_id=schedule_data.company_id,
            competitor_id=schedule_data.competitor_id,
            cron_expression=schedule_data.cron_expression,
            capture_screenshot=schedule_data.capture_screenshot,
            scraping_config=schedule_data.scraping_config,
            is_active=True
        )

        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)

        logger.info(f"Created scraping schedule {schedule.id}")
        return schedule

    except Exception as e:
        logger.error(f"Error creating scraping schedule: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scraping schedule: {str(e)}"
        )


@router.get("/schedules", response_model=ScrapingScheduleListResponse)
async def list_scraping_schedules(
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List scraping schedules.

    Args:
        company_id: Optional company ID filter
        is_active: Optional active status filter
        page: Page number
        page_size: Items per page
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of scraping schedules
    """
    try:
        query = select(ScrapingSchedule)

        # Apply filters
        filters = []
        if company_id:
            filters.append(ScrapingSchedule.company_id == company_id)
        if is_active is not None:
            filters.append(ScrapingSchedule.is_active == is_active)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(desc(ScrapingSchedule.created_at))

        # Get total
        count_query = select(ScrapingSchedule)
        if filters:
            count_query = count_query.where(and_(*filters))

        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        schedules = result.scalars().all()

        return {
            "schedules": schedules,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        logger.error(f"Error listing scraping schedules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scraping schedules: {str(e)}"
        )


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scraping_schedule(
    schedule_id: int = Path(..., description="Schedule ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a scraping schedule.

    Args:
        schedule_id: Schedule ID
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException: If schedule not found
    """
    try:
        result = await db.execute(
            select(ScrapingSchedule).where(ScrapingSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scraping schedule not found"
            )

        await db.delete(schedule)
        await db.commit()

        logger.info(f"Deleted scraping schedule {schedule_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scraping schedule: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete scraping schedule: {str(e)}"
        )
