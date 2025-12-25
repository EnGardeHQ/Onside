"""Pydantic schemas for SEO Services (Google Custom Search & YouTube) API endpoints."""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


# Google Custom Search Schemas

class GoogleSearchRequest(BaseModel):
    """Schema for Google Custom Search request."""
    query: str = Field(..., min_length=1, description="Search query")
    max_results: int = Field(10, ge=1, le=100, description="Maximum results to return")
    language: Optional[str] = Field(None, description="Search language")
    date_restrict: Optional[str] = Field(None, description="Date restriction (d[number], w[number], m[number], y[number])")
    site_search: Optional[str] = Field(None, description="Restrict to specific site")
    exclude_site: Optional[str] = Field(None, description="Exclude specific site")


class GoogleSearchResult(BaseModel):
    """Schema for individual search result."""
    title: str
    link: str
    snippet: str
    displayed_link: Optional[str]
    pagemap: Optional[Dict[str, Any]]


class GoogleSearchResponse(BaseModel):
    """Schema for Google Custom Search response."""
    query: str
    total_results: int
    search_time: float
    results: List[GoogleSearchResult]
    next_page_token: Optional[str]


class BrandMentionRequest(BaseModel):
    """Schema for brand mention tracking request."""
    brand_name: str = Field(..., min_length=1, description="Brand name to track")
    keywords: List[str] = Field(default_factory=list, description="Additional keywords")
    competitors: List[str] = Field(default_factory=list, description="Competitor brands")
    date_restrict: Optional[str] = Field(None, description="Date restriction")
    max_results: int = Field(50, ge=1, le=100, description="Maximum results")


class BrandMentionResponse(BaseModel):
    """Schema for brand mention tracking response."""
    brand_name: str
    mentions_found: int
    sentiment_distribution: Dict[str, int]
    top_sources: List[Dict[str, Any]]
    competitor_comparison: Dict[str, int]
    trending_topics: List[str]


class ContentPerformanceRequest(BaseModel):
    """Schema for content performance analysis request."""
    url: str = Field(..., description="Content URL to analyze")
    competitors: List[str] = Field(default_factory=list, description="Competitor URLs")
    metrics: List[str] = Field(
        default=["ranking", "backlinks", "shares"],
        description="Metrics to analyze"
    )


class ContentPerformanceResponse(BaseModel):
    """Schema for content performance response."""
    url: str
    ranking_position: Optional[int]
    indexed_pages: int
    backlink_estimate: int
    social_shares: int
    competitor_comparison: Dict[str, Dict[str, Any]]
    recommendations: List[str]


# YouTube Service Schemas

class YouTubeSearchRequest(BaseModel):
    """Schema for YouTube video search request."""
    query: str = Field(..., min_length=1, description="Search query")
    max_results: int = Field(10, ge=1, le=50, description="Maximum results")
    order: str = Field("relevance", description="Sort order")
    published_after: Optional[datetime] = Field(None, description="Filter by publish date")
    video_duration: Optional[str] = Field(None, description="Video duration filter")
    video_type: Optional[str] = Field(None, description="Video type filter")

    @validator('order')
    def validate_order(cls, v):
        """Validate order parameter."""
        valid_orders = ['relevance', 'date', 'rating', 'viewCount', 'title']
        if v not in valid_orders:
            raise ValueError(f"Order must be one of: {', '.join(valid_orders)}")
        return v


class YouTubeVideoResult(BaseModel):
    """Schema for YouTube video result."""
    video_id: str
    title: str
    description: str
    channel_id: str
    channel_title: str
    published_at: datetime
    thumbnail_url: Optional[str]
    view_count: Optional[int]
    like_count: Optional[int]
    comment_count: Optional[int]


class YouTubeSearchResponse(BaseModel):
    """Schema for YouTube search response."""
    query: str
    total_results: int
    videos: List[YouTubeVideoResult]
    next_page_token: Optional[str]


class YouTubeChannelStatsRequest(BaseModel):
    """Schema for YouTube channel stats request."""
    channel_id: str = Field(..., description="YouTube channel ID")


class YouTubeChannelStatsResponse(BaseModel):
    """Schema for YouTube channel statistics."""
    channel_id: str
    title: str
    description: Optional[str]
    subscriber_count: int
    video_count: int
    view_count: int
    avg_views_per_video: float
    upload_frequency: Optional[str]
    top_videos: List[YouTubeVideoResult]


class YouTubeVideoAnalyticsRequest(BaseModel):
    """Schema for YouTube video analytics request."""
    video_id: str = Field(..., description="YouTube video ID")


class YouTubeVideoAnalyticsResponse(BaseModel):
    """Schema for YouTube video analytics."""
    video_id: str
    title: str
    channel_title: str
    published_at: datetime
    view_count: int
    like_count: int
    dislike_count: int
    comment_count: int
    favorite_count: int
    duration: str
    tags: List[str]
    category_id: str
    engagement_rate: float
    likes_to_views_ratio: float
    comments_to_views_ratio: float


class CompetitorVideoTrackingRequest(BaseModel):
    """Schema for competitor video tracking request."""
    competitor_id: int = Field(..., description="Competitor ID")
    channel_id: Optional[str] = Field(None, description="YouTube channel ID")
    max_videos: int = Field(20, ge=1, le=50, description="Maximum videos to fetch")
    published_after: Optional[datetime] = Field(None, description="Filter by publish date")


class CompetitorVideoTrackingResponse(BaseModel):
    """Schema for competitor video tracking response."""
    competitor_id: int
    channel_id: str
    channel_title: str
    videos_analyzed: int
    total_views: int
    total_likes: int
    total_comments: int
    avg_engagement_rate: float
    top_performing_videos: List[YouTubeVideoResult]
    upload_frequency: str
    trending_topics: List[str]
