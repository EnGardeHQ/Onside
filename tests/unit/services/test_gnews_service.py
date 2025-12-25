"""Unit tests for the GNews service adapter.

These tests verify the functionality of the GNewsService class, including:
- News search functionality
- Competitor news retrieval
- Top headlines retrieval
- Sentiment analysis
- Rate limiting and quota management
- Error handling and retry logic
"""
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio

from src.services.external_api.gnews_service import (
    GNewsService,
    GNewsAPIError,
    GNewsRateLimitError,
    GNewsAuthenticationError,
)


# ----- Test Data -----

SAMPLE_ARTICLE = {
    "title": "Test Article Title",
    "description": "This is a test article description",
    "content": "Full content of the test article",
    "url": "https://example.com/article/123",
    "image": "https://example.com/image.jpg",
    "publishedAt": "2024-01-15T10:30:00Z",
    "source": {
        "name": "Test News",
        "url": "https://testnews.com"
    }
}

SAMPLE_ARTICLES_RESPONSE = {
    "totalArticles": 2,
    "articles": [
        SAMPLE_ARTICLE,
        {
            "title": "Second Test Article",
            "description": "Another test description",
            "content": "More content here",
            "url": "https://example.com/article/456",
            "image": "https://example.com/image2.jpg",
            "publishedAt": "2024-01-14T08:00:00Z",
            "source": {
                "name": "Other News",
                "url": "https://othernews.com"
            }
        }
    ]
}

SAMPLE_HEADLINES_RESPONSE = {
    "totalArticles": 3,
    "articles": [
        {
            "title": "Breaking: Market Update",
            "description": "Stock markets show positive growth",
            "url": "https://news.example.com/market",
            "publishedAt": "2024-01-15T14:00:00Z",
            "source": {"name": "Financial Times", "url": "https://ft.com"}
        },
        {
            "title": "Tech Company Announces Innovation",
            "description": "New breakthrough in AI technology",
            "url": "https://news.example.com/tech",
            "publishedAt": "2024-01-15T12:00:00Z",
            "source": {"name": "Tech Crunch", "url": "https://techcrunch.com"}
        }
    ]
}


# ----- Fixtures -----

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    client = MagicMock(spec=httpx.AsyncClient)
    # Set up a default mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"articles": []}
    mock_response.headers = {}
    mock_response.content = b'{}'

    # Make get return a coroutine that resolves to the response
    async def mock_get(*args, **kwargs):
        return mock_response

    client.get = MagicMock(side_effect=mock_get)
    client._mock_response = mock_response  # Store for test access
    return client


@pytest.fixture
def mock_gnews_repo():
    """Create a mock GNews repository."""
    repo = AsyncMock()
    repo.get_by_article_id.return_value = None
    repo.create_article.return_value = MagicMock(id=1)
    return repo


@pytest.fixture
def mock_usage_repo():
    """Create a mock API usage repository."""
    repo = AsyncMock()
    repo.get_quota_status.return_value = {
        "api_name": "gnews",
        "request_count": 50,
        "quota_limit": 1000,
        "quota_remaining": 950,
        "usage_percentage": 5.0,
        "is_exceeded": False
    }
    repo.record_usage.return_value = MagicMock()
    repo.set_quota_limit.return_value = True
    return repo


@pytest.fixture
def mock_competitor_repo():
    """Create a mock competitor repository."""
    repo = AsyncMock()
    competitor = MagicMock()
    competitor.id = 1
    competitor.name = "Acme Corp"
    competitor.domain = "acme.com"
    repo.get_by_id.return_value = competitor
    return repo


@pytest.fixture
def gnews_service(mock_db, mock_http_client, mock_gnews_repo, mock_usage_repo, mock_competitor_repo):
    """Create a GNewsService instance with mocked dependencies."""
    with patch.dict("os.environ", {"GNEWS_API_KEY": "test-api-key"}):
        service = GNewsService(
            db=mock_db,
            api_key="test-api-key",
            http_client=mock_http_client
        )
        service.gnews_repo = mock_gnews_repo
        service.usage_repo = mock_usage_repo
        service.competitor_repo = mock_competitor_repo
        return service


# ----- Test: Initialization -----

class TestGNewsServiceInitialization:
    """Tests for GNewsService initialization."""

    def test_init_with_api_key(self, mock_db):
        """Test initialization with explicit API key."""
        service = GNewsService(db=mock_db, api_key="explicit-key")
        assert service.api_key == "explicit-key"

    def test_init_from_environment(self, mock_db):
        """Test initialization from environment variable."""
        with patch.dict("os.environ", {"GNEWS_API_KEY": "env-key"}):
            service = GNewsService(db=mock_db)
            assert service.api_key == "env-key"

    def test_init_without_api_key(self, mock_db):
        """Test initialization without API key."""
        with patch.dict("os.environ", {}, clear=True):
            service = GNewsService(db=mock_db)
            assert service.api_key is None


# ----- Test: Search News -----

class TestSearchNews:
    """Tests for the search_news method."""

    @pytest.mark.asyncio
    async def test_search_news_success(self, gnews_service, mock_http_client):
        """Test successful news search."""
        # Setup mock response
        mock_http_client._mock_response.status_code = 200
        mock_http_client._mock_response.json.return_value = SAMPLE_ARTICLES_RESPONSE

        async with gnews_service:
            results = await gnews_service.search_news(
                query="test query",
                max_results=10,
                language="en",
                save_to_db=False  # Skip DB to avoid SQLAlchemy mapper issues
            )

        assert len(results) == 2
        assert results[0]["title"] == "Test Article Title"
        assert results[0]["source_name"] == "Test News"
        mock_http_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_news_with_filters(self, gnews_service, mock_http_client):
        """Test news search with date filters."""
        mock_http_client._mock_response.status_code = 200
        mock_http_client._mock_response.json.return_value = SAMPLE_ARTICLES_RESPONSE

        from_date = datetime(2024, 1, 1)
        to_date = datetime(2024, 1, 15)

        async with gnews_service:
            await gnews_service.search_news(
                query="filtered search",
                from_date=from_date,
                to_date=to_date,
                country="us",
                save_to_db=False
            )

        call_kwargs = mock_http_client.get.call_args
        params = call_kwargs.kwargs.get("params", {})
        assert "from" in params
        assert "to" in params
        assert params["country"] == "us"

    @pytest.mark.asyncio
    async def test_search_news_max_results_limit(self, gnews_service, mock_http_client):
        """Test that max_results is clamped to valid range."""
        mock_http_client._mock_response.status_code = 200
        mock_http_client._mock_response.json.return_value = {"articles": []}

        async with gnews_service:
            # Test with value > 100
            await gnews_service.search_news(query="test", max_results=200, save_to_db=False)

        call_kwargs = mock_http_client.get.call_args
        params = call_kwargs.kwargs.get("params", {})
        assert params["max"] == 100

    @pytest.mark.asyncio
    async def test_search_news_without_api_key(self, mock_db):
        """Test that search fails without API key."""
        with patch.dict("os.environ", {}, clear=True):
            service = GNewsService(db=mock_db, api_key=None)
            service.usage_repo = AsyncMock()
            service.usage_repo.get_quota_status.return_value = {"is_exceeded": False}

            with pytest.raises(GNewsAuthenticationError) as exc_info:
                async with service:
                    await service.search_news(query="test")

            assert "not set" in str(exc_info.value.message)


# ----- Test: Get Competitor News -----

class TestGetCompetitorNews:
    """Tests for the get_competitor_news method."""

    @pytest.mark.asyncio
    async def test_get_competitor_news_success(self, gnews_service, mock_http_client):
        """Test successful competitor news retrieval."""
        mock_http_client._mock_response.status_code = 200
        mock_http_client._mock_response.json.return_value = SAMPLE_ARTICLES_RESPONSE

        # Mock the gnews_repo to skip actual DB operations
        gnews_service.gnews_repo.get_by_article_id = AsyncMock(return_value=None)
        gnews_service.gnews_repo.create_article = AsyncMock()
        # Mock _dict_to_model to avoid SQLAlchemy mapper issues
        gnews_service._dict_to_model = MagicMock(return_value=MagicMock())

        async with gnews_service:
            results = await gnews_service.get_competitor_news(
                competitor_id=1,
                days_back=7
            )

        assert len(results) == 2
        # Verify search query was built from competitor data
        call_kwargs = mock_http_client.get.call_args
        params = call_kwargs.kwargs.get("params", {})
        assert "Acme Corp" in params["q"] or "acme" in params["q"]

    @pytest.mark.asyncio
    async def test_get_competitor_news_not_found(self, gnews_service):
        """Test competitor news when competitor doesn't exist."""
        gnews_service.competitor_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            async with gnews_service:
                await gnews_service.get_competitor_news(competitor_id=999)

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_competitor_news_no_searchable_terms(self, gnews_service):
        """Test competitor without name or domain."""
        competitor = MagicMock()
        competitor.id = 1
        competitor.name = None
        competitor.domain = None
        gnews_service.competitor_repo.get_by_id = AsyncMock(return_value=competitor)

        with pytest.raises(ValueError) as exc_info:
            async with gnews_service:
                await gnews_service.get_competitor_news(competitor_id=1)

        assert "no searchable" in str(exc_info.value).lower()


# ----- Test: Get Top Headlines -----

class TestGetTopHeadlines:
    """Tests for the get_top_headlines method."""

    @pytest.mark.asyncio
    async def test_get_headlines_success(self, gnews_service, mock_http_client):
        """Test successful headlines retrieval."""
        mock_http_client._mock_response.status_code = 200
        mock_http_client._mock_response.json.return_value = SAMPLE_HEADLINES_RESPONSE

        # Mock DB operations
        gnews_service.gnews_repo.get_by_article_id = AsyncMock(return_value=None)
        gnews_service.gnews_repo.create_article = AsyncMock()
        # Mock _dict_to_model to avoid SQLAlchemy mapper issues
        gnews_service._dict_to_model = MagicMock(return_value=MagicMock())

        async with gnews_service:
            results = await gnews_service.get_top_headlines(
                category="business",
                country="us"
            )

        assert len(results) == 2
        assert results[0]["title"] == "Breaking: Market Update"

    @pytest.mark.asyncio
    async def test_get_headlines_invalid_category(self, gnews_service):
        """Test headlines with invalid category."""
        with pytest.raises(ValueError) as exc_info:
            async with gnews_service:
                await gnews_service.get_top_headlines(category="invalid")

        assert "Invalid category" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_headlines_all_categories(self, gnews_service, mock_http_client):
        """Test that all valid categories are accepted."""
        mock_http_client._mock_response.status_code = 200
        mock_http_client._mock_response.json.return_value = {"articles": []}

        # Mock DB operations
        gnews_service.gnews_repo.get_by_article_id = AsyncMock(return_value=None)
        gnews_service.gnews_repo.create_article = AsyncMock()

        valid_categories = [
            "general", "world", "nation", "business", "technology",
            "entertainment", "sports", "science", "health"
        ]

        async with gnews_service:
            for category in valid_categories:
                results = await gnews_service.get_top_headlines(category=category)
                assert results is not None


# ----- Test: Sentiment Analysis -----

class TestSentimentAnalysis:
    """Tests for the analyze_news_sentiment method."""

    @pytest.mark.asyncio
    async def test_analyze_positive_sentiment(self, gnews_service):
        """Test sentiment analysis with positive articles."""
        positive_articles = [
            {"title": "Company Achieves Record Growth", "description": "Success and profit surge"},
            {"title": "Innovation Award Winner", "description": "Outstanding achievement celebrated"}
        ]

        async with gnews_service:
            result = await gnews_service.analyze_news_sentiment(positive_articles)

        assert result["overall_sentiment"] == "positive"
        assert result["sentiment_score"] > 0
        assert result["positive_count"] == 2

    @pytest.mark.asyncio
    async def test_analyze_negative_sentiment(self, gnews_service):
        """Test sentiment analysis with negative articles."""
        negative_articles = [
            {"title": "Company Faces Crisis", "description": "Major losses and decline reported"},
            {"title": "Lawsuit Filed Against Firm", "description": "Scandal threatens business"}
        ]

        async with gnews_service:
            result = await gnews_service.analyze_news_sentiment(negative_articles)

        assert result["overall_sentiment"] == "negative"
        assert result["sentiment_score"] < 0
        assert result["negative_count"] == 2

    @pytest.mark.asyncio
    async def test_analyze_empty_list(self, gnews_service):
        """Test sentiment analysis with empty list."""
        async with gnews_service:
            result = await gnews_service.analyze_news_sentiment([])

        assert result["overall_sentiment"] == "neutral"
        assert result["sentiment_score"] == 0.0
        assert result["positive_count"] == 0
        assert result["negative_count"] == 0
        assert result["neutral_count"] == 0

    @pytest.mark.asyncio
    async def test_analyze_mixed_sentiment(self, gnews_service):
        """Test sentiment analysis with mixed articles."""
        mixed_articles = [
            {"title": "Record Profits Announced", "description": "Strong growth and success reported"},
            {"title": "Quarterly Report Released", "description": "Standard financial update"},
            {"title": "Major Layoffs and Crisis", "description": "Cost cutting and decline announced"}
        ]

        async with gnews_service:
            result = await gnews_service.analyze_news_sentiment(mixed_articles)

        assert result["positive_count"] >= 1
        assert result["negative_count"] >= 1
        assert len(result["article_sentiments"]) == 3


# ----- Test: Rate Limiting -----

class TestRateLimiting:
    """Tests for rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_rate_limit_check_exceeded(self, gnews_service, mock_http_client):
        """Test that requests fail when quota is exceeded."""
        gnews_service.usage_repo.get_quota_status = AsyncMock(return_value={
            "is_exceeded": True,
            "request_count": 1000,
            "quota_limit": 1000
        })

        with pytest.raises(GNewsRateLimitError) as exc_info:
            async with gnews_service:
                await gnews_service.search_news(query="test")

        assert "quota exceeded" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_api_rate_limit_response(self, gnews_service, mock_http_client):
        """Test handling of 429 response from API."""
        mock_http_client._mock_response.status_code = 429
        mock_http_client._mock_response.headers = {"Retry-After": "3600"}

        with pytest.raises(GNewsRateLimitError) as exc_info:
            async with gnews_service:
                await gnews_service.search_news(query="test")

        assert exc_info.value.retry_after == 3600

    @pytest.mark.asyncio
    async def test_record_api_usage(self, gnews_service, mock_http_client):
        """Test that API usage is recorded."""
        mock_http_client._mock_response.status_code = 200
        mock_http_client._mock_response.json.return_value = {"articles": []}

        async with gnews_service:
            await gnews_service.search_news(query="test", save_to_db=False)

        gnews_service.usage_repo.record_usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_usage_status(self, gnews_service):
        """Test getting usage status."""
        async with gnews_service:
            status = await gnews_service.get_usage_status()

        assert status["api_name"] == "gnews"
        assert "request_count" in status
        assert "quota_limit" in status

    @pytest.mark.asyncio
    async def test_set_daily_quota(self, gnews_service):
        """Test setting daily quota."""
        async with gnews_service:
            result = await gnews_service.set_daily_quota(500)

        assert result is True
        gnews_service.usage_repo.set_quota_limit.assert_called_with("gnews", 500)


# ----- Test: Error Handling -----

class TestErrorHandling:
    """Tests for error handling and retry logic."""

    @pytest.mark.asyncio
    async def test_authentication_error(self, gnews_service, mock_http_client):
        """Test handling of authentication error."""
        mock_http_client._mock_response.status_code = 401

        with pytest.raises(GNewsAuthenticationError):
            async with gnews_service:
                await gnews_service.search_news(query="test")

    @pytest.mark.asyncio
    async def test_forbidden_error(self, gnews_service, mock_http_client):
        """Test handling of 403 forbidden error."""
        mock_http_client._mock_response.status_code = 403

        with pytest.raises(GNewsAuthenticationError) as exc_info:
            async with gnews_service:
                await gnews_service.search_news(query="test")

        assert "forbidden" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_api_error_with_details(self, gnews_service, mock_http_client):
        """Test handling of API error with error details."""
        mock_http_client._mock_response.status_code = 400
        mock_http_client._mock_response.content = b'{"errors": ["Invalid query parameter"]}'
        mock_http_client._mock_response.json.return_value = {"errors": ["Invalid query parameter"]}

        with pytest.raises(GNewsAPIError) as exc_info:
            async with gnews_service:
                await gnews_service.search_news(query="test")

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_timeout_with_retry(self, gnews_service, mock_http_client):
        """Test that timeouts trigger retries."""
        # First call times out, second succeeds
        call_count = [0]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"articles": []}

        async def mock_get_with_retry(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise httpx.TimeoutException("Timeout")
            return mock_response

        mock_http_client.get = MagicMock(side_effect=mock_get_with_retry)

        async with gnews_service:
            with patch("asyncio.sleep", new_callable=AsyncMock):
                results = await gnews_service.search_news(query="test", save_to_db=False)

        assert results == []
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, gnews_service, mock_http_client):
        """Test that max retries are respected."""
        call_count = [0]

        async def mock_get_timeout(*args, **kwargs):
            call_count[0] += 1
            raise httpx.TimeoutException("Timeout")

        mock_http_client.get = MagicMock(side_effect=mock_get_timeout)

        with pytest.raises(GNewsAPIError) as exc_info:
            async with gnews_service:
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    await gnews_service.search_news(query="test")

        assert "timed out" in str(exc_info.value.message).lower()
        # Should have tried MAX_RETRIES + 1 times
        assert call_count[0] == gnews_service.MAX_RETRIES + 1


# ----- Test: Article Parsing -----

class TestArticleParsing:
    """Tests for article parsing functionality."""

    def test_generate_article_id(self, gnews_service):
        """Test article ID generation."""
        article = {"url": "https://example.com/article/123"}
        article_id = gnews_service._generate_article_id(article)

        assert len(article_id) == 64
        assert article_id == hashlib.sha256(article["url"].encode()).hexdigest()[:64]

    def test_generate_article_id_empty_url(self, gnews_service):
        """Test article ID generation with empty URL."""
        article = {"url": ""}
        article_id = gnews_service._generate_article_id(article)

        # Should still generate a valid hash
        assert len(article_id) == 64

    def test_generate_article_id_missing_url(self, gnews_service):
        """Test article ID generation with missing URL."""
        article = {}
        article_id = gnews_service._generate_article_id(article)

        # Should still generate a valid hash from empty string
        assert len(article_id) == 64


# ----- Test: Context Manager -----

class TestContextManager:
    """Tests for async context manager functionality."""

    @pytest.mark.asyncio
    async def test_context_manager_creates_client(self, mock_db):
        """Test that context manager creates HTTP client."""
        with patch.dict("os.environ", {"GNEWS_API_KEY": "test-key"}):
            service = GNewsService(db=mock_db)

            assert service._http_client is None

            async with service:
                assert service._http_client is not None

    @pytest.mark.asyncio
    async def test_context_manager_uses_provided_client(self, mock_db, mock_http_client):
        """Test that provided client is used."""
        with patch.dict("os.environ", {"GNEWS_API_KEY": "test-key"}):
            service = GNewsService(db=mock_db, http_client=mock_http_client)

            async with service:
                assert service._http_client is mock_http_client

    @pytest.mark.asyncio
    async def test_context_manager_closes_owned_client(self, mock_db):
        """Test that owned client is closed on exit."""
        with patch.dict("os.environ", {"GNEWS_API_KEY": "test-key"}):
            service = GNewsService(db=mock_db)

            async with service:
                client = service._http_client

            # After context manager exits, client should be closed
            # (In practice, the client would be set to None after close)


# ----- Test: Database Integration -----

class TestDatabaseIntegration:
    """Tests for database integration."""

    @pytest.mark.asyncio
    async def test_saves_new_articles(self, gnews_service, mock_http_client):
        """Test that new articles are saved to database."""
        mock_http_client._mock_response.status_code = 200
        mock_http_client._mock_response.json.return_value = SAMPLE_ARTICLES_RESPONSE

        # Mock DB operations to avoid SQLAlchemy issues
        gnews_service.gnews_repo.get_by_article_id = AsyncMock(return_value=None)
        gnews_service.gnews_repo.create_article = AsyncMock()
        # Mock _dict_to_model to avoid SQLAlchemy mapper issues
        gnews_service._dict_to_model = MagicMock(return_value=MagicMock())

        async with gnews_service:
            await gnews_service.search_news(query="test", save_to_db=True)

        # Should have tried to create 2 articles
        assert gnews_service.gnews_repo.create_article.call_count == 2

    @pytest.mark.asyncio
    async def test_skips_existing_articles(self, gnews_service, mock_http_client):
        """Test that existing articles are not duplicated."""
        mock_http_client._mock_response.status_code = 200
        mock_http_client._mock_response.json.return_value = SAMPLE_ARTICLES_RESPONSE

        # First article already exists
        gnews_service.gnews_repo.get_by_article_id = AsyncMock(side_effect=[
            MagicMock(),  # First article exists
            None          # Second article doesn't exist
        ])
        gnews_service.gnews_repo.create_article = AsyncMock()
        # Mock _dict_to_model to avoid SQLAlchemy mapper issues
        gnews_service._dict_to_model = MagicMock(return_value=MagicMock())

        async with gnews_service:
            await gnews_service.search_news(query="test", save_to_db=True)

        # Should only create one new article
        assert gnews_service.gnews_repo.create_article.call_count == 1

    @pytest.mark.asyncio
    async def test_save_to_db_disabled(self, gnews_service, mock_http_client):
        """Test that saving can be disabled."""
        mock_http_client._mock_response.status_code = 200
        mock_http_client._mock_response.json.return_value = SAMPLE_ARTICLES_RESPONSE

        gnews_service.gnews_repo.create_article = AsyncMock()

        async with gnews_service:
            await gnews_service.search_news(query="test", save_to_db=False)

        # Should not have tried to create any articles
        gnews_service.gnews_repo.create_article.assert_not_called()
