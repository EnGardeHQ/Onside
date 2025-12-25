"""API endpoints for SEO Services (Google Custom Search & YouTube).

This module provides REST API endpoints for Google Custom Search and YouTube Data API
integration for SEO and content performance analysis.
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.config import get_db
from src.auth.security import get_current_user
from src.models.user import User
from src.services.google_custom_search import GoogleCustomSearchService
from src.services.youtube_service import YouTubeService
from src.schemas.seo_services import (
    GoogleSearchRequest,
    GoogleSearchResponse,
    BrandMentionRequest,
    BrandMentionResponse,
    ContentPerformanceRequest,
    ContentPerformanceResponse,
    YouTubeSearchRequest,
    YouTubeSearchResponse,
    YouTubeChannelStatsRequest,
    YouTubeChannelStatsResponse,
    YouTubeVideoAnalyticsRequest,
    YouTubeVideoAnalyticsResponse,
    CompetitorVideoTrackingRequest,
    CompetitorVideoTrackingResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/seo", tags=["seo-services"])


# Google Custom Search Endpoints

@router.post("/google-search", response_model=GoogleSearchResponse)
async def perform_google_search(
    search_request: GoogleSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform a Google Custom Search.

    Args:
        search_request: Search configuration
        db: Database session
        current_user: Authenticated user

    Returns:
        Search results from Google Custom Search API
    """
    try:
        google_service = GoogleCustomSearchService()

        # Perform search
        results = await google_service.search(
            query=search_request.query,
            max_results=search_request.max_results,
            language=search_request.language,
            date_restrict=search_request.date_restrict,
            site_search=search_request.site_search,
            exclude_site=search_request.exclude_site
        )

        logger.info(f"Performed Google search for query: {search_request.query}")

        # Format response
        return {
            "query": search_request.query,
            "total_results": results.get("total_results", 0),
            "search_time": results.get("search_time", 0.0),
            "results": results.get("items", []),
            "next_page_token": results.get("next_page_token")
        }

    except Exception as e:
        logger.error(f"Error performing Google search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform Google search: {str(e)}"
        )


@router.post("/brand-mentions", response_model=BrandMentionResponse)
async def track_brand_mentions(
    mention_request: BrandMentionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track brand mentions across the web.

    Args:
        mention_request: Brand mention tracking configuration
        db: Database session
        current_user: Authenticated user

    Returns:
        Brand mention analysis
    """
    try:
        google_service = GoogleCustomSearchService()

        # Track brand mentions
        mentions = await google_service.track_brand_mentions(
            brand_name=mention_request.brand_name,
            keywords=mention_request.keywords,
            competitors=mention_request.competitors,
            date_restrict=mention_request.date_restrict,
            max_results=mention_request.max_results
        )

        logger.info(f"Tracked brand mentions for: {mention_request.brand_name}")

        return {
            "brand_name": mention_request.brand_name,
            "mentions_found": mentions.get("mentions_found", 0),
            "sentiment_distribution": mentions.get("sentiment_distribution", {}),
            "top_sources": mentions.get("top_sources", []),
            "competitor_comparison": mentions.get("competitor_comparison", {}),
            "trending_topics": mentions.get("trending_topics", [])
        }

    except Exception as e:
        logger.error(f"Error tracking brand mentions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track brand mentions: {str(e)}"
        )


@router.post("/content-performance", response_model=ContentPerformanceResponse)
async def analyze_content_performance(
    performance_request: ContentPerformanceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze content performance using Google Custom Search.

    Args:
        performance_request: Content performance analysis configuration
        db: Database session
        current_user: Authenticated user

    Returns:
        Content performance analysis
    """
    try:
        google_service = GoogleCustomSearchService()

        # Analyze content performance
        performance = await google_service.analyze_content_performance(
            url=performance_request.url,
            competitors=performance_request.competitors,
            metrics=performance_request.metrics
        )

        logger.info(f"Analyzed content performance for: {performance_request.url}")

        return {
            "url": performance_request.url,
            "ranking_position": performance.get("ranking_position"),
            "indexed_pages": performance.get("indexed_pages", 0),
            "backlink_estimate": performance.get("backlink_estimate", 0),
            "social_shares": performance.get("social_shares", 0),
            "competitor_comparison": performance.get("competitor_comparison", {}),
            "recommendations": performance.get("recommendations", [])
        }

    except Exception as e:
        logger.error(f"Error analyzing content performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze content performance: {str(e)}"
        )


# YouTube Service Endpoints

@router.post("/youtube/search", response_model=YouTubeSearchResponse)
async def search_youtube_videos(
    search_request: YouTubeSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for YouTube videos.

    Args:
        search_request: YouTube search configuration
        db: Database session
        current_user: Authenticated user

    Returns:
        YouTube video search results
    """
    try:
        youtube_service = YouTubeService()

        # Search videos
        results = await youtube_service.search_videos(
            query=search_request.query,
            max_results=search_request.max_results,
            order=search_request.order,
            published_after=search_request.published_after,
            video_duration=search_request.video_duration,
            video_type=search_request.video_type
        )

        logger.info(f"Performed YouTube search for: {search_request.query}")

        return {
            "query": search_request.query,
            "total_results": results.get("total_results", 0),
            "videos": results.get("items", []),
            "next_page_token": results.get("next_page_token")
        }

    except Exception as e:
        logger.error(f"Error searching YouTube videos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search YouTube videos: {str(e)}"
        )


@router.get("/youtube/channel/{channel_id}/stats", response_model=YouTubeChannelStatsResponse)
async def get_youtube_channel_stats(
    channel_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get YouTube channel statistics.

    Args:
        channel_id: YouTube channel ID
        db: Database session
        current_user: Authenticated user

    Returns:
        YouTube channel statistics
    """
    try:
        youtube_service = YouTubeService()

        # Get channel stats
        stats = await youtube_service.get_channel_stats(channel_id)

        logger.info(f"Retrieved YouTube channel stats for: {channel_id}")

        return {
            "channel_id": channel_id,
            "title": stats.get("title", ""),
            "description": stats.get("description"),
            "subscriber_count": stats.get("subscriber_count", 0),
            "video_count": stats.get("video_count", 0),
            "view_count": stats.get("view_count", 0),
            "avg_views_per_video": stats.get("avg_views_per_video", 0.0),
            "upload_frequency": stats.get("upload_frequency"),
            "top_videos": stats.get("top_videos", [])
        }

    except Exception as e:
        logger.error(f"Error getting YouTube channel stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get YouTube channel stats: {str(e)}"
        )


@router.get("/youtube/video/{video_id}/analytics", response_model=YouTubeVideoAnalyticsResponse)
async def get_youtube_video_analytics(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get YouTube video analytics.

    Args:
        video_id: YouTube video ID
        db: Database session
        current_user: Authenticated user

    Returns:
        YouTube video analytics
    """
    try:
        youtube_service = YouTubeService()

        # Get video analytics
        analytics = await youtube_service.get_video_analytics(video_id)

        logger.info(f"Retrieved YouTube video analytics for: {video_id}")

        return {
            "video_id": video_id,
            "title": analytics.get("title", ""),
            "channel_title": analytics.get("channel_title", ""),
            "published_at": analytics.get("published_at"),
            "view_count": analytics.get("view_count", 0),
            "like_count": analytics.get("like_count", 0),
            "dislike_count": analytics.get("dislike_count", 0),
            "comment_count": analytics.get("comment_count", 0),
            "favorite_count": analytics.get("favorite_count", 0),
            "duration": analytics.get("duration", ""),
            "tags": analytics.get("tags", []),
            "category_id": analytics.get("category_id", ""),
            "engagement_rate": analytics.get("engagement_rate", 0.0),
            "likes_to_views_ratio": analytics.get("likes_to_views_ratio", 0.0),
            "comments_to_views_ratio": analytics.get("comments_to_views_ratio", 0.0)
        }

    except Exception as e:
        logger.error(f"Error getting YouTube video analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get YouTube video analytics: {str(e)}"
        )


@router.post("/youtube/competitor/{competitor_id}/videos", response_model=CompetitorVideoTrackingResponse)
async def track_competitor_videos(
    competitor_id: int,
    tracking_request: CompetitorVideoTrackingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track competitor videos on YouTube.

    Args:
        competitor_id: Competitor ID
        tracking_request: Video tracking configuration
        db: Database session
        current_user: Authenticated user

    Returns:
        Competitor video tracking analysis
    """
    try:
        youtube_service = YouTubeService()

        # Get competitor videos
        tracking = await youtube_service.track_competitor_videos(
            channel_id=tracking_request.channel_id,
            max_videos=tracking_request.max_videos,
            published_after=tracking_request.published_after
        )

        logger.info(f"Tracked competitor {competitor_id} videos")

        return {
            "competitor_id": competitor_id,
            "channel_id": tracking_request.channel_id or "",
            "channel_title": tracking.get("channel_title", ""),
            "videos_analyzed": tracking.get("videos_analyzed", 0),
            "total_views": tracking.get("total_views", 0),
            "total_likes": tracking.get("total_likes", 0),
            "total_comments": tracking.get("total_comments", 0),
            "avg_engagement_rate": tracking.get("avg_engagement_rate", 0.0),
            "top_performing_videos": tracking.get("top_performing_videos", []),
            "upload_frequency": tracking.get("upload_frequency", ""),
            "trending_topics": tracking.get("trending_topics", [])
        }

    except Exception as e:
        logger.error(f"Error tracking competitor videos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track competitor videos: {str(e)}"
        )
