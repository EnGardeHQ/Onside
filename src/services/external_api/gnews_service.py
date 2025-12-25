"""GNews API Service Adapter.

This module provides a service adapter for the GNews API, enabling news article
retrieval and competitor monitoring functionality. It includes rate limiting,
retry logic with exponential backoff, and proper error handling.

GNews API documentation: https://gnews.io/docs/v4
"""
import asyncio
import hashlib
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.external_api import GNewsArticle
from src.repositories.gnews_repository import GNewsRepository
from src.repositories.api_usage_repository import APIUsageRepository
from src.repositories.competitor_repository import CompetitorRepository

logger = logging.getLogger(__name__)


class GNewsAPIError(Exception):
    """Base exception for GNews API errors.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code if applicable
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class GNewsRateLimitError(GNewsAPIError):
    """Raised when the GNews API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "GNews API rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after
        self.details["retry_after"] = retry_after


class GNewsAuthenticationError(GNewsAPIError):
    """Raised when authentication with GNews API fails."""

    def __init__(self, message: str = "Invalid or missing GNews API key"):
        super().__init__(message, status_code=401)


class GNewsService:
    """Service adapter for GNews API.

    Provides methods for searching news, retrieving competitor news,
    and analyzing news sentiment. Includes rate limiting, retry logic,
    and usage tracking.

    Attributes:
        BASE_URL: GNews API base URL
        DAILY_QUOTA: Maximum API requests per day (free tier)
        MAX_RETRIES: Maximum retry attempts for failed requests
        INITIAL_RETRY_DELAY: Initial delay in seconds for exponential backoff
    """

    BASE_URL = "https://gnews.io/api/v4"
    DAILY_QUOTA = 1000
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0

    def __init__(
        self,
        db: AsyncSession,
        api_key: Optional[str] = None,
        http_client: Optional[httpx.AsyncClient] = None
    ):
        """Initialize the GNews service.

        Args:
            db: Async database session for persistence operations
            api_key: GNews API key. If not provided, reads from GNEWS_API_KEY env var
            http_client: Optional httpx client for testing/mocking
        """
        self.db = db
        self.api_key = api_key or os.getenv("GNEWS_API_KEY")
        self._http_client = http_client
        self._owns_client = http_client is None

        # Initialize repositories
        self.gnews_repo = GNewsRepository(db)
        self.usage_repo = APIUsageRepository(db)
        self.competitor_repo = CompetitorRepository(db)

    async def __aenter__(self) -> "GNewsService":
        """Async context manager entry."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._owns_client and self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get the HTTP client, creating one if necessary.

        Returns:
            httpx.AsyncClient instance

        Raises:
            RuntimeError: If client is not initialized and not in context manager
        """
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
            self._owns_client = True
        return self._http_client

    async def _check_rate_limit(self) -> bool:
        """Check if the API rate limit has been exceeded.

        Returns:
            True if requests can be made, False if quota exceeded
        """
        status = await self.usage_repo.get_quota_status("gnews")
        if status.get("is_exceeded"):
            logger.warning("GNews API daily quota exceeded")
            return False
        return True

    async def _record_api_call(self, endpoint: str) -> None:
        """Record an API call for usage tracking.

        Args:
            endpoint: The API endpoint that was called
        """
        await self.usage_repo.record_usage(
            api_name="gnews",
            endpoint=endpoint,
            count=1
        )

    async def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Make an HTTP request to the GNews API with retry logic.

        Args:
            endpoint: API endpoint to call
            params: Query parameters
            retry_count: Current retry attempt number

        Returns:
            JSON response from the API

        Raises:
            GNewsAuthenticationError: If API key is invalid or missing
            GNewsRateLimitError: If rate limit is exceeded
            GNewsAPIError: For other API errors
        """
        if not self.api_key:
            raise GNewsAuthenticationError("GNEWS_API_KEY environment variable not set")

        # Check rate limit before making request
        if not await self._check_rate_limit():
            raise GNewsRateLimitError(
                "Daily quota exceeded. Try again tomorrow.",
                retry_after=86400  # 24 hours in seconds
            )

        # Add API key to params
        params["apikey"] = self.api_key

        url = f"{self.BASE_URL}/{endpoint}"
        client = self._get_client()

        try:
            response = await client.get(url, params=params)

            # Record the API call
            await self._record_api_call(endpoint)

            if response.status_code == 401:
                raise GNewsAuthenticationError()

            if response.status_code == 403:
                raise GNewsAuthenticationError(
                    "Access forbidden. Check your API key permissions."
                )

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise GNewsRateLimitError(retry_after=retry_after)

            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise GNewsAPIError(
                    message=error_data.get("errors", [f"HTTP {response.status_code}"])[0]
                    if error_data.get("errors")
                    else f"HTTP {response.status_code}",
                    status_code=response.status_code,
                    details=error_data
                )

            return response.json()

        except httpx.TimeoutException:
            if retry_count < self.MAX_RETRIES:
                delay = self.INITIAL_RETRY_DELAY * (2 ** retry_count)
                logger.warning(
                    f"GNews API timeout. Retrying in {delay}s (attempt {retry_count + 1})"
                )
                await asyncio.sleep(delay)
                return await self._make_request(endpoint, params, retry_count + 1)
            raise GNewsAPIError(
                "Request timed out after multiple retries",
                details={"retries": retry_count}
            )

        except httpx.RequestError as e:
            if retry_count < self.MAX_RETRIES:
                delay = self.INITIAL_RETRY_DELAY * (2 ** retry_count)
                logger.warning(
                    f"GNews API request error: {e}. Retrying in {delay}s"
                )
                await asyncio.sleep(delay)
                return await self._make_request(endpoint, params, retry_count + 1)
            raise GNewsAPIError(
                f"Request failed: {str(e)}",
                details={"error_type": type(e).__name__}
            )

    def _generate_article_id(self, article: Dict[str, Any]) -> str:
        """Generate a unique article ID from article data.

        Args:
            article: Article data from GNews API

        Returns:
            SHA256 hash of the article URL
        """
        url = article.get("url", "")
        return hashlib.sha256(url.encode()).hexdigest()[:64]

    def _parse_article_to_dict(
        self,
        article: Dict[str, Any],
        query_term: Optional[str] = None,
        competitor_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Parse GNews API article data into a dictionary.

        Args:
            article: Raw article data from GNews API
            query_term: Search query used to find this article
            competitor_id: ID of associated competitor

        Returns:
            Dictionary with parsed article data
        """
        # Parse published date
        published_str = article.get("publishedAt", "")
        try:
            published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            published_at = datetime.now(timezone.utc)

        source = article.get("source", {})

        return {
            "article_id": self._generate_article_id(article),
            "title": article.get("title", "")[:500],
            "description": article.get("description"),
            "content": article.get("content"),
            "url": article.get("url", ""),
            "image_url": article.get("image"),
            "published_at": published_at.isoformat() if published_at else None,
            "source_name": source.get("name", "Unknown"),
            "source_url": source.get("url"),
            "query_term": query_term,
            "language": None,
            "country": None,
            "competitor_id": competitor_id,
            "id": None,
            "created_at": None,
            "updated_at": None,
        }

    def _dict_to_model(self, data: Dict[str, Any]) -> GNewsArticle:
        """Convert parsed article dict to GNewsArticle model.

        Args:
            data: Parsed article dictionary

        Returns:
            GNewsArticle instance
        """
        # Parse published_at back to datetime if it's a string
        published_at = data.get("published_at")
        if isinstance(published_at, str):
            try:
                published_at = datetime.fromisoformat(published_at)
            except (ValueError, AttributeError):
                published_at = datetime.now(datetime.UTC)

        return GNewsArticle(
            article_id=data["article_id"],
            title=data["title"],
            description=data.get("description"),
            content=data.get("content"),
            url=data["url"],
            image_url=data.get("image_url"),
            published_at=published_at,
            source_name=data["source_name"],
            source_url=data.get("source_url"),
            query_term=data.get("query_term"),
            language=data.get("language"),
            country=data.get("country"),
            competitor_id=data.get("competitor_id")
        )

    async def search_news(
        self,
        query: str,
        max_results: int = 10,
        language: str = "en",
        country: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sort_by: str = "relevance",
        save_to_db: bool = True
    ) -> List[Dict[str, Any]]:
        """Search for news articles.

        Args:
            query: Search query string
            max_results: Maximum number of results (1-100)
            language: Language code (e.g., "en", "es", "fr")
            country: Country code for regional news (e.g., "us", "gb")
            from_date: Filter articles published after this date
            to_date: Filter articles published before this date
            sort_by: Sort order ("relevance" or "publishedAt")
            save_to_db: Whether to save results to database

        Returns:
            List of article dictionaries with parsed data

        Raises:
            GNewsAPIError: If the API request fails
        """
        max_results = max(1, min(max_results, 100))

        params: Dict[str, Any] = {
            "q": query,
            "max": max_results,
            "lang": language,
            "sortby": sort_by
        }

        if country:
            params["country"] = country

        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        response = await self._make_request("search", params)
        articles = response.get("articles", [])

        result = []
        for article_data in articles:
            article_dict = self._parse_article_to_dict(article_data, query_term=query)

            if save_to_db:
                # Check if article already exists
                existing = await self.gnews_repo.get_by_article_id(article_dict["article_id"])
                if not existing:
                    article_model = self._dict_to_model(article_dict)
                    await self.gnews_repo.create_article(article_model)
                    logger.debug(f"Saved new article: {article_dict['title'][:50]}...")

            result.append(article_dict)

        logger.info(f"Found {len(result)} articles for query: {query}")
        return result

    async def get_competitor_news(
        self,
        competitor_id: int,
        days_back: int = 7,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Get news articles related to a specific competitor.

        Searches for news using the competitor's name and domain,
        then associates the articles with the competitor.

        Args:
            competitor_id: Database ID of the competitor
            days_back: Number of days to look back
            max_results: Maximum number of results

        Returns:
            List of article dictionaries

        Raises:
            GNewsAPIError: If the API request fails
            ValueError: If competitor is not found
        """
        # Get competitor details
        competitor = await self.competitor_repo.get_by_id(competitor_id)
        if not competitor:
            raise ValueError(f"Competitor with ID {competitor_id} not found")

        # Build search query from competitor name and domain
        search_terms = []
        if hasattr(competitor, "name") and competitor.name:
            search_terms.append(f'"{competitor.name}"')
        if hasattr(competitor, "domain") and competitor.domain:
            # Extract company name from domain if possible
            domain_name = competitor.domain.replace("www.", "").split(".")[0]
            if domain_name and domain_name not in str(search_terms):
                search_terms.append(domain_name)

        if not search_terms:
            raise ValueError(f"Competitor {competitor_id} has no searchable name or domain")

        query = " OR ".join(search_terms)
        from_date = datetime.now(timezone.utc) - timedelta(days=days_back)

        params: Dict[str, Any] = {
            "q": query,
            "max": min(max_results, 100),
            "lang": "en",
            "from": from_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sortby": "publishedAt"
        }

        response = await self._make_request("search", params)
        articles = response.get("articles", [])

        result = []
        for article_data in articles:
            article_dict = self._parse_article_to_dict(
                article_data,
                query_term=query,
                competitor_id=competitor_id
            )

            # Check if article already exists
            existing = await self.gnews_repo.get_by_article_id(article_dict["article_id"])
            if not existing:
                article_model = self._dict_to_model(article_dict)
                await self.gnews_repo.create_article(article_model)
            else:
                # Update competitor_id if not set
                if existing.competitor_id is None:
                    existing.competitor_id = competitor_id
                    await self.db.commit()

            result.append(article_dict)

        logger.info(
            f"Found {len(result)} articles for competitor {competitor_id} "
            f"in the last {days_back} days"
        )
        return result

    async def get_top_headlines(
        self,
        category: str = "general",
        country: str = "us",
        max_results: int = 10,
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """Get top news headlines by category and country.

        Args:
            category: News category (general, world, nation, business,
                     technology, entertainment, sports, science, health)
            country: Country code (e.g., "us", "gb", "ca")
            max_results: Maximum number of results (1-100)
            language: Language code

        Returns:
            List of headline article dictionaries

        Raises:
            GNewsAPIError: If the API request fails
            ValueError: If category is invalid
        """
        valid_categories = [
            "general", "world", "nation", "business", "technology",
            "entertainment", "sports", "science", "health"
        ]

        if category not in valid_categories:
            raise ValueError(
                f"Invalid category '{category}'. "
                f"Must be one of: {', '.join(valid_categories)}"
            )

        params: Dict[str, Any] = {
            "category": category,
            "country": country,
            "max": min(max_results, 100),
            "lang": language
        }

        response = await self._make_request("top-headlines", params)
        articles = response.get("articles", [])

        result = []
        for article_data in articles:
            article_dict = self._parse_article_to_dict(article_data)
            article_dict["country"] = country
            article_dict["language"] = language

            # Save to database
            existing = await self.gnews_repo.get_by_article_id(article_dict["article_id"])
            if not existing:
                article_model = self._dict_to_model(article_dict)
                await self.gnews_repo.create_article(article_model)

            result.append(article_dict)

        logger.info(
            f"Retrieved {len(result)} top headlines for "
            f"category={category}, country={country}"
        )
        return result

    async def analyze_news_sentiment(
        self,
        news_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform basic sentiment analysis on news items.

        This is a simple keyword-based sentiment analysis. For more
        accurate results, consider integrating with an NLP service.

        Args:
            news_items: List of news article dictionaries

        Returns:
            Dictionary with sentiment analysis results:
            - overall_sentiment: "positive", "negative", or "neutral"
            - sentiment_score: Float from -1 (very negative) to 1 (very positive)
            - positive_count: Number of positive articles
            - negative_count: Number of negative articles
            - neutral_count: Number of neutral articles
            - article_sentiments: List of per-article sentiment data
        """
        if not news_items:
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "article_sentiments": []
            }

        # Simple keyword-based sentiment analysis
        positive_keywords = {
            "success", "growth", "profit", "gain", "positive", "increase",
            "improve", "innovation", "breakthrough", "award", "achievement",
            "partnership", "expansion", "record", "surge", "boost", "win",
            "celebrate", "milestone", "excellent", "outstanding", "strong"
        }

        negative_keywords = {
            "loss", "decline", "fail", "drop", "negative", "decrease",
            "problem", "issue", "crisis", "lawsuit", "scandal", "concern",
            "warning", "risk", "threat", "downturn", "layoff", "cut",
            "struggle", "challenge", "weak", "poor", "miss", "fall"
        }

        article_sentiments = []
        total_score = 0.0

        for item in news_items:
            title = (item.get("title") or "").lower()
            description = (item.get("description") or "").lower()
            text = f"{title} {description}"

            words = set(text.split())
            pos_count = len(words & positive_keywords)
            neg_count = len(words & negative_keywords)

            if pos_count > neg_count:
                sentiment = "positive"
                score = min(1.0, (pos_count - neg_count) / 5)
            elif neg_count > pos_count:
                sentiment = "negative"
                score = max(-1.0, (pos_count - neg_count) / 5)
            else:
                sentiment = "neutral"
                score = 0.0

            total_score += score
            article_sentiments.append({
                "article_id": item.get("article_id"),
                "title": item.get("title"),
                "sentiment": sentiment,
                "score": round(score, 2)
            })

        avg_score = total_score / len(news_items)
        positive_count = sum(1 for a in article_sentiments if a["sentiment"] == "positive")
        negative_count = sum(1 for a in article_sentiments if a["sentiment"] == "negative")
        neutral_count = sum(1 for a in article_sentiments if a["sentiment"] == "neutral")

        if avg_score > 0.1:
            overall_sentiment = "positive"
        elif avg_score < -0.1:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"

        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_score": round(avg_score, 3),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "article_sentiments": article_sentiments
        }

    async def get_usage_status(self) -> Dict[str, Any]:
        """Get current API usage status.

        Returns:
            Dictionary with usage information:
            - request_count: Number of requests made in current period
            - quota_limit: Maximum allowed requests
            - quota_remaining: Remaining requests
            - usage_percentage: Percentage of quota used
            - is_exceeded: Whether quota has been exceeded
        """
        return await self.usage_repo.get_quota_status("gnews")

    async def set_daily_quota(self, quota: int = DAILY_QUOTA) -> bool:
        """Set the daily API quota limit.

        Args:
            quota: Maximum requests per day (default: 1000)

        Returns:
            True if quota was set successfully
        """
        return await self.usage_repo.set_quota_limit("gnews", quota)
