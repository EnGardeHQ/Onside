"""
Comprehensive unit and integration tests for YouTubeService.

This module provides extensive test coverage for YouTube Data API integration,
including video search, channel statistics, video analytics, competitor tracking,
quota management, and error handling with mocked API calls.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timedelta
import httpx

from src.services.youtube_service import (
    YouTubeService,
    YouTubeAPIError
)


class TestYouTubeServiceInitialization:
    """Test suite for service initialization."""

    def test_init_with_custom_api_key(self):
        """Test initialization with custom API key."""
        service = YouTubeService(api_key="test_api_key")
        assert service.api_key == "test_api_key"

    def test_init_with_custom_quota(self):
        """Test initialization with custom daily quota."""
        service = YouTubeService(api_key="test_key", daily_quota=5000)
        assert service.daily_quota == 5000
        assert service.quota_used == 0

    @patch('src.services.youtube_service.settings')
    def test_init_with_settings_api_key(self, mock_settings):
        """Test initialization uses settings if no API key provided."""
        mock_settings.YOUTUBE_API_KEY = "settings_key"
        service = YouTubeService()
        assert service.api_key == "settings_key"

    def test_init_creates_http_client(self):
        """Test that HTTP client is created."""
        service = YouTubeService(api_key="test_key")
        assert service.client is not None

    def test_check_quota_allows_operation(self):
        """Test quota check allows operation when under limit."""
        service = YouTubeService(api_key="test_key", daily_quota=1000)
        assert service._check_quota(100) is True
        assert service.quota_used == 100

    def test_check_quota_blocks_when_exceeded(self):
        """Test quota check blocks when limit would be exceeded."""
        service = YouTubeService(api_key="test_key", daily_quota=100)
        service.quota_used = 90
        assert service._check_quota(20) is False
        assert service.quota_used == 90  # Should not increment


class TestYouTubeServiceVideoSearch:
    """Test suite for video search functionality."""

    @pytest.fixture
    def service(self):
        """Create a YouTubeService instance."""
        return YouTubeService(api_key="test_api_key", daily_quota=10000)

    @pytest.fixture
    def mock_search_response(self):
        """Create a mock video search response."""
        return {
            "pageInfo": {
                "totalResults": 1000,
                "resultsPerPage": 10
            },
            "nextPageToken": "NEXT_PAGE_TOKEN",
            "items": [
                {
                    "id": {"videoId": "video1"},
                    "snippet": {
                        "title": "Test Video 1",
                        "description": "This is a test video description",
                        "channelId": "channel123",
                        "channelTitle": "Test Channel",
                        "publishedAt": "2024-01-15T10:30:00Z",
                        "thumbnails": {
                            "default": {"url": "https://i.ytimg.com/vi/video1/default.jpg"}
                        }
                    }
                },
                {
                    "id": {"videoId": "video2"},
                    "snippet": {
                        "title": "Test Video 2",
                        "description": "Another test video",
                        "channelId": "channel456",
                        "channelTitle": "Another Channel",
                        "publishedAt": "2024-01-14T15:00:00Z",
                        "thumbnails": {
                            "default": {"url": "https://i.ytimg.com/vi/video2/default.jpg"}
                        }
                    }
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_search_videos_success(self, service, mock_search_response):
        """Test successful video search."""
        # Mock HTTP response
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_search_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        result = await service.search_videos(query="test query")

        # Assert
        assert result['totalResults'] == 1000
        assert result['resultsPerPage'] == 10
        assert len(result['videos']) == 2
        assert result['videos'][0]['videoId'] == "video1"
        assert result['videos'][0]['title'] == "Test Video 1"
        assert result['nextPageToken'] == "NEXT_PAGE_TOKEN"
        assert 'quotaRemaining' in result

    @pytest.mark.asyncio
    async def test_search_videos_with_max_results(self, service, mock_search_response):
        """Test video search with max_results parameter."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_search_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        await service.search_videos(query="test", max_results=25)

        # Assert
        call_args = service.client.get.call_args
        params = call_args[1]['params']
        assert params['maxResults'] == 25

    @pytest.mark.asyncio
    async def test_search_videos_enforces_max_limit(self, service, mock_search_response):
        """Test that max_results is capped at 50."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_search_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        await service.search_videos(query="test", max_results=100)

        # Assert
        call_args = service.client.get.call_args
        params = call_args[1]['params']
        assert params['maxResults'] == 50

    @pytest.mark.asyncio
    async def test_search_videos_with_order(self, service, mock_search_response):
        """Test video search with order parameter."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_search_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        await service.search_videos(query="test", order="viewCount")

        # Assert
        call_args = service.client.get.call_args
        params = call_args[1]['params']
        assert params['order'] == "viewCount"

    @pytest.mark.asyncio
    async def test_search_videos_with_published_after(self, service, mock_search_response):
        """Test video search with publishedAfter filter."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_search_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        published_after = datetime(2024, 1, 1, 0, 0, 0)
        await service.search_videos(query="test", published_after=published_after)

        # Assert
        call_args = service.client.get.call_args
        params = call_args[1]['params']
        assert 'publishedAfter' in params
        assert params['publishedAfter'].startswith("2024-01-01")

    @pytest.mark.asyncio
    async def test_search_videos_with_duration_filter(self, service, mock_search_response):
        """Test video search with duration filter."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_search_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        await service.search_videos(query="test", video_duration="short")

        # Assert
        call_args = service.client.get.call_args
        params = call_args[1]['params']
        assert params['videoDuration'] == "short"

    @pytest.mark.asyncio
    async def test_search_videos_quota_exceeded(self, service):
        """Test search fails when quota exceeded."""
        service.quota_used = 10000

        # Execute & Assert
        with pytest.raises(YouTubeAPIError, match="quota exceeded"):
            await service.search_videos(query="test")

    @pytest.mark.asyncio
    async def test_search_videos_http_error(self, service):
        """Test search handles HTTP errors."""
        service.client.get = AsyncMock(side_effect=httpx.HTTPError("Network error"))

        # Execute & Assert
        with pytest.raises(YouTubeAPIError, match="search failed"):
            await service.search_videos(query="test")


class TestYouTubeServiceChannelStats:
    """Test suite for channel statistics."""

    @pytest.fixture
    def service(self):
        """Create a YouTubeService instance."""
        return YouTubeService(api_key="test_api_key", daily_quota=10000)

    @pytest.fixture
    def mock_channel_response(self):
        """Create a mock channel statistics response."""
        return {
            "items": [
                {
                    "id": "channel123",
                    "snippet": {
                        "title": "Test Channel",
                        "description": "This is a test channel",
                        "customUrl": "@testchannel",
                        "publishedAt": "2020-01-01T00:00:00Z",
                        "thumbnails": {
                            "default": {"url": "https://yt3.ggpht.com/channel.jpg"}
                        }
                    },
                    "statistics": {
                        "viewCount": "1000000",
                        "subscriberCount": "50000",
                        "videoCount": "200",
                        "hiddenSubscriberCount": False
                    },
                    "brandingSettings": {
                        "channel": {
                            "country": "US",
                            "keywords": "test channel keywords"
                        }
                    }
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_get_channel_stats_success(self, service, mock_channel_response):
        """Test successful channel statistics retrieval."""
        # Mock HTTP response
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_channel_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        result = await service.get_channel_stats(channel_id="channel123")

        # Assert
        assert result['channelId'] == "channel123"
        assert result['title'] == "Test Channel"
        assert result['statistics']['viewCount'] == 1000000
        assert result['statistics']['subscriberCount'] == 50000
        assert result['statistics']['videoCount'] == 200
        assert result['country'] == "US"

    @pytest.mark.asyncio
    async def test_get_channel_stats_not_found(self, service):
        """Test channel not found error."""
        # Mock empty response
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = {"items": []}
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute & Assert
        with pytest.raises(YouTubeAPIError, match="Channel not found"):
            await service.get_channel_stats(channel_id="nonexistent")

    @pytest.mark.asyncio
    async def test_get_channel_stats_quota_cost(self, service, mock_channel_response):
        """Test that getting channel stats costs 1 quota unit."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_channel_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        initial_quota = service.quota_used
        await service.get_channel_stats(channel_id="channel123")

        # Assert
        assert service.quota_used == initial_quota + 1


class TestYouTubeServiceVideoAnalytics:
    """Test suite for video analytics."""

    @pytest.fixture
    def service(self):
        """Create a YouTubeService instance."""
        return YouTubeService(api_key="test_api_key", daily_quota=10000)

    @pytest.fixture
    def mock_video_response(self):
        """Create a mock video analytics response."""
        return {
            "items": [
                {
                    "id": "video123",
                    "snippet": {
                        "title": "Test Video",
                        "description": "Video description",
                        "channelId": "channel123",
                        "channelTitle": "Test Channel",
                        "publishedAt": "2024-01-01T00:00:00Z",
                        "thumbnails": {},
                        "tags": ["test", "video", "tutorial"],
                        "categoryId": "22"
                    },
                    "statistics": {
                        "viewCount": "10000",
                        "likeCount": "500",
                        "commentCount": "100",
                        "favoriteCount": "0"
                    },
                    "contentDetails": {
                        "duration": "PT10M30S",
                        "definition": "hd",
                        "caption": "true"
                    },
                    "status": {
                        "privacyStatus": "public"
                    }
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_get_video_analytics_success(self, service, mock_video_response):
        """Test successful video analytics retrieval."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_video_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        result = await service.get_video_analytics(video_id="video123")

        # Assert
        assert result['videoId'] == "video123"
        assert result['title'] == "Test Video"
        assert result['statistics']['viewCount'] == 10000
        assert result['statistics']['likeCount'] == 500
        assert result['statistics']['commentCount'] == 100
        assert 'engagementRate' in result['statistics']
        assert result['tags'] == ["test", "video", "tutorial"]

    @pytest.mark.asyncio
    async def test_get_video_analytics_calculates_engagement(self, service, mock_video_response):
        """Test engagement rate calculation."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_video_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        result = await service.get_video_analytics(video_id="video123")

        # Assert
        # Engagement = (likes + comments) / views * 100 = (500 + 100) / 10000 * 100 = 6%
        assert result['statistics']['engagementRate'] == 6.0

    @pytest.mark.asyncio
    async def test_get_video_analytics_not_found(self, service):
        """Test video not found error."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = {"items": []}
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute & Assert
        with pytest.raises(YouTubeAPIError, match="Video not found"):
            await service.get_video_analytics(video_id="nonexistent")

    @pytest.mark.asyncio
    async def test_get_video_analytics_zero_views(self, service):
        """Test engagement calculation with zero views."""
        # Mock video with zero views
        response = {
            "items": [{
                "id": "video123",
                "snippet": {"title": "Test", "channelId": "ch1", "channelTitle": "Ch", "publishedAt": "2024-01-01T00:00:00Z", "thumbnails": {}, "tags": [], "categoryId": "22"},
                "statistics": {"viewCount": "0", "likeCount": "0", "commentCount": "0", "favoriteCount": "0"},
                "contentDetails": {"duration": "PT5M", "definition": "hd", "caption": "false"},
                "status": {"privacyStatus": "public"}
            }]
        }

        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        result = await service.get_video_analytics(video_id="video123")

        # Assert - engagement should be 0 when views are 0
        assert result['statistics']['engagementRate'] == 0


class TestYouTubeServiceCompetitorTracking:
    """Test suite for competitor video tracking."""

    @pytest.fixture
    def service(self):
        """Create a YouTubeService instance."""
        return YouTubeService(api_key="test_api_key", daily_quota=10000)

    @pytest.fixture
    def mock_competitor_search(self):
        """Create mock competitor search response."""
        return {
            "items": [
                {
                    "id": {"videoId": "comp_video1"},
                    "snippet": {
                        "title": "Competitor Video 1",
                        "channelId": "competitor123",
                        "publishedAt": "2024-01-15T00:00:00Z"
                    }
                }
            ]
        }

    @pytest.fixture
    def mock_competitor_channel(self):
        """Create mock competitor channel response."""
        return {
            "items": [{
                "id": "competitor123",
                "snippet": {"title": "Competitor Channel", "publishedAt": "2020-01-01T00:00:00Z", "thumbnails": {}},
                "statistics": {"viewCount": "5000000", "subscriberCount": "100000", "videoCount": "500", "hiddenSubscriberCount": False},
                "brandingSettings": {"channel": {}}
            }]
        }

    @pytest.fixture
    def mock_competitor_video(self):
        """Create mock competitor video response."""
        return {
            "items": [{
                "id": "comp_video1",
                "snippet": {"title": "Video", "channelId": "comp123", "channelTitle": "Comp", "publishedAt": "2024-01-01T00:00:00Z", "thumbnails": {}, "tags": [], "categoryId": "22"},
                "statistics": {"viewCount": "50000", "likeCount": "2000", "commentCount": "500", "favoriteCount": "0"},
                "contentDetails": {"duration": "PT15M", "definition": "hd", "caption": "true"},
                "status": {"privacyStatus": "public"}
            }]
        }

    @pytest.mark.asyncio
    async def test_track_competitor_videos_success(
        self, service, mock_competitor_channel, mock_competitor_search, mock_competitor_video
    ):
        """Test successful competitor video tracking."""
        # Mock multiple responses
        mock_channel_response = AsyncMock()
        mock_channel_response.json.return_value = mock_competitor_channel
        mock_channel_response.raise_for_status = MagicMock()

        mock_search_response = AsyncMock()
        mock_search_response.json.return_value = mock_competitor_search
        mock_search_response.raise_for_status = MagicMock()

        mock_video_response = AsyncMock()
        mock_video_response.json.return_value = mock_competitor_video
        mock_video_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(
            side_effect=[
                mock_channel_response,
                mock_search_response,
                mock_video_response
            ]
        )

        # Execute
        result = await service.track_competitor_videos(
            competitor_id="competitor123",
            max_results=10,
            days_back=30
        )

        # Assert
        assert result['channelId'] == "competitor123"
        assert result['period'] == "30 days"
        assert 'channelStats' in result
        assert 'recentVideos' in result
        assert 'totalViews' in result
        assert 'averageEngagementRate' in result

    @pytest.mark.asyncio
    async def test_track_competitor_videos_calculates_metrics(
        self, service, mock_competitor_channel, mock_competitor_search, mock_competitor_video
    ):
        """Test competitor tracking calculates aggregate metrics."""
        mock_channel_response = AsyncMock()
        mock_channel_response.json.return_value = mock_competitor_channel
        mock_channel_response.raise_for_status = MagicMock()

        mock_search_response = AsyncMock()
        mock_search_response.json.return_value = mock_competitor_search
        mock_search_response.raise_for_status = MagicMock()

        mock_video_response = AsyncMock()
        mock_video_response.json.return_value = mock_competitor_video
        mock_video_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(
            side_effect=[
                mock_channel_response,
                mock_search_response,
                mock_video_response
            ]
        )

        # Execute
        result = await service.track_competitor_videos(competitor_id="competitor123")

        # Assert
        assert result['totalViews'] > 0
        assert result['totalEngagement'] > 0
        assert result['averageEngagementRate'] >= 0

    @pytest.mark.asyncio
    async def test_track_competitor_videos_handles_video_errors(
        self, service, mock_competitor_channel, mock_competitor_search
    ):
        """Test competitor tracking handles individual video errors."""
        mock_channel_response = AsyncMock()
        mock_channel_response.json.return_value = mock_competitor_channel
        mock_channel_response.raise_for_status = MagicMock()

        mock_search_response = AsyncMock()
        mock_search_response.json.return_value = mock_competitor_search
        mock_search_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(
            side_effect=[
                mock_channel_response,
                mock_search_response,
                httpx.HTTPError("Video not available")
            ]
        )

        # Execute - should not raise exception
        result = await service.track_competitor_videos(competitor_id="competitor123")

        # Assert - should still return results
        assert result is not None


class TestYouTubeServiceTrendingVideos:
    """Test suite for trending videos."""

    @pytest.fixture
    def service(self):
        """Create a YouTubeService instance."""
        return YouTubeService(api_key="test_api_key", daily_quota=10000)

    @pytest.fixture
    def mock_trending_response(self):
        """Create mock trending videos response."""
        return {
            "items": [
                {
                    "id": "trending1",
                    "snippet": {"title": "Trending Video", "channelId": "ch1", "channelTitle": "Channel", "publishedAt": "2024-01-01T00:00:00Z", "thumbnails": {}, "tags": [], "categoryId": "10"},
                    "statistics": {"viewCount": "1000000", "likeCount": "50000", "commentCount": "10000", "favoriteCount": "0"},
                    "contentDetails": {"duration": "PT5M", "definition": "hd", "caption": "true"},
                    "status": {"privacyStatus": "public"}
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_get_trending_videos_success(self, service, mock_trending_response):
        """Test successful trending videos retrieval."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_trending_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        result = await service.get_trending_videos(region_code="US")

        # Assert
        assert result['regionCode'] == "US"
        assert len(result['videos']) == 1
        assert result['videos'][0]['videoId'] == "trending1"

    @pytest.mark.asyncio
    async def test_get_trending_videos_with_category(self, service, mock_trending_response):
        """Test trending videos with category filter."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_trending_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        await service.get_trending_videos(region_code="US", category_id="10")

        # Assert
        call_args = service.client.get.call_args
        params = call_args[1]['params']
        assert params['videoCategoryId'] == "10"

    @pytest.mark.asyncio
    async def test_get_trending_videos_quota_cost(self, service, mock_trending_response):
        """Test trending videos quota cost."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_trending_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        initial_quota = service.quota_used
        await service.get_trending_videos()

        # Assert - costs 1 unit
        assert service.quota_used == initial_quota + 1


class TestYouTubeServiceResourceManagement:
    """Test suite for resource management."""

    @pytest.fixture
    def service(self):
        """Create a YouTubeService instance."""
        return YouTubeService(api_key="test_api_key")

    @pytest.mark.asyncio
    async def test_close_client(self, service):
        """Test closing HTTP client."""
        service.client.aclose = AsyncMock()
        await service.close()
        assert service.client.aclose.called

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test service as async context manager."""
        async with YouTubeService(api_key="test_key") as service:
            assert service is not None
        # Client should be closed after context exit


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    @pytest.fixture
    def service(self):
        """Create a YouTubeService instance."""
        return YouTubeService(api_key="test_api_key", daily_quota=10000)

    @pytest.mark.asyncio
    async def test_search_empty_query(self, service):
        """Test search with empty query."""
        mock_response = {
            "pageInfo": {"totalResults": 0, "resultsPerPage": 0},
            "items": []
        }

        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        result = await service.search_videos(query="")
        assert result is not None

    @pytest.mark.asyncio
    async def test_search_no_results(self, service):
        """Test search with no results."""
        mock_response = {
            "pageInfo": {"totalResults": 0, "resultsPerPage": 0},
            "items": []
        }

        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        result = await service.search_videos(query="nonexistent_query_12345")
        assert result['totalResults'] == 0
        assert len(result['videos']) == 0

    @pytest.mark.asyncio
    async def test_video_analytics_missing_statistics(self, service):
        """Test video analytics with missing statistics."""
        response = {
            "items": [{
                "id": "video123",
                "snippet": {"title": "Test", "channelId": "ch", "channelTitle": "Ch", "publishedAt": "2024-01-01T00:00:00Z", "thumbnails": {}, "tags": [], "categoryId": "22"},
                "statistics": {},  # Empty statistics
                "contentDetails": {"duration": "PT5M", "definition": "hd", "caption": "false"},
                "status": {"privacyStatus": "public"}
            }]
        }

        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute - should handle gracefully
        result = await service.get_video_analytics(video_id="video123")
        assert result['statistics']['viewCount'] == 0

    @pytest.mark.asyncio
    async def test_channel_stats_hidden_subscribers(self, service):
        """Test channel stats with hidden subscriber count."""
        response = {
            "items": [{
                "id": "channel123",
                "snippet": {"title": "Test", "publishedAt": "2020-01-01T00:00:00Z", "thumbnails": {}},
                "statistics": {"viewCount": "1000", "subscriberCount": "0", "videoCount": "10", "hiddenSubscriberCount": True},
                "brandingSettings": {"channel": {}}
            }]
        }

        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        result = await service.get_channel_stats(channel_id="channel123")
        assert result['statistics']['hiddenSubscriberCount'] is True

    def test_quota_check_exactly_at_limit(self, service):
        """Test quota check when exactly at limit."""
        service.quota_used = 9900
        service.daily_quota = 10000
        assert service._check_quota(100) is True
        assert service.quota_used == 10000

    def test_quota_check_one_over_limit(self, service):
        """Test quota check when one unit over limit."""
        service.quota_used = 9999
        service.daily_quota = 10000
        assert service._check_quota(2) is False
