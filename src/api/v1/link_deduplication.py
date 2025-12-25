"""API endpoints for Link Deduplication.

This module provides REST API endpoints for detecting and merging duplicate links.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.config import get_db
from src.auth.security import get_current_user
from src.models.user import User
from src.models.link import Link
from src.services.link_deduplication_service import LinkDeduplicationService
from src.schemas.link_deduplication import (
    DetectDuplicatesRequest,
    DetectDuplicatesResponse,
    MergeDuplicatesRequest,
    MergeDuplicatesResponse,
    DuplicateReportResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/links", tags=["link-deduplication"])


@router.post("/detect-duplicates", response_model=DetectDuplicatesResponse)
async def detect_duplicate_links(
    request: DetectDuplicatesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Detect duplicate links using URL normalization and similarity matching.

    Args:
        request: Detection configuration
        db: Database session
        current_user: Authenticated user

    Returns:
        Detected duplicate link groups
    """
    try:
        dedup_service = LinkDeduplicationService(
            similarity_threshold=request.similarity_threshold
        )

        # Get links to analyze
        query = select(Link)

        if request.company_id:
            query = query.where(Link.company_id == request.company_id)

        if not request.include_inactive:
            query = query.where(Link.is_active == True)

        result = await db.execute(query)
        links = result.scalars().all()

        # Detect duplicates
        duplicate_groups_dict = await dedup_service.detect_duplicates(db, list(links))

        # Format response
        duplicate_groups = []
        for normalized_url, group_info in duplicate_groups_dict.items():
            duplicate_groups.append({
                "normalized_url": normalized_url,
                "similarity_score": group_info.get("similarity_score", 1.0),
                "link_ids": group_info["link_ids"],
                "urls": group_info["urls"],
                "titles": group_info["titles"]
            })

        logger.info(f"Detected {len(duplicate_groups)} duplicate link groups")

        return {
            "total_links_analyzed": len(links),
            "duplicate_groups_found": len(duplicate_groups),
            "duplicate_groups": duplicate_groups
        }

    except Exception as e:
        logger.error(f"Error detecting duplicate links: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect duplicate links: {str(e)}"
        )


@router.post("/merge", response_model=MergeDuplicatesResponse)
async def merge_duplicate_links(
    request: MergeDuplicatesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Merge duplicate links into a single primary link.

    Args:
        request: Merge configuration
        db: Database session
        current_user: Authenticated user

    Returns:
        Merge operation result
    """
    try:
        dedup_service = LinkDeduplicationService()

        # Get primary link
        result = await db.execute(
            select(Link).where(Link.id == request.primary_link_id)
        )
        primary_link = result.scalar_one_or_none()

        if not primary_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Primary link not found"
            )

        # Get duplicate links
        result = await db.execute(
            select(Link).where(Link.id.in_(request.duplicate_link_ids))
        )
        duplicate_links = result.scalars().all()

        if len(duplicate_links) != len(request.duplicate_link_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more duplicate links not found"
            )

        # Merge links
        merged_link = await dedup_service.merge_links(
            db=db,
            primary_link=primary_link,
            duplicate_links=list(duplicate_links),
            merge_metadata=request.merge_metadata,
            merge_tags=request.merge_tags
        )

        logger.info(f"Merged {len(duplicate_links)} links into link {primary_link.id}")

        return {
            "message": f"Successfully merged {len(duplicate_links)} duplicate links",
            "primary_link_id": primary_link.id,
            "merged_count": len(duplicate_links),
            "deleted_link_ids": request.duplicate_link_ids
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error merging duplicate links: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge duplicate links: {str(e)}"
        )


@router.get("/duplicates/report", response_model=DuplicateReportResponse)
async def generate_duplicate_report(
    company_id: Optional[int] = None,
    similarity_threshold: float = 0.85,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a comprehensive duplicate links report.

    Args:
        company_id: Optional company ID filter
        similarity_threshold: Similarity threshold for detection
        db: Database session
        current_user: Authenticated user

    Returns:
        Duplicate links report
    """
    try:
        from datetime import datetime

        dedup_service = LinkDeduplicationService(
            similarity_threshold=similarity_threshold
        )

        # Get all links
        query = select(Link)
        if company_id:
            query = query.where(Link.company_id == company_id)

        result = await db.execute(query)
        all_links = result.scalars().all()

        # Detect duplicates
        duplicate_groups_dict = await dedup_service.detect_duplicates(db, list(all_links))

        # Calculate statistics
        total_links = len(all_links)
        duplicate_link_ids = set()
        for group_info in duplicate_groups_dict.values():
            duplicate_link_ids.update(group_info["link_ids"])

        duplicate_links = len(duplicate_link_ids)
        unique_links = total_links - duplicate_links
        duplication_rate = (duplicate_links / total_links * 100) if total_links > 0 else 0.0

        # Format duplicate groups
        duplicate_groups = []
        for normalized_url, group_info in duplicate_groups_dict.items():
            duplicate_groups.append({
                "normalized_url": normalized_url,
                "similarity_score": group_info.get("similarity_score", 1.0),
                "link_ids": group_info["link_ids"],
                "urls": group_info["urls"],
                "titles": group_info["titles"]
            })

        # Generate recommendations
        recommendations = []
        if duplication_rate > 20:
            recommendations.append("High duplication rate detected. Consider running merge operations.")
        if len(duplicate_groups) > 10:
            recommendations.append("Multiple duplicate groups found. Review and consolidate links.")
        if duplication_rate < 5:
            recommendations.append("Low duplication rate. Link management is healthy.")

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "total_links": total_links,
            "unique_links": unique_links,
            "duplicate_links": duplicate_links,
            "duplication_rate": duplication_rate,
            "duplicate_groups": duplicate_groups,
            "recommendations": recommendations
        }

    except Exception as e:
        logger.error(f"Error generating duplicate report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate duplicate report: {str(e)}"
        )
