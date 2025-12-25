"""YouTube Data API service.

This module provides integration with YouTube Data API for video analytics,
channel statistics, and competitor video tracking.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings

logger = logging.getLogger(__name__)


class YouTubeAPIError(Exception):
    """Exception raised for YouTube API errors."""
    pass


class YouTubeService:
    """Service for YouTube Data API integration.

    Provides methods for video search, channel analytics, video metrics,
    and competitor tracking on YouTube.
    """

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: Optional[str] = None, daily_quota: int = 10000):
        """Initialize the YouTube service.

        Args:
            api_key: YouTube Data API key
            daily_quota: Maximum daily quota units
        """
        self.api_key = api_key or getattr(settings, 'YOUTUBE_API_KEY', None)

        if not self.api_key:
            logger.warning("YouTube API key not configured")

        self.daily_quota = daily_quota
        self.quota_used = 0
        self.client = httpx.AsyncClient(timeout=30.0)

    def _check_quota(self, cost: int) -> bool:
        """Check if quota allows the operation.

        Args:
            cost: Quota cost of the operation

        Returns:
            bool: True if quota available
        """
        if self.quota_used + cost > self.daily_quota:
            logger.warning(f"YouTube API quota would be exceeded. Used: {self.quota_used}/{self.daily_quota}")
            return False

        self.quota_used += cost
        return True

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def search_videos(
        self,
        query: str,
        max_results: int = 10,
        order: str = 'relevance',
        published_after: Optional[datetime] = None,
        video_duration: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Search for videos on YouTube.

        Args:
            query: Search query string
            max_results: Maximum number of results (max 50)
            order: Sort order (relevance, date, rating, viewCount, title)
            published_after: Only include videos after this date
            video_duration: Filter by duration (short, medium, long)
            **kwargs: Additional search parameters

        Returns:
            Dict containing video search results

        Raises:
            YouTubeAPIError: If search fails
        """
        # Quota cost: 100 units
        if not self._check_quota(100):
            raise YouTubeAPIError("Daily quota exceeded")

        params = {
            'key': self.api_key,
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': min(max_results, 50),
            'order': order,
            **kwargs
        }

        if published_after:
            params['publishedAfter'] = published_after.isoformat() + 'Z'

        if video_duration:
            params['videoDuration'] = video_duration

        try:
            response = await self.client.get(f"{self.BASE_URL}/search", params=params)
            response.raise_for_status()
            data = response.json()

            return self._parse_search_response(data)

        except httpx.HTTPError as e:
            logger.error(f"YouTube search error: {str(e)}")
            raise YouTubeAPIError(f"Video search failed: {str(e)}")

    def _parse_search_response(self, data: Dict) -> Dict[str, Any]:
        """Parse YouTube search API response.

        Args:
            data: Raw API response

        Returns:
            Structured search results
        """
        items = data.get('items', [])

        videos = []
        for item in items:
            video_id = item.get('id', {}).get('videoId')
            snippet = item.get('snippet', {})

            videos.append({
                'videoId': video_id,
                'title': snippet.get('title'),
                'description': snippet.get('description'),
                'channelId': snippet.get('channelId'),
                'channelTitle': snippet.get('channelTitle'),
                'publishedAt': snippet.get('publishedAt'),
                'thumbnails': snippet.get('thumbnails', {}),
            })

        return {
            'totalResults': data.get('pageInfo', {}).get('totalResults', 0),
            'resultsPerPage': data.get('pageInfo', {}).get('resultsPerPage', 0),
            'videos': videos,
            'nextPageToken': data.get('nextPageToken'),
            'quotaRemaining': self.daily_quota - self.quota_used
        }

    async def get_channel_stats(
        self,
        channel_id: str
    ) -> Dict[str, Any]:
        """Get statistics for a YouTube channel.

        Args:
            channel_id: YouTube channel ID

        Returns:
            Dict containing channel statistics

        Raises:
            YouTubeAPIError: If request fails
        """
        # Quota cost: 1 unit
        if not self._check_quota(1):
            raise YouTubeAPIError("Daily quota exceeded")

        params = {
            'key': self.api_key,
            'part': 'snippet,statistics,contentDetails,brandingSettings',
            'id': channel_id
        }

        try:
            response = await self.client.get(f"{self.BASE_URL}/channels", params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get('items'):
                raise YouTubeAPIError(f"Channel not found: {channel_id}")

            return self._parse_channel_stats(data['items'][0])

        except httpx.HTTPError as e:
            logger.error(f"YouTube channel stats error: {str(e)}")
            raise YouTubeAPIError(f"Failed to get channel stats: {str(e)}")

    def _parse_channel_stats(self, item: Dict) -> Dict[str, Any]:
        """Parse channel statistics from API response.

        Args:
            item: Channel item from API response

        Returns:
            Structured channel statistics
        """
        snippet = item.get('snippet', {})
        statistics = item.get('statistics', {})
        branding = item.get('brandingSettings', {}).get('channel', {})

        return {
            'channelId': item.get('id'),
            'title': snippet.get('title'),
            'description': snippet.get('description'),
            'customUrl': snippet.get('customUrl'),
            'publishedAt': snippet.get('publishedAt'),
            'thumbnails': snippet.get('thumbnails', {}),
            'country': branding.get('country'),
            'keywords': branding.get('keywords'),
            'statistics': {
                'viewCount': int(statistics.get('viewCount', 0)),
                'subscriberCount': int(statistics.get('subscriberCount', 0)),
                'videoCount': int(statistics.get('videoCount', 0)),
                'hiddenSubscriberCount': statistics.get('hiddenSubscriberCount', False)
            },
            'quotaRemaining': self.daily_quota - self.quota_used
        }

    async def get_video_analytics(
        self,
        video_id: str
    ) -> Dict[str, Any]:
        """Get detailed analytics for a video.

        Args:
            video_id: YouTube video ID

        Returns:
            Dict containing video analytics

        Raises:
            YouTubeAPIError: If request fails
        """
        # Quota cost: 1 unit
        if not self._check_quota(1):
            raise YouTubeAPIError("Daily quota exceeded")

        params = {
            'key': self.api_key,
            'part': 'snippet,statistics,contentDetails,status',
            'id': video_id
        }

        try:
            response = await self.client.get(f"{self.BASE_URL}/videos", params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get('items'):
                raise YouTubeAPIError(f"Video not found: {video_id}")

            return self._parse_video_analytics(data['items'][0])

        except httpx.HTTPError as e:
            logger.error(f"YouTube video analytics error: {str(e)}")
            raise YouTubeAPIError(f"Failed to get video analytics: {str(e)}")

    def _parse_video_analytics(self, item: Dict) -> Dict[str, Any]:
        """Parse video analytics from API response.

        Args:
            item: Video item from API response

        Returns:
            Structured video analytics
        """
        snippet = item.get('snippet', {})
        statistics = item.get('statistics', {})
        content_details = item.get('contentDetails', {})
        status = item.get('status', {})

        # Calculate engagement rate
        views = int(statistics.get('viewCount', 0))
        likes = int(statistics.get('likeCount', 0))
        comments = int(statistics.get('commentCount', 0))
        engagement_rate = ((likes + comments) / views * 100) if views > 0 else 0

        return {
            'videoId': item.get('id'),
            'title': snippet.get('title'),
            'description': snippet.get('description'),
            'channelId': snippet.get('channelId'),
            'channelTitle': snippet.get('channelTitle'),
            'publishedAt': snippet.get('publishedAt'),
            'thumbnails': snippet.get('thumbnails', {}),
            'tags': snippet.get('tags', []),
            'categoryId': snippet.get('categoryId'),
            'duration': content_details.get('duration'),
            'definition': content_details.get('definition'),
            'caption': content_details.get('caption'),
            'privacyStatus': status.get('privacyStatus'),
            'statistics': {
                'viewCount': views,
                'likeCount': likes,
                'commentCount': comments,
                'favoriteCount': int(statistics.get('favoriteCount', 0)),
                'engagementRate': round(engagement_rate, 2)
            },
            'quotaRemaining': self.daily_quota - self.quota_used
        }

    async def track_competitor_videos(
        self,
        competitor_id: str,
        max_results: int = 10,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Track competitor's recent video activity.

        Args:
            competitor_id: Competitor's channel ID
            max_results: Maximum number of videos to retrieve
            days_back: Number of days to look back

        Returns:
            Dict containing competitor video activity

        Raises:
            YouTubeAPIError: If request fails
        """
        # Get competitor channel stats first
        channel_stats = await self.get_channel_stats(competitor_id)

        # Search for recent videos from this channel
        published_after = datetime.utcnow() - timedelta(days=days_back)

        # Quota cost: 100 units for search
        if not self._check_quota(100):
            raise YouTubeAPIError("Daily quota exceeded")

        params = {
            'key': self.api_key,
            'part': 'snippet',
            'channelId': competitor_id,
            'maxResults': min(max_results, 50),
            'order': 'date',
            'type': 'video',
            'publishedAfter': published_after.isoformat() + 'Z'
        }

        try:
            response = await self.client.get(f"{self.BASE_URL}/search", params=params)
            response.raise_for_status()
            data = response.json()

            videos = data.get('items', [])

            # Get detailed stats for each video (1 unit per video)
            video_analytics = []
            for video_item in videos[:10]:  # Limit to 10 to save quota
                video_id = video_item.get('id', {}).get('videoId')
                if video_id:
                    try:
                        analytics = await self.get_video_analytics(video_id)
                        video_analytics.append(analytics)
                    except YouTubeAPIError as e:
                        logger.warning(f"Failed to get analytics for video {video_id}: {str(e)}")

            # Calculate aggregate metrics
            total_views = sum(v['statistics']['viewCount'] for v in video_analytics)
            total_engagement = sum(
                v['statistics']['likeCount'] + v['statistics']['commentCount']
                for v in video_analytics
            )
            avg_engagement_rate = (
                sum(v['statistics']['engagementRate'] for v in video_analytics) / len(video_analytics)
                if video_analytics else 0
            )

            return {
                'channelId': competitor_id,
                'channelTitle': channel_stats['title'],
                'period': f'{days_back} days',
                'channelStats': channel_stats['statistics'],
                'recentVideos': len(video_analytics),
                'totalViews': total_views,
                'totalEngagement': total_engagement,
                'averageEngagementRate': round(avg_engagement_rate, 2),
                'videos': video_analytics,
                'analyzedAt': datetime.utcnow().isoformat(),
                'quotaRemaining': self.daily_quota - self.quota_used
            }

        except httpx.HTTPError as e:
            logger.error(f"Competitor video tracking error: {str(e)}")
            raise YouTubeAPIError(f"Failed to track competitor videos: {str(e)}")

    async def get_trending_videos(
        self,
        region_code: str = 'US',
        category_id: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """Get trending videos for a region.

        Args:
            region_code: Region code (ISO 3166-1 alpha-2)
            category_id: Optional video category ID
            max_results: Maximum number of results

        Returns:
            Dict containing trending videos

        Raises:
            YouTubeAPIError: If request fails
        """
        # Quota cost: 1 unit
        if not self._check_quota(1):
            raise YouTubeAPIError("Daily quota exceeded")

        params = {
            'key': self.api_key,
            'part': 'snippet,statistics',
            'chart': 'mostPopular',
            'regionCode': region_code,
            'maxResults': min(max_results, 50)
        }

        if category_id:
            params['videoCategoryId'] = category_id

        try:
            response = await self.client.get(f"{self.BASE_URL}/videos", params=params)
            response.raise_for_status()
            data = response.json()

            videos = []
            for item in data.get('items', []):
                videos.append(self._parse_video_analytics(item))

            return {
                'regionCode': region_code,
                'categoryId': category_id,
                'totalResults': len(videos),
                'videos': videos,
                'quotaRemaining': self.daily_quota - self.quota_used
            }

        except httpx.HTTPError as e:
            logger.error(f"Trending videos error: {str(e)}")
            raise YouTubeAPIError(f"Failed to get trending videos: {str(e)}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
