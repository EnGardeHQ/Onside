"""Google Custom Search API service.

This module provides integration with Google Custom Search API for
brand monitoring, content performance tracking, and competitor analysis.
"""
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, calls_per_day: int = 100):
        """Initialize rate limiter.

        Args:
            calls_per_day: Maximum API calls per day
        """
        self.calls_per_day = calls_per_day
        self.calls_today = 0
        self.reset_time = datetime.utcnow() + timedelta(days=1)

    def check_and_wait(self) -> bool:
        """Check if call is allowed and reset if needed.

        Returns:
            bool: True if call is allowed
        """
        now = datetime.utcnow()

        # Reset counter if day has passed
        if now >= self.reset_time:
            self.calls_today = 0
            self.reset_time = now + timedelta(days=1)

        # Check if under limit
        if self.calls_today >= self.calls_per_day:
            logger.warning("Google Custom Search API daily quota exceeded")
            return False

        self.calls_today += 1
        return True

    def get_remaining_calls(self) -> int:
        """Get remaining API calls for today.

        Returns:
            int: Number of remaining calls
        """
        return max(0, self.calls_per_day - self.calls_today)


class GoogleCustomSearchError(Exception):
    """Exception raised for Google Custom Search API errors."""
    pass


class GoogleCustomSearchService:
    """Service for Google Custom Search API integration.

    Provides methods for searching, brand monitoring, and content analysis
    using Google's Custom Search API.
    """

    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        search_engine_id: Optional[str] = None,
        daily_quota: int = 100
    ):
        """Initialize the Google Custom Search service.

        Args:
            api_key: Google API key
            search_engine_id: Custom Search Engine ID
            daily_quota: Maximum daily API calls
        """
        self.api_key = api_key or getattr(settings, 'GOOGLE_SEARCH_API_KEY', None)
        self.search_engine_id = search_engine_id or getattr(settings, 'GOOGLE_SEARCH_ENGINE_ID', None)

        if not self.api_key or not self.search_engine_id:
            logger.warning("Google Custom Search API credentials not configured")

        self.rate_limiter = RateLimiter(daily_quota)
        self.client = httpx.AsyncClient(timeout=30.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def search(
        self,
        query: str,
        site: Optional[str] = None,
        num_results: int = 10,
        start_index: int = 1,
        language: str = 'en',
        **kwargs
    ) -> Dict[str, Any]:
        """Perform a custom search query.

        Args:
            query: Search query string
            site: Optional site restriction (e.g., 'example.com')
            num_results: Number of results to return (max 10)
            start_index: Starting index for results
            language: Search language code
            **kwargs: Additional search parameters

        Returns:
            Dict containing search results and metadata

        Raises:
            GoogleCustomSearchError: If search fails
        """
        # Check rate limit
        if not self.rate_limiter.check_and_wait():
            raise GoogleCustomSearchError("Daily API quota exceeded")

        # Build search query
        search_query = query
        if site:
            search_query = f"site:{site} {query}"

        # Build request parameters
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': search_query,
            'num': min(num_results, 10),
            'start': start_index,
            'lr': f'lang_{language}',
            **kwargs
        }

        try:
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            # Parse and structure the response
            return self._parse_search_response(data)

        except httpx.HTTPError as e:
            logger.error(f"Google Custom Search API error: {str(e)}")
            raise GoogleCustomSearchError(f"Search failed: {str(e)}")

    def _parse_search_response(self, data: Dict) -> Dict[str, Any]:
        """Parse Google Custom Search API response.

        Args:
            data: Raw API response

        Returns:
            Structured search results
        """
        items = data.get('items', [])
        search_info = data.get('searchInformation', {})

        results = []
        for item in items:
            results.append({
                'title': item.get('title'),
                'link': item.get('link'),
                'snippet': item.get('snippet'),
                'displayLink': item.get('displayLink'),
                'formattedUrl': item.get('formattedUrl'),
                'htmlSnippet': item.get('htmlSnippet'),
                'htmlTitle': item.get('htmlTitle'),
                'pagemap': item.get('pagemap', {})
            })

        return {
            'query': data.get('queries', {}).get('request', [{}])[0].get('searchTerms'),
            'totalResults': int(search_info.get('totalResults', 0)),
            'searchTime': search_info.get('searchTime', 0),
            'results': results,
            'remainingQuota': self.rate_limiter.get_remaining_calls()
        }

    async def track_brand_mentions(
        self,
        brand_name: str,
        days_back: int = 7,
        exclude_own_domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """Track brand mentions across the web.

        Args:
            brand_name: Brand name to track
            days_back: Number of days to look back
            exclude_own_domain: Optional domain to exclude from results

        Returns:
            Dict containing brand mention data and analytics
        """
        # Build date range query
        date_from = datetime.utcnow() - timedelta(days=days_back)
        date_str = date_from.strftime('%Y-%m-%d')

        # Build search query
        query = f'"{brand_name}"'
        if exclude_own_domain:
            query += f' -site:{exclude_own_domain}'

        try:
            # Search for mentions
            results = await self.search(
                query=query,
                num_results=10,
                dateRestrict=f'd{days_back}'
            )

            # Analyze mentions
            mentions = []
            sentiment_scores = []

            for result in results.get('results', []):
                mention = {
                    'url': result['link'],
                    'title': result['title'],
                    'snippet': result['snippet'],
                    'domain': result['displayLink'],
                    'foundAt': datetime.utcnow().isoformat()
                }

                # Simple sentiment analysis based on snippet
                sentiment = self._analyze_sentiment(result['snippet'])
                mention['sentiment'] = sentiment
                sentiment_scores.append(sentiment)

                mentions.append(mention)

            # Calculate metrics
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

            return {
                'brandName': brand_name,
                'period': f'{days_back} days',
                'totalMentions': results.get('totalResults', 0),
                'mentions': mentions,
                'averageSentiment': avg_sentiment,
                'positiveCount': sum(1 for s in sentiment_scores if s > 0.3),
                'neutralCount': sum(1 for s in sentiment_scores if -0.3 <= s <= 0.3),
                'negativeCount': sum(1 for s in sentiment_scores if s < -0.3),
                'queriedAt': datetime.utcnow().isoformat()
            }

        except GoogleCustomSearchError as e:
            logger.error(f"Brand mention tracking failed: {str(e)}")
            raise

    async def analyze_content_performance(
        self,
        url: str
    ) -> Dict[str, Any]:
        """Analyze content performance and visibility.

        Args:
            url: URL to analyze

        Returns:
            Dict containing performance metrics
        """
        try:
            # Extract domain and page
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            path = parsed.path

            # Search for exact URL
            exact_results = await self.search(
                query=f'site:{domain} "{path}"',
                num_results=1
            )

            # Search for domain
            domain_results = await self.search(
                query=f'site:{domain}',
                num_results=10
            )

            # Check if URL is indexed
            is_indexed = len(exact_results.get('results', [])) > 0

            # Analyze visibility
            domain_visibility = domain_results.get('totalResults', 0)

            return {
                'url': url,
                'isIndexed': is_indexed,
                'domainVisibility': domain_visibility,
                'indexedPages': domain_results.get('totalResults', 0),
                'analyzedAt': datetime.utcnow().isoformat(),
                'topPages': domain_results.get('results', [])[:5]
            }

        except GoogleCustomSearchError as e:
            logger.error(f"Content performance analysis failed: {str(e)}")
            raise

    async def competitor_search(
        self,
        competitor_domain: str,
        keywords: List[str],
        num_results: int = 10
    ) -> Dict[str, Any]:
        """Search for competitor content on specific keywords.

        Args:
            competitor_domain: Competitor's domain
            keywords: List of keywords to search
            num_results: Number of results per keyword

        Returns:
            Dict containing competitor search results
        """
        results_by_keyword = {}

        for keyword in keywords:
            try:
                search_results = await self.search(
                    query=keyword,
                    site=competitor_domain,
                    num_results=num_results
                )

                results_by_keyword[keyword] = {
                    'totalResults': search_results.get('totalResults', 0),
                    'results': search_results.get('results', [])
                }

            except GoogleCustomSearchError as e:
                logger.error(f"Competitor search failed for keyword '{keyword}': {str(e)}")
                results_by_keyword[keyword] = {
                    'totalResults': 0,
                    'results': [],
                    'error': str(e)
                }

        return {
            'competitorDomain': competitor_domain,
            'keywords': keywords,
            'results': results_by_keyword,
            'analyzedAt': datetime.utcnow().isoformat()
        }

    def _analyze_sentiment(self, text: str) -> float:
        """Simple sentiment analysis of text.

        Args:
            text: Text to analyze

        Returns:
            float: Sentiment score (-1 to 1)
        """
        # Simple keyword-based sentiment
        positive_words = ['great', 'excellent', 'amazing', 'best', 'love', 'wonderful', 'fantastic']
        negative_words = ['bad', 'poor', 'terrible', 'worst', 'hate', 'awful', 'horrible']

        text_lower = text.lower()

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        total = positive_count + negative_count
        if total == 0:
            return 0.0

        return (positive_count - negative_count) / total

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
