"""API endpoints for Search History.

This module provides REST API endpoints for tracking and analyzing search history,
including search analytics and cleanup operations.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from datetime import datetime, timedelta

from src.database.config import get_db
from src.auth.security import get_current_user
from src.models.user import User
from src.models.search_history import SearchHistory
from src.schemas.search_history import (
    SearchHistoryListResponse,
    SearchHistoryResponse,
    SearchAnalyticsResponse,
    CleanupResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search-history", tags=["search-history"])


@router.get("", response_model=SearchHistoryListResponse)
async def list_search_history(
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    search_type: Optional[str] = Query(None, description="Filter by search type"),
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List search history with filtering.

    Args:
        company_id: Optional company ID filter
        search_type: Optional search type filter
        days: Number of days to retrieve
        page: Page number
        page_size: Items per page
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of search history records
    """
    try:
        # Calculate date threshold
        date_threshold = datetime.utcnow() - timedelta(days=days)

        # Build query
        query = select(SearchHistory).where(
            and_(
                SearchHistory.user_id == current_user.id,
                SearchHistory.created_at >= date_threshold
            )
        )

        # Apply filters
        if company_id:
            query = query.where(SearchHistory.company_id == company_id)
        if search_type:
            query = query.where(SearchHistory.search_type == search_type)

        # Order by created_at descending
        query = query.order_by(desc(SearchHistory.created_at))

        # Get total count
        count_query = select(func.count()).select_from(SearchHistory).where(
            and_(
                SearchHistory.user_id == current_user.id,
                SearchHistory.created_at >= date_threshold
            )
        )
        if company_id:
            count_query = count_query.where(SearchHistory.company_id == company_id)
        if search_type:
            count_query = count_query.where(SearchHistory.search_type == search_type)

        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await db.execute(query)
        searches = result.scalars().all()

        return {
            "searches": searches,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        logger.error(f"Error listing search history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list search history: {str(e)}"
        )


@router.get("/analytics", response_model=SearchAnalyticsResponse)
async def get_search_analytics(
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get search analytics for the current user.

    Args:
        company_id: Optional company ID filter
        days: Number of days to analyze
        db: Database session
        current_user: Authenticated user

    Returns:
        Search analytics data
    """
    try:
        # Calculate date threshold
        date_threshold = datetime.utcnow() - timedelta(days=days)

        # Build base query
        base_query = select(SearchHistory).where(
            and_(
                SearchHistory.user_id == current_user.id,
                SearchHistory.created_at >= date_threshold
            )
        )

        if company_id:
            base_query = base_query.where(SearchHistory.company_id == company_id)

        # Get all searches
        result = await db.execute(base_query)
        searches = result.scalars().all()

        # Calculate analytics
        total_searches = len(searches)
        unique_queries = len(set(s.query for s in searches))

        # Average execution time
        execution_times = [s.execution_time_ms for s in searches if s.execution_time_ms]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0

        # Top queries (most frequent)
        query_counts = {}
        for search in searches:
            query_counts[search.query] = query_counts.get(search.query, 0) + 1

        top_queries = [
            {"query": query, "count": count}
            for query, count in sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        # Search types distribution
        search_types_dist = {}
        for search in searches:
            search_types_dist[search.search_type] = search_types_dist.get(search.search_type, 0) + 1

        # Searches by hour
        searches_by_hour = {}
        for search in searches:
            hour = search.created_at.hour
            searches_by_hour[hour] = searches_by_hour.get(hour, 0) + 1

        # Searches by day
        searches_by_day = {}
        for search in searches:
            day = search.created_at.strftime('%Y-%m-%d')
            searches_by_day[day] = searches_by_day.get(day, 0) + 1

        # Average results count
        results_counts = [s.results_count for s in searches if s.results_count is not None]
        avg_results = sum(results_counts) / len(results_counts) if results_counts else 0.0

        return {
            "total_searches": total_searches,
            "unique_queries": unique_queries,
            "avg_execution_time_ms": avg_execution_time,
            "top_queries": top_queries,
            "search_types_distribution": search_types_dist,
            "searches_by_hour": searches_by_hour,
            "searches_by_day": searches_by_day,
            "avg_results_count": avg_results
        }

    except Exception as e:
        logger.error(f"Error getting search analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get search analytics: {str(e)}"
        )


@router.delete("/cleanup", response_model=CleanupResponse)
async def cleanup_old_searches(
    days: int = Query(90, ge=30, le=365, description="Delete searches older than this many days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cleanup old search history records.

    Args:
        days: Delete searches older than this many days
        db: Database session
        current_user: Authenticated user

    Returns:
        Cleanup operation result
    """
    try:
        # Calculate date threshold
        date_threshold = datetime.utcnow() - timedelta(days=days)

        # Get old searches
        query = select(SearchHistory).where(
            and_(
                SearchHistory.user_id == current_user.id,
                SearchHistory.created_at < date_threshold
            )
        )

        result = await db.execute(query)
        old_searches = result.scalars().all()

        deleted_count = len(old_searches)

        # Delete old searches
        for search in old_searches:
            await db.delete(search)

        await db.commit()

        logger.info(f"Cleaned up {deleted_count} old searches for user {current_user.id}")

        return {
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} search records older than {days} days"
        }

    except Exception as e:
        logger.error(f"Error cleaning up search history: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup search history: {str(e)}"
        )
