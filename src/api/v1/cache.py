"""
Cache Management API Endpoints

Provides admin endpoints for cache monitoring and management:
- Cache statistics and health checks
- Cache invalidation by pattern
- Full cache clearing
- Performance monitoring
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from src.auth.security import get_current_user, require_admin
from src.models.user import User
from src.services.cache_service import get_cache_service, AsyncCacheService

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class CacheStatsResponse(BaseModel):
    """Cache statistics response."""
    backend: str = Field(..., description="Cache backend (redis or memory)")
    namespace: str = Field(..., description="Cache namespace")
    statistics: Dict[str, Any] = Field(..., description="Cache statistics")


class CacheHealthResponse(BaseModel):
    """Cache health check response."""
    healthy: bool = Field(..., description="Overall health status")
    backend: str = Field(..., description="Cache backend")
    write_success: bool = Field(..., description="Write operation success")
    read_success: bool = Field(..., description="Read operation success")
    timestamp: str = Field(..., description="Check timestamp")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class CacheClearResponse(BaseModel):
    """Cache clear operation response."""
    success: bool = Field(..., description="Operation success")
    message: str = Field(..., description="Operation message")
    keys_deleted: Optional[int] = Field(None, description="Number of keys deleted")


class CachePatternRequest(BaseModel):
    """Request body for pattern-based cache operations."""
    pattern: str = Field(..., description="Key pattern to match (e.g., 'user:*')")
    category: Optional[str] = Field(None, description="Optional cache category")


@router.get("/cache/stats", response_model=CacheStatsResponse, tags=["cache"])
async def get_cache_statistics(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get cache statistics.

    Requires admin privileges.

    Returns:
        Cache statistics including hit rate, operations count, etc.
    """
    try:
        cache = get_cache_service()

        if not cache._initialized:
            await cache.initialize()

        stats = cache.get_statistics()
        return stats

    except Exception as e:
        logger.error(f"Error fetching cache statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch cache statistics: {str(e)}"
        )


@router.get("/cache/health", response_model=CacheHealthResponse, tags=["cache"])
async def check_cache_health(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Perform cache health check.

    Tests read/write operations to verify cache is operational.

    Returns:
        Health status information
    """
    try:
        cache = get_cache_service()

        if not cache._initialized:
            await cache.initialize()

        health = await cache.health_check()
        return health

    except Exception as e:
        logger.error(f"Error checking cache health: {e}")
        return {
            "healthy": False,
            "backend": "unknown",
            "error": str(e),
            "write_success": False,
            "read_success": False,
            "timestamp": ""
        }


@router.delete("/cache/clear", response_model=CacheClearResponse, tags=["cache"])
async def clear_all_cache(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Clear all cache entries.

    WARNING: This clears the entire cache namespace. Use with caution!

    Requires admin privileges.

    Returns:
        Operation result
    """
    try:
        cache = get_cache_service()

        if not cache._initialized:
            await cache.initialize()

        success = await cache.clear_all()

        if success:
            logger.info(f"Cache cleared by user {current_user.email}")
            return {
                "success": True,
                "message": "Cache cleared successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to clear cache"
            }

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.post("/cache/clear-pattern", response_model=CacheClearResponse, tags=["cache"])
async def clear_cache_by_pattern(
    request: CachePatternRequest,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Clear cache entries matching a pattern.

    Allows selective cache invalidation based on key patterns.

    Examples:
        - Pattern: "serp:*" clears all SERP results
        - Pattern: "crawl:*" clears all website crawl data
        - Pattern: "user:123:*" clears all data for user 123

    Requires admin privileges.

    Args:
        request: Pattern and optional category

    Returns:
        Operation result with count of deleted keys
    """
    try:
        cache = get_cache_service()

        if not cache._initialized:
            await cache.initialize()

        deleted_count = await cache.clear_pattern(
            pattern=request.pattern,
            category=request.category
        )

        logger.info(
            f"Cache pattern '{request.pattern}' cleared by user {current_user.email}, "
            f"{deleted_count} keys deleted"
        )

        return {
            "success": True,
            "message": f"Cleared {deleted_count} cache entries matching pattern",
            "keys_deleted": deleted_count
        }

    except Exception as e:
        logger.error(f"Error clearing cache pattern: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache pattern: {str(e)}"
        )


@router.post("/cache/reset-stats", tags=["cache"])
async def reset_cache_statistics(
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """
    Reset cache statistics counters.

    Useful for monitoring cache performance over specific time periods.

    Requires admin privileges.

    Returns:
        Success message
    """
    try:
        cache = get_cache_service()

        if not cache._initialized:
            await cache.initialize()

        cache.reset_statistics()

        logger.info(f"Cache statistics reset by user {current_user.email}")

        return {
            "success": True,
            "message": "Cache statistics reset successfully"
        }

    except Exception as e:
        logger.error(f"Error resetting cache statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset cache statistics: {str(e)}"
        )


@router.delete("/cache/{category}", response_model=CacheClearResponse, tags=["cache"])
async def clear_cache_category(
    category: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Clear all cache entries in a specific category.

    Categories organize cache entries by data type:
        - website_crawl: Website crawl results
        - serp_results: SERP analysis data
        - keyword_data: Keyword information
        - api_responses: API response caches

    Requires admin privileges.

    Args:
        category: Category name to clear

    Returns:
        Operation result with count of deleted keys
    """
    try:
        cache = get_cache_service()

        if not cache._initialized:
            await cache.initialize()

        # Clear all keys in category
        deleted_count = await cache.clear_pattern(
            pattern="*",
            category=category
        )

        logger.info(
            f"Cache category '{category}' cleared by user {current_user.email}, "
            f"{deleted_count} keys deleted"
        )

        return {
            "success": True,
            "message": f"Cleared {deleted_count} entries from category '{category}'",
            "keys_deleted": deleted_count
        }

    except Exception as e:
        logger.error(f"Error clearing cache category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache category: {str(e)}"
        )
