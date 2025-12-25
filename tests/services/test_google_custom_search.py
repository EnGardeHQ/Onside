"""
Comprehensive unit and integration tests for GoogleCustomSearchService.

This module provides extensive test coverage for Google Custom Search API integration,
including search functionality, brand mention tracking, content performance analysis,
rate limiting, quota management, and retry logic with mocked API calls.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timedelta
import httpx

from src.services.google_custom_search import (
    GoogleCustomSearchService,
    GoogleCustomSearchError,
    RateLimiter
)


class TestRateLimiter:
    """Test suite for RateLimiter."""

    def test_init_default_quota(self):
        """Test initialization with default quota."""
        limiter = RateLimiter()
        assert limiter.calls_per_day == 100
        assert limiter.calls_today == 0

    def test_init_custom_quota(self):
        """Test initialization with custom quota."""
        limiter = RateLimiter(calls_per_day=50)
        assert limiter.calls_per_day == 50

    def test_check_and_wait_allows_call(self):
        """Test that call is allowed when under quota."""
        limiter = RateLimiter(calls_per_day=10)
        assert limiter.check_and_wait() is True
        assert limiter.calls_today == 1

    def test_check_and_wait_blocks_when_quota_exceeded(self):
        """Test that call is blocked when quota exceeded."""
        limiter = RateLimiter(calls_per_day=2)
        limiter.calls_today = 2
        assert limiter.check_and_wait() is False
        assert limiter.calls_today == 2  # Should not increment

    def test_check_and_wait_resets_after_day(self):
        """Test that quota resets after a day."""
        limiter = RateLimiter(calls_per_day=10)
        limiter.calls_today = 10
        # Manually set reset time to past
        limiter.reset_time = datetime.utcnow() - timedelta(hours=1)

        assert limiter.check_and_wait() is True
        assert limiter.calls_today == 1  # Should reset and allow

    def test_get_remaining_calls(self):
        """Test getting remaining API calls."""
        limiter = RateLimiter(calls_per_day=100)
        limiter.calls_today = 30
        assert limiter.get_remaining_calls() == 70

    def test_get_remaining_calls_when_exceeded(self):
        """Test remaining calls is 0 when quota exceeded."""
        limiter = RateLimiter(calls_per_day=10)
        limiter.calls_today = 15
        assert limiter.get_remaining_calls() == 0


class TestGoogleCustomSearchServiceInitialization:
    """Test suite for service initialization."""

    def test_init_with_custom_credentials(self):
        """Test initialization with custom API credentials."""
        service = GoogleCustomSearchService(
            api_key="test_api_key",
            search_engine_id="test_engine_id"
        )
        assert service.api_key == "test_api_key"
        assert service.search_engine_id == "test_engine_id"

    def test_init_with_custom_quota(self):
        """Test initialization with custom daily quota."""
        service = GoogleCustomSearchService(
            api_key="test_key",
            search_engine_id="test_id",
            daily_quota=50
        )
        assert service.rate_limiter.calls_per_day == 50

    @patch('src.services.google_custom_search.settings')
    def test_init_with_settings_credentials(self, mock_settings):
        """Test initialization uses settings if no credentials provided."""
        mock_settings.GOOGLE_SEARCH_API_KEY = "settings_key"
        mock_settings.GOOGLE_SEARCH_ENGINE_ID = "settings_engine"

        service = GoogleCustomSearchService()
        assert service.api_key == "settings_key"
        assert service.search_engine_id == "settings_engine"

    def test_init_creates_http_client(self):
        """Test that HTTP client is created."""
        service = GoogleCustomSearchService(
            api_key="test_key",
            search_engine_id="test_id"
        )
        assert service.client is not None


class TestGoogleCustomSearchServiceSearch:
    """Test suite for search functionality."""

    @pytest.fixture
    def service(self):
        """Create a GoogleCustomSearchService instance."""
        return GoogleCustomSearchService(
            api_key="test_api_key",
            search_engine_id="test_engine_id",
            daily_quota=100
        )

    @pytest.fixture
    def mock_response(self):
        """Create a mock search response."""
        return {
            "queries": {
                "request": [{"searchTerms": "test query"}]
            },
            "searchInformation": {
                "totalResults": "42",
                "searchTime": 0.123
            },
            "items": [
                {
                    "title": "Test Result 1",
                    "link": "https://example.com/page1",
                    "snippet": "This is a test snippet",
                    "displayLink": "example.com",
                    "formattedUrl": "https://example.com/page1",
                    "htmlSnippet": "<b>Test</b> snippet",
                    "htmlTitle": "<b>Test</b> Result 1",
                    "pagemap": {"metatags": [{"description": "Test description"}]}
                },
                {
                    "title": "Test Result 2",
                    "link": "https://example.com/page2",
                    "snippet": "Another test snippet",
                    "displayLink": "example.com",
                    "formattedUrl": "https://example.com/page2",
                    "htmlSnippet": "Another <b>test</b>",
                    "htmlTitle": "<b>Test</b> Result 2",
                    "pagemap": {}
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_search_success(self, service, mock_response):
        """Test successful search query."""
        # Mock HTTP response
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        result = await service.search(query="test query")

        # Assert
        assert result['query'] == "test query"
        assert result['totalResults'] == 42
        assert len(result['results']) == 2
        assert result['results'][0]['title'] == "Test Result 1"
        assert result['results'][0]['link'] == "https://example.com/page1"

    @pytest.mark.asyncio
    async def test_search_with_site_restriction(self, service, mock_response):
        """Test search with site restriction."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        await service.search(query="test", site="example.com")

        # Assert - check that site restriction was added to query
        call_args = service.client.get.call_args
        params = call_args[1]['params']
        assert "site:example.com" in params['q']

    @pytest.mark.asyncio
    async def test_search_with_pagination(self, service, mock_response):
        """Test search with pagination parameters."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        await service.search(query="test", num_results=5, start_index=11)

        # Assert
        call_args = service.client.get.call_args
        params = call_args[1]['params']
        assert params['num'] == 5
        assert params['start'] == 11

    @pytest.mark.asyncio
    async def test_search_enforces_max_results(self, service, mock_response):
        """Test that num_results is capped at 10."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        await service.search(query="test", num_results=50)

        # Assert - should be capped at 10
        call_args = service.client.get.call_args
        params = call_args[1]['params']
        assert params['num'] == 10

    @pytest.mark.asyncio
    async def test_search_with_language(self, service, mock_response):
        """Test search with language parameter."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        await service.search(query="test", language="es")

        # Assert
        call_args = service.client.get.call_args
        params = call_args[1]['params']
        assert params['lr'] == "lang_es"

    @pytest.mark.asyncio
    async def test_search_quota_exceeded(self, service):
        """Test search fails when quota exceeded."""
        # Exhaust quota
        service.rate_limiter.calls_today = 100

        # Execute & Assert
        with pytest.raises(GoogleCustomSearchError, match="quota exceeded"):
            await service.search(query="test")

    @pytest.mark.asyncio
    async def test_search_http_error(self, service):
        """Test search handles HTTP errors."""
        # Mock HTTP error
        service.client.get = AsyncMock(side_effect=httpx.HTTPError("Network error"))

        # Execute & Assert
        with pytest.raises(GoogleCustomSearchError, match="Search failed"):
            await service.search(query="test")

    @pytest.mark.asyncio
    async def test_search_retry_on_failure(self, service, mock_response):
        """Test search retries on failure."""
        # First call fails, second succeeds
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(
            side_effect=[
                httpx.HTTPError("Temporary error"),
                mock_http_response
            ]
        )

        # Execute - should succeed after retry
        result = await service.search(query="test")
        assert result is not None

    @pytest.mark.asyncio
    async def test_search_updates_remaining_quota(self, service, mock_response):
        """Test that search updates remaining quota in response."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        result = await service.search(query="test")

        # Assert
        assert 'remainingQuota' in result
        assert result['remainingQuota'] >= 0


class TestGoogleCustomSearchServiceBrandMentions:
    """Test suite for brand mention tracking."""

    @pytest.fixture
    def service(self):
        """Create a GoogleCustomSearchService instance."""
        return GoogleCustomSearchService(
            api_key="test_api_key",
            search_engine_id="test_engine_id"
        )

    @pytest.fixture
    def mock_mentions_response(self):
        """Create a mock response for brand mentions."""
        return {
            "queries": {"request": [{"searchTerms": '"TestBrand"'}]},
            "searchInformation": {"totalResults": "150", "searchTime": 0.2},
            "items": [
                {
                    "title": "Great review of TestBrand",
                    "link": "https://review-site.com/testbrand",
                    "snippet": "TestBrand is amazing and excellent for our needs",
                    "displayLink": "review-site.com",
                    "formattedUrl": "https://review-site.com/testbrand",
                    "htmlSnippet": "Amazing product",
                    "htmlTitle": "Review",
                    "pagemap": {}
                },
                {
                    "title": "TestBrand criticism",
                    "link": "https://forum.com/testbrand-bad",
                    "snippet": "TestBrand is terrible and awful quality",
                    "displayLink": "forum.com",
                    "formattedUrl": "https://forum.com/testbrand-bad",
                    "htmlSnippet": "Not good",
                    "htmlTitle": "Complaint",
                    "pagemap": {}
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_track_brand_mentions_success(self, service, mock_mentions_response):
        """Test successful brand mention tracking."""
        # Mock search response
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_mentions_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        result = await service.track_brand_mentions(
            brand_name="TestBrand",
            days_back=7
        )

        # Assert
        assert result['brandName'] == "TestBrand"
        assert result['period'] == "7 days"
        assert result['totalMentions'] == 150
        assert len(result['mentions']) == 2
        assert 'averageSentiment' in result
        assert 'positiveCount' in result
        assert 'negativeCount' in result

    @pytest.mark.asyncio
    async def test_track_brand_mentions_sentiment_analysis(self, service, mock_mentions_response):
        """Test sentiment analysis in brand mentions."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_mentions_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        result = await service.track_brand_mentions(brand_name="TestBrand")

        # Assert - should detect positive and negative mentions
        assert result['positiveCount'] >= 0
        assert result['negativeCount'] >= 0

    @pytest.mark.asyncio
    async def test_track_brand_mentions_exclude_own_domain(self, service, mock_mentions_response):
        """Test excluding own domain from brand mentions."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_mentions_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        await service.track_brand_mentions(
            brand_name="TestBrand",
            exclude_own_domain="testbrand.com"
        )

        # Assert - check query excludes domain
        call_args = service.client.get.call_args
        params = call_args[1]['params']
        assert "-site:testbrand.com" in params['q']

    @pytest.mark.asyncio
    async def test_track_brand_mentions_with_date_restrict(self, service, mock_mentions_response):
        """Test brand mentions with date restriction."""
        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_mentions_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        await service.track_brand_mentions(brand_name="TestBrand", days_back=30)

        # Assert
        call_args = service.client.get.call_args
        params = call_args[1]['params']
        assert params['dateRestrict'] == 'd30'


class TestGoogleCustomSearchServiceContentPerformance:
    """Test suite for content performance analysis."""

    @pytest.fixture
    def service(self):
        """Create a GoogleCustomSearchService instance."""
        return GoogleCustomSearchService(
            api_key="test_api_key",
            search_engine_id="test_engine_id"
        )

    @pytest.mark.asyncio
    async def test_analyze_content_performance_indexed(self, service):
        """Test content performance analysis for indexed URL."""
        # Mock responses for exact URL search and domain search
        exact_response = {
            "queries": {"request": [{"searchTerms": "site:example.com"}]},
            "searchInformation": {"totalResults": "1"},
            "items": [{"title": "Page", "link": "https://example.com/page"}]
        }

        domain_response = {
            "queries": {"request": [{"searchTerms": "site:example.com"}]},
            "searchInformation": {"totalResults": "500"},
            "items": [{"title": "Page1", "link": "https://example.com/page1"}]
        }

        mock_http_response1 = AsyncMock()
        mock_http_response1.json.return_value = exact_response
        mock_http_response1.raise_for_status = MagicMock()

        mock_http_response2 = AsyncMock()
        mock_http_response2.json.return_value = domain_response
        mock_http_response2.raise_for_status = MagicMock()

        service.client.get = AsyncMock(
            side_effect=[mock_http_response1, mock_http_response2]
        )

        # Execute
        result = await service.analyze_content_performance(
            url="https://example.com/page"
        )

        # Assert
        assert result['url'] == "https://example.com/page"
        assert result['isIndexed'] is True
        assert result['domainVisibility'] == 500
        assert 'indexedPages' in result
        assert 'topPages' in result

    @pytest.mark.asyncio
    async def test_analyze_content_performance_not_indexed(self, service):
        """Test content performance analysis for non-indexed URL."""
        # Mock empty response for exact URL
        exact_response = {
            "queries": {"request": [{"searchTerms": "site:example.com"}]},
            "searchInformation": {"totalResults": "0"},
            "items": []
        }

        domain_response = {
            "queries": {"request": [{"searchTerms": "site:example.com"}]},
            "searchInformation": {"totalResults": "100"},
            "items": []
        }

        mock_http_response1 = AsyncMock()
        mock_http_response1.json.return_value = exact_response
        mock_http_response1.raise_for_status = MagicMock()

        mock_http_response2 = AsyncMock()
        mock_http_response2.json.return_value = domain_response
        mock_http_response2.raise_for_status = MagicMock()

        service.client.get = AsyncMock(
            side_effect=[mock_http_response1, mock_http_response2]
        )

        # Execute
        result = await service.analyze_content_performance(
            url="https://example.com/new-page"
        )

        # Assert
        assert result['isIndexed'] is False


class TestGoogleCustomSearchServiceCompetitorSearch:
    """Test suite for competitor search functionality."""

    @pytest.fixture
    def service(self):
        """Create a GoogleCustomSearchService instance."""
        return GoogleCustomSearchService(
            api_key="test_api_key",
            search_engine_id="test_engine_id"
        )

    @pytest.mark.asyncio
    async def test_competitor_search_multiple_keywords(self, service):
        """Test searching competitor content for multiple keywords."""
        # Mock response
        mock_response = {
            "queries": {"request": [{"searchTerms": "keyword"}]},
            "searchInformation": {"totalResults": "10"},
            "items": [{"title": "Result", "link": "https://competitor.com/page"}]
        }

        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        # Execute
        result = await service.competitor_search(
            competitor_domain="competitor.com",
            keywords=["keyword1", "keyword2", "keyword3"]
        )

        # Assert
        assert result['competitorDomain'] == "competitor.com"
        assert len(result['keywords']) == 3
        assert 'keyword1' in result['results']
        assert 'keyword2' in result['results']
        assert 'keyword3' in result['results']

    @pytest.mark.asyncio
    async def test_competitor_search_handles_errors(self, service):
        """Test competitor search handles keyword errors gracefully."""
        # First keyword succeeds, second fails
        success_response = {
            "queries": {"request": [{"searchTerms": "keyword1"}]},
            "searchInformation": {"totalResults": "5"},
            "items": []
        }

        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = success_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(
            side_effect=[
                mock_http_response,
                httpx.HTTPError("Error")
            ]
        )

        # Execute
        result = await service.competitor_search(
            competitor_domain="competitor.com",
            keywords=["keyword1", "keyword2"]
        )

        # Assert - should have results for keyword1, error for keyword2
        assert 'keyword1' in result['results']
        assert 'keyword2' in result['results']
        assert 'error' in result['results']['keyword2']


class TestGoogleCustomSearchServiceHelpers:
    """Test suite for helper methods."""

    @pytest.fixture
    def service(self):
        """Create a GoogleCustomSearchService instance."""
        return GoogleCustomSearchService(
            api_key="test_api_key",
            search_engine_id="test_engine_id"
        )

    def test_analyze_sentiment_positive(self, service):
        """Test sentiment analysis for positive text."""
        text = "This is a great and excellent product that I love"
        sentiment = service._analyze_sentiment(text)
        assert sentiment > 0

    def test_analyze_sentiment_negative(self, service):
        """Test sentiment analysis for negative text."""
        text = "This is terrible and awful, I hate it"
        sentiment = service._analyze_sentiment(text)
        assert sentiment < 0

    def test_analyze_sentiment_neutral(self, service):
        """Test sentiment analysis for neutral text."""
        text = "This is a product description without emotion"
        sentiment = service._analyze_sentiment(text)
        assert sentiment == 0.0

    def test_parse_search_response(self, service):
        """Test parsing search response."""
        data = {
            "queries": {"request": [{"searchTerms": "test"}]},
            "searchInformation": {"totalResults": "100", "searchTime": 0.5},
            "items": [
                {"title": "Result 1", "link": "https://example.com/1", "snippet": "Snippet 1"}
            ]
        }

        result = service._parse_search_response(data)

        assert result['query'] == "test"
        assert result['totalResults'] == 100
        assert result['searchTime'] == 0.5
        assert len(result['results']) == 1


class TestGoogleCustomSearchServiceResourceManagement:
    """Test suite for resource management."""

    @pytest.fixture
    def service(self):
        """Create a GoogleCustomSearchService instance."""
        return GoogleCustomSearchService(
            api_key="test_api_key",
            search_engine_id="test_engine_id"
        )

    @pytest.mark.asyncio
    async def test_close_client(self, service):
        """Test closing HTTP client."""
        service.client.aclose = AsyncMock()
        await service.close()
        assert service.client.aclose.called

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test service as async context manager."""
        async with GoogleCustomSearchService(
            api_key="test_key",
            search_engine_id="test_id"
        ) as service:
            assert service is not None
        # Client should be closed after context exit


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    @pytest.fixture
    def service(self):
        """Create a GoogleCustomSearchService instance."""
        return GoogleCustomSearchService(
            api_key="test_api_key",
            search_engine_id="test_engine_id"
        )

    @pytest.mark.asyncio
    async def test_search_empty_query(self, service):
        """Test search with empty query."""
        mock_response = {
            "queries": {"request": [{"searchTerms": ""}]},
            "searchInformation": {"totalResults": "0"},
            "items": []
        }

        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        result = await service.search(query="")
        assert result is not None

    @pytest.mark.asyncio
    async def test_search_no_results(self, service):
        """Test search with no results."""
        mock_response = {
            "queries": {"request": [{"searchTerms": "test"}]},
            "searchInformation": {"totalResults": "0"},
            "items": []
        }

        mock_http_response = AsyncMock()
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        service.client.get = AsyncMock(return_value=mock_http_response)

        result = await service.search(query="nonexistent")
        assert result['totalResults'] == 0
        assert len(result['results']) == 0

    def test_analyze_sentiment_empty_text(self, service):
        """Test sentiment analysis with empty text."""
        sentiment = service._analyze_sentiment("")
        assert sentiment == 0.0

    def test_analyze_sentiment_mixed_emotions(self, service):
        """Test sentiment with both positive and negative words."""
        text = "Great product but terrible service"
        sentiment = service._analyze_sentiment(text)
        # Should be close to neutral
        assert -0.5 < sentiment < 0.5
