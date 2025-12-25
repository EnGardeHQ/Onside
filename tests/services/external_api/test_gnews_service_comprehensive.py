"""
Comprehensive Unit Tests for GNewsService

This module implements comprehensive tests for the GNewsService to achieve 90%+ coverage.
Tests cover all public methods, error handling, edge cases, and integration scenarios.

Feature: GNews API Integration
As a developer,
I want comprehensive GNews service tests,
So I can ensure reliable news data collection.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from src.services.external_api.gnews_service import (
    GNewsService,
    GNewsAPIError,
    GNewsRateLimitError,
    GNewsAuthenticationError
)


@pytest.fixture
def mock_db_session():
    """Provide a mock database session."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_http_client():
    """Provide a mock HTTP client."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def gnews_service(mock_db_session, mock_http_client):
    """Provide a GNewsService instance with mocked dependencies."""
    service = GNewsService(
        db=mock_db_session,
        api_key="test_api_key",
        http_client=mock_http_client
    )
    return service


class TestGNewsServiceInitialization:
    """Test suite for service initialization."""

    @pytest.mark.asyncio
    async def test_initialization_with_api_key(self, mock_db_session, mock_http_client):
        """
        Given an API key and database session
        When I initialize the GNewsService
        Then the service should be configured correctly
        """
        # Act
        service = GNewsService(
            db=mock_db_session,
            api_key="test_key",
            http_client=mock_http_client
        )

        # Assert
        assert service.api_key == "test_key"
        assert service.db == mock_db_session
        assert service._http_client == mock_http_client

    @pytest.mark.asyncio
    async def test_initialization_without_api_key_uses_env(
        self, mock_db_session, mock_http_client
    ):
        """
        Given no API key is provided
        When I initialize the GNewsService
        Then it should read from environment variable
        """
        # Act
        with patch.dict('os.environ', {'GNEWS_API_KEY': 'env_key'}):
            service = GNewsService(
                db=mock_db_session,
                http_client=mock_http_client
            )

            # Assert
            assert service.api_key == "env_key"

    @pytest.mark.asyncio
    async def test_context_manager_creates_client_when_none(self, mock_db_session):
        """
        Given a service without an HTTP client
        When I use it as a context manager
        Then an HTTP client should be created automatically
        """
        # Arrange
        service = GNewsService(db=mock_db_session, api_key="test")

        # Act
        async with service as svc:
            # Assert
            assert svc._http_client is not None

    @pytest.mark.asyncio
    async def test_context_manager_closes_owned_client(self, mock_db_session):
        """
        Given a service that owns its HTTP client
        When exiting the context manager
        Then the client should be closed
        """
        # Arrange
        service = GNewsService(db=mock_db_session, api_key="test")

        # Act
        async with service:
            client = service._http_client

        # Assert - client should be closed and set to None
        assert service._http_client is None


class TestGNewsServiceRateLimiting:
    """Test suite for rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_allows_when_under_quota(self, gnews_service):
        """
        Given usage under the quota
        When I check the rate limit
        Then it should return True
        """
        # Arrange
        gnews_service.usage_repo.get_quota_status = AsyncMock(
            return_value={"is_exceeded": False, "quota_remaining": 500}
        )

        # Act
        result = await gnews_service._check_rate_limit()

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_blocks_when_quota_exceeded(self, gnews_service):
        """
        Given usage exceeding the quota
        When I check the rate limit
        Then it should return False
        """
        # Arrange
        gnews_service.usage_repo.get_quota_status = AsyncMock(
            return_value={"is_exceeded": True, "quota_remaining": 0}
        )

        # Act
        result = await gnews_service._check_rate_limit()

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_record_api_call_tracks_usage(self, gnews_service):
        """
        Given an API endpoint call
        When I record the API call
        Then usage should be tracked in the database
        """
        # Arrange
        gnews_service.usage_repo.record_usage = AsyncMock()

        # Act
        await gnews_service._record_api_call("search")

        # Assert
        gnews_service.usage_repo.record_usage.assert_called_once_with(
            api_name="gnews",
            endpoint="search",
            count=1
        )


class TestGNewsServiceRequestHandling:
    """Test suite for HTTP request handling."""

    @pytest.mark.asyncio
    async def test_make_request_raises_error_when_no_api_key(self, gnews_service):
        """
        Given a service without an API key
        When I make a request
        Then an authentication error should be raised
        """
        # Arrange
        gnews_service.api_key = None

        # Act & Assert
        with pytest.raises(GNewsAuthenticationError) as exc_info:
            await gnews_service._make_request("search", {"q": "test"})

        assert "not set" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_make_request_raises_error_when_quota_exceeded(self, gnews_service):
        """
        Given the rate limit is exceeded
        When I make a request
        Then a rate limit error should be raised
        """
        # Arrange
        gnews_service._check_rate_limit = AsyncMock(return_value=False)

        # Act & Assert
        with pytest.raises(GNewsRateLimitError) as exc_info:
            await gnews_service._make_request("search", {"q": "test"})

        assert "quota exceeded" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_make_request_successful(self, gnews_service, mock_http_client):
        """
        Given a valid API request
        When I make the request
        Then the response should be returned successfully
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"articles": []}
        mock_http_client.get = AsyncMock(return_value=mock_response)

        gnews_service._check_rate_limit = AsyncMock(return_value=True)
        gnews_service._record_api_call = AsyncMock()

        # Act
        result = await gnews_service._make_request("search", {"q": "test"})

        # Assert
        assert "articles" in result
        gnews_service._record_api_call.assert_called_once_with("search")

    @pytest.mark.asyncio
    async def test_make_request_retries_on_timeout(self, gnews_service, mock_http_client):
        """
        Given a request that times out
        When I make the request
        Then it should retry with exponential backoff
        """
        # Arrange
        mock_http_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        gnews_service._check_rate_limit = AsyncMock(return_value=True)
        gnews_service._record_api_call = AsyncMock()

        # Act & Assert
        with pytest.raises(GNewsAPIError) as exc_info:
            await gnews_service._make_request("search", {"q": "test"})

        assert "timed out" in str(exc_info.value).lower()
        assert mock_http_client.get.call_count == gnews_service.MAX_RETRIES + 1

    @pytest.mark.asyncio
    async def test_make_request_handles_401_error(self, gnews_service, mock_http_client):
        """
        Given an unauthorized response
        When I make the request
        Then an authentication error should be raised
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_http_client.get = AsyncMock(return_value=mock_response)

        gnews_service._check_rate_limit = AsyncMock(return_value=True)
        gnews_service._record_api_call = AsyncMock()

        # Act & Assert
        with pytest.raises(GNewsAuthenticationError):
            await gnews_service._make_request("search", {"q": "test"})

    @pytest.mark.asyncio
    async def test_make_request_handles_429_error(self, gnews_service, mock_http_client):
        """
        Given a rate limit response
        When I make the request
        Then a rate limit error should be raised
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_http_client.get = AsyncMock(return_value=mock_response)

        gnews_service._check_rate_limit = AsyncMock(return_value=True)
        gnews_service._record_api_call = AsyncMock()

        # Act & Assert
        with pytest.raises(GNewsRateLimitError) as exc_info:
            await gnews_service._make_request("search", {"q": "test"})

        assert exc_info.value.retry_after == 60


class TestGNewsServiceArticleParsing:
    """Test suite for article data parsing."""

    def test_generate_article_id_creates_hash(self, gnews_service):
        """
        Given an article with a URL
        When I generate an article ID
        Then it should return a consistent hash
        """
        # Arrange
        article = {"url": "https://example.com/article"}

        # Act
        article_id = gnews_service._generate_article_id(article)

        # Assert
        assert isinstance(article_id, str)
        assert len(article_id) == 64
        # Same URL should produce same ID
        assert article_id == gnews_service._generate_article_id(article)

    def test_parse_article_to_dict_complete_data(self, gnews_service):
        """
        Given a complete article from GNews API
        When I parse the article
        Then all fields should be correctly extracted
        """
        # Arrange
        article = {
            "title": "Test Article",
            "description": "Test description",
            "content": "Full content",
            "url": "https://example.com/article",
            "image": "https://example.com/image.jpg",
            "publishedAt": "2025-01-15T10:00:00Z",
            "source": {
                "name": "Example News",
                "url": "https://example.com"
            }
        }

        # Act
        result = gnews_service._parse_article_to_dict(
            article,
            query_term="test query",
            competitor_id=1
        )

        # Assert
        assert result["title"] == "Test Article"
        assert result["description"] == "Test description"
        assert result["url"] == "https://example.com/article"
        assert result["source_name"] == "Example News"
        assert result["query_term"] == "test query"
        assert result["competitor_id"] == 1

    def test_parse_article_handles_missing_fields(self, gnews_service):
        """
        Given an article with missing optional fields
        When I parse the article
        Then it should handle missing data gracefully
        """
        # Arrange
        article = {
            "url": "https://example.com/article",
            "source": {}
        }

        # Act
        result = gnews_service._parse_article_to_dict(article)

        # Assert
        assert result["title"] == ""
        assert result["description"] is None
        assert result["source_name"] == "Unknown"

    def test_parse_article_handles_invalid_date(self, gnews_service):
        """
        Given an article with an invalid date
        When I parse the article
        Then it should use current time as fallback
        """
        # Arrange
        article = {
            "url": "https://example.com/article",
            "publishedAt": "invalid-date",
            "source": {}
        }

        # Act
        result = gnews_service._parse_article_to_dict(article)

        # Assert
        assert result["published_at"] is not None


class TestGNewsServiceSearchNews:
    """Test suite for news search functionality."""

    @pytest.mark.asyncio
    async def test_search_news_returns_articles(self, gnews_service, mock_http_client):
        """
        Given a search query
        When I search for news
        Then articles should be returned
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": [
                {
                    "title": "Article 1",
                    "url": "https://example.com/1",
                    "source": {"name": "Source 1"},
                    "publishedAt": "2025-01-15T10:00:00Z"
                }
            ]
        }
        mock_http_client.get = AsyncMock(return_value=mock_response)

        gnews_service._check_rate_limit = AsyncMock(return_value=True)
        gnews_service._record_api_call = AsyncMock()
        gnews_service.gnews_repo.get_by_article_id = AsyncMock(return_value=None)
        gnews_service.gnews_repo.create_article = AsyncMock()

        # Act
        results = await gnews_service.search_news("test query")

        # Assert
        assert len(results) == 1
        assert results[0]["title"] == "Article 1"

    @pytest.mark.asyncio
    async def test_search_news_respects_max_results(self, gnews_service):
        """
        Given a max_results parameter
        When I search for news
        Then the parameter should be capped at 100
        """
        # Arrange
        gnews_service._make_request = AsyncMock(return_value={"articles": []})

        # Act
        await gnews_service.search_news("test", max_results=200)

        # Assert
        call_params = gnews_service._make_request.call_args[0][1]
        assert call_params["max"] <= 100

    @pytest.mark.asyncio
    async def test_search_news_with_date_filters(self, gnews_service):
        """
        Given date range filters
        When I search for news
        Then dates should be formatted correctly in the request
        """
        # Arrange
        gnews_service._make_request = AsyncMock(return_value={"articles": []})
        from_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        to_date = datetime(2025, 1, 15, tzinfo=timezone.utc)

        # Act
        await gnews_service.search_news(
            "test",
            from_date=from_date,
            to_date=to_date
        )

        # Assert
        call_params = gnews_service._make_request.call_args[0][1]
        assert "from" in call_params
        assert "to" in call_params

    @pytest.mark.asyncio
    async def test_search_news_skips_duplicate_articles(
        self, gnews_service, mock_http_client
    ):
        """
        Given search results with an article that already exists
        When I search for news
        Then duplicate articles should not be saved again
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": [
                {
                    "title": "Existing Article",
                    "url": "https://example.com/existing",
                    "source": {"name": "Source"},
                    "publishedAt": "2025-01-15T10:00:00Z"
                }
            ]
        }
        mock_http_client.get = AsyncMock(return_value=mock_response)

        gnews_service._check_rate_limit = AsyncMock(return_value=True)
        gnews_service._record_api_call = AsyncMock()
        gnews_service.gnews_repo.get_by_article_id = AsyncMock(
            return_value=MagicMock()  # Article exists
        )
        gnews_service.gnews_repo.create_article = AsyncMock()

        # Act
        results = await gnews_service.search_news("test")

        # Assert
        assert len(results) == 1
        gnews_service.gnews_repo.create_article.assert_not_called()


class TestGNewsServiceSentimentAnalysis:
    """Test suite for sentiment analysis."""

    @pytest.mark.asyncio
    async def test_analyze_news_sentiment_positive(self, gnews_service):
        """
        Given news articles with positive keywords
        When I analyze sentiment
        Then overall sentiment should be positive
        """
        # Arrange
        news_items = [
            {
                "article_id": "1",
                "title": "Company achieves success with innovation",
                "description": "Growth and profit increase"
            }
        ]

        # Act
        result = await gnews_service.analyze_news_sentiment(news_items)

        # Assert
        assert result["overall_sentiment"] == "positive"
        assert result["positive_count"] == 1
        assert result["sentiment_score"] > 0

    @pytest.mark.asyncio
    async def test_analyze_news_sentiment_negative(self, gnews_service):
        """
        Given news articles with negative keywords
        When I analyze sentiment
        Then overall sentiment should be negative
        """
        # Arrange
        news_items = [
            {
                "article_id": "1",
                "title": "Company faces crisis and lawsuit",
                "description": "Loss and decline reported"
            }
        ]

        # Act
        result = await gnews_service.analyze_news_sentiment(news_items)

        # Assert
        assert result["overall_sentiment"] == "negative"
        assert result["negative_count"] == 1
        assert result["sentiment_score"] < 0

    @pytest.mark.asyncio
    async def test_analyze_news_sentiment_neutral(self, gnews_service):
        """
        Given news articles without strong sentiment
        When I analyze sentiment
        Then overall sentiment should be neutral
        """
        # Arrange
        news_items = [
            {
                "article_id": "1",
                "title": "Company announces new product",
                "description": "Standard business update"
            }
        ]

        # Act
        result = await gnews_service.analyze_news_sentiment(news_items)

        # Assert
        assert result["overall_sentiment"] == "neutral"

    @pytest.mark.asyncio
    async def test_analyze_news_sentiment_empty_list(self, gnews_service):
        """
        Given an empty list of news items
        When I analyze sentiment
        Then it should return neutral with zero counts
        """
        # Act
        result = await gnews_service.analyze_news_sentiment([])

        # Assert
        assert result["overall_sentiment"] == "neutral"
        assert result["positive_count"] == 0
        assert result["negative_count"] == 0
        assert result["neutral_count"] == 0


class TestGNewsServiceUsageTracking:
    """Test suite for usage tracking functionality."""

    @pytest.mark.asyncio
    async def test_get_usage_status_returns_quota_info(self, gnews_service):
        """
        Given API usage tracking
        When I check usage status
        Then quota information should be returned
        """
        # Arrange
        expected_status = {
            "request_count": 100,
            "quota_limit": 1000,
            "quota_remaining": 900,
            "usage_percentage": 10.0,
            "is_exceeded": False
        }
        gnews_service.usage_repo.get_quota_status = AsyncMock(
            return_value=expected_status
        )

        # Act
        result = await gnews_service.get_usage_status()

        # Assert
        assert result == expected_status
        gnews_service.usage_repo.get_quota_status.assert_called_once_with("gnews")

    @pytest.mark.asyncio
    async def test_set_daily_quota_updates_limit(self, gnews_service):
        """
        Given a new quota limit
        When I set the daily quota
        Then the limit should be updated
        """
        # Arrange
        gnews_service.usage_repo.set_quota_limit = AsyncMock(return_value=True)

        # Act
        result = await gnews_service.set_daily_quota(2000)

        # Assert
        assert result is True
        gnews_service.usage_repo.set_quota_limit.assert_called_once_with(
            "gnews", 2000
        )
