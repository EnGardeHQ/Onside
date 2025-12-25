"""
EnGarde API Client

This module provides an async HTTP client for communicating with the EnGarde
production backend API. It handles authentication, retry logic, error handling,
and logging for all API interactions.

Features:
- Async/await pattern with aiohttp
- Automatic authentication with API key
- Retry logic with exponential backoff
- Comprehensive error handling
- Request/response logging
- Timeout management
- Proper typing annotations

Usage:
    from src.services.engarde_integration.api_client import EnGardeAPIClient
    from src.config import settings

    async with EnGardeAPIClient(
        api_url=settings.ENGARDE_API_URL,
        api_key=settings.ENGARDE_API_KEY,
        tenant_uuid=settings.ENGARDE_TENANT_UUID
    ) as client:
        response = await client.create_keyword(keyword_data)
"""

import logging
import asyncio
from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientResponse, ClientError
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# EXCEPTIONS
# ============================================================================

class EnGardeAPIError(Exception):
    """Base exception for EnGarde API errors."""
    pass


class EnGardeAuthenticationError(EnGardeAPIError):
    """Authentication failed with EnGarde API."""
    pass


class EnGardeRateLimitError(EnGardeAPIError):
    """Rate limit exceeded."""
    pass


class EnGardeValidationError(EnGardeAPIError):
    """Request validation failed."""
    pass


class EnGardeNotFoundError(EnGardeAPIError):
    """Resource not found."""
    pass


class EnGardeServerError(EnGardeAPIError):
    """EnGarde server error (5xx)."""
    pass


# ============================================================================
# SCHEMAS
# ============================================================================

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status_code: int
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RetryConfig(BaseModel):
    """Configuration for retry logic."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    retry_on_status_codes: List[int] = Field(default_factory=lambda: [429, 500, 502, 503, 504])


# ============================================================================
# API CLIENT
# ============================================================================

class EnGardeAPIClient:
    """
    Async HTTP client for EnGarde production backend API.

    This client provides methods for creating and managing keywords, competitors,
    and content ideas in the EnGarde system. It handles authentication, retries,
    and error handling automatically.

    Example:
        async with EnGardeAPIClient(
            api_url="https://engarde.example.com",
            api_key="your-api-key",
            tenant_uuid="tenant-uuid"
        ) as client:
            result = await client.create_keyword({
                "keyword_text": "example keyword",
                "search_volume": 1000
            })
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        tenant_uuid: str,
        timeout: int = 30,
        retry_config: Optional[RetryConfig] = None,
        session: Optional[ClientSession] = None
    ):
        """
        Initialize EnGarde API client.

        Args:
            api_url: Base URL of EnGarde API (e.g., "https://api.engarde.com")
            api_key: API authentication key
            tenant_uuid: UUID of the tenant for multi-tenant operations
            timeout: Request timeout in seconds (default: 30)
            retry_config: Custom retry configuration (optional)
            session: Existing aiohttp session to reuse (optional)
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.tenant_uuid = tenant_uuid
        self.timeout = ClientTimeout(total=timeout)
        self.retry_config = retry_config or RetryConfig()
        self._session: Optional[ClientSession] = session
        self._session_owned = session is None

        logger.info(
            f"Initialized EnGardeAPIClient - URL: {self.api_url}, "
            f"Tenant: {self.tenant_uuid}, Timeout: {timeout}s"
        )

    async def __aenter__(self):
        """Async context manager entry."""
        if self._session is None:
            self._session = ClientSession(
                timeout=self.timeout,
                headers=self._get_default_headers()
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session_owned and self._session:
            await self._session.close()
            self._session = None

    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for all requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Tenant-UUID": self.tenant_uuid,
            "User-Agent": "Onside-Walker-Agent/1.0"
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry: bool = True
    ) -> APIResponse:
        """
        Make HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/api/v1/keywords")
            data: Request body data (for POST/PUT)
            params: Query parameters
            retry: Whether to retry on failure

        Returns:
            APIResponse object with result

        Raises:
            EnGardeAPIError: On API errors
        """
        if self._session is None:
            raise EnGardeAPIError("Client session not initialized. Use async context manager.")

        url = f"{self.api_url}{endpoint}"
        attempt = 0
        last_error = None

        while attempt < (self.retry_config.max_attempts if retry else 1):
            attempt += 1

            try:
                logger.debug(
                    f"[Attempt {attempt}/{self.retry_config.max_attempts}] "
                    f"{method} {url} - Params: {params}, Data: {data}"
                )

                async with self._session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params
                ) as response:
                    return await self._handle_response(response)

            except (ClientError, asyncio.TimeoutError) as e:
                last_error = e
                logger.warning(
                    f"Request failed (attempt {attempt}/{self.retry_config.max_attempts}): {str(e)}"
                )

                if attempt < self.retry_config.max_attempts and retry:
                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    raise EnGardeAPIError(f"Request failed after {attempt} attempts: {str(e)}")

        raise EnGardeAPIError(f"Request failed: {str(last_error)}")

    async def _handle_response(self, response: ClientResponse) -> APIResponse:
        """
        Handle HTTP response and convert to APIResponse.

        Args:
            response: aiohttp ClientResponse

        Returns:
            APIResponse object

        Raises:
            EnGardeAPIError: On error status codes
        """
        status_code = response.status
        request_id = response.headers.get('X-Request-ID')

        try:
            response_data = await response.json()
        except Exception:
            response_data = await response.text()

        # Handle success responses (2xx)
        if 200 <= status_code < 300:
            logger.info(f"Request successful: {status_code} - {response.url}")
            return APIResponse(
                success=True,
                data=response_data,
                status_code=status_code,
                request_id=request_id
            )

        # Handle error responses
        error_message = self._extract_error_message(response_data, status_code)

        logger.error(
            f"Request failed: {status_code} - {response.url} - Error: {error_message}"
        )

        # Raise specific exceptions based on status code
        if status_code == 401 or status_code == 403:
            raise EnGardeAuthenticationError(f"Authentication failed: {error_message}")
        elif status_code == 404:
            raise EnGardeNotFoundError(f"Resource not found: {error_message}")
        elif status_code == 422:
            raise EnGardeValidationError(f"Validation error: {error_message}")
        elif status_code == 429:
            raise EnGardeRateLimitError(f"Rate limit exceeded: {error_message}")
        elif status_code >= 500:
            raise EnGardeServerError(f"Server error: {error_message}")
        else:
            raise EnGardeAPIError(f"API error ({status_code}): {error_message}")

    def _extract_error_message(self, response_data: Any, status_code: int) -> str:
        """Extract error message from response data."""
        if isinstance(response_data, dict):
            return response_data.get('detail') or response_data.get('error') or response_data.get('message') or str(response_data)
        return str(response_data)

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff."""
        delay = min(
            self.retry_config.initial_delay * (self.retry_config.exponential_base ** (attempt - 1)),
            self.retry_config.max_delay
        )
        return delay

    # ========================================================================
    # KEYWORD OPERATIONS
    # ========================================================================

    async def create_keyword(self, keyword_data: Dict[str, Any]) -> APIResponse:
        """
        Create a new keyword in EnGarde.

        Args:
            keyword_data: Keyword data matching EnGardeKeywordSchema

        Returns:
            APIResponse with created keyword data

        Example:
            response = await client.create_keyword({
                "keyword_text": "example keyword",
                "search_volume": 1000,
                "competition_score": 65.5,
                "cpc_estimate": 2.50
            })
        """
        logger.info(f"Creating keyword: {keyword_data.get('keyword_text')}")

        return await self._make_request(
            method="POST",
            endpoint=f"/api/v1/tenants/{self.tenant_uuid}/keywords",
            data=keyword_data
        )

    async def bulk_create_keywords(self, keywords: List[Dict[str, Any]]) -> APIResponse:
        """
        Create multiple keywords in a single request.

        Args:
            keywords: List of keyword data dictionaries

        Returns:
            APIResponse with bulk creation results
        """
        logger.info(f"Bulk creating {len(keywords)} keywords")

        return await self._make_request(
            method="POST",
            endpoint=f"/api/v1/tenants/{self.tenant_uuid}/keywords/bulk",
            data={"keywords": keywords}
        )

    async def get_keyword(self, keyword_id: int) -> APIResponse:
        """Get keyword by ID."""
        return await self._make_request(
            method="GET",
            endpoint=f"/api/v1/tenants/{self.tenant_uuid}/keywords/{keyword_id}"
        )

    async def check_keyword_exists(self, keyword_text: str) -> APIResponse:
        """
        Check if a keyword already exists.

        Args:
            keyword_text: Keyword text to check

        Returns:
            APIResponse with exists flag and existing keyword data if found
        """
        return await self._make_request(
            method="GET",
            endpoint=f"/api/v1/tenants/{self.tenant_uuid}/keywords/check",
            params={"keyword_text": keyword_text}
        )

    # ========================================================================
    # COMPETITOR OPERATIONS
    # ========================================================================

    async def create_competitor(self, competitor_data: Dict[str, Any]) -> APIResponse:
        """
        Create a new competitor in EnGarde.

        Args:
            competitor_data: Competitor data matching EnGardeCompetitorSchema

        Returns:
            APIResponse with created competitor data
        """
        logger.info(f"Creating competitor: {competitor_data.get('competitor_name')}")

        return await self._make_request(
            method="POST",
            endpoint=f"/api/v1/tenants/{self.tenant_uuid}/competitors",
            data=competitor_data
        )

    async def bulk_create_competitors(self, competitors: List[Dict[str, Any]]) -> APIResponse:
        """Create multiple competitors in a single request."""
        logger.info(f"Bulk creating {len(competitors)} competitors")

        return await self._make_request(
            method="POST",
            endpoint=f"/api/v1/tenants/{self.tenant_uuid}/competitors/bulk",
            data={"competitors": competitors}
        )

    async def get_competitor(self, competitor_id: int) -> APIResponse:
        """Get competitor by ID."""
        return await self._make_request(
            method="GET",
            endpoint=f"/api/v1/tenants/{self.tenant_uuid}/competitors/{competitor_id}"
        )

    async def check_competitor_exists(self, domain: str) -> APIResponse:
        """
        Check if a competitor already exists by domain.

        Args:
            domain: Competitor domain to check

        Returns:
            APIResponse with exists flag and existing competitor data if found
        """
        return await self._make_request(
            method="GET",
            endpoint=f"/api/v1/tenants/{self.tenant_uuid}/competitors/check",
            params={"domain": domain}
        )

    # ========================================================================
    # CONTENT IDEA OPERATIONS
    # ========================================================================

    async def create_content_idea(self, content_idea_data: Dict[str, Any]) -> APIResponse:
        """
        Create a new content idea in EnGarde.

        Args:
            content_idea_data: Content idea data matching EnGardeContentIdeaSchema

        Returns:
            APIResponse with created content idea data
        """
        logger.info(f"Creating content idea: {content_idea_data.get('title')}")

        return await self._make_request(
            method="POST",
            endpoint=f"/api/v1/tenants/{self.tenant_uuid}/content-ideas",
            data=content_idea_data
        )

    async def bulk_create_content_ideas(self, content_ideas: List[Dict[str, Any]]) -> APIResponse:
        """Create multiple content ideas in a single request."""
        logger.info(f"Bulk creating {len(content_ideas)} content ideas")

        return await self._make_request(
            method="POST",
            endpoint=f"/api/v1/tenants/{self.tenant_uuid}/content-ideas/bulk",
            data={"content_ideas": content_ideas}
        )

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    async def health_check(self) -> APIResponse:
        """
        Check API health and connectivity.

        Returns:
            APIResponse with health status
        """
        return await self._make_request(
            method="GET",
            endpoint="/health",
            retry=False
        )

    async def verify_authentication(self) -> APIResponse:
        """
        Verify that authentication is working.

        Returns:
            APIResponse with authentication status
        """
        return await self._make_request(
            method="GET",
            endpoint="/api/v1/auth/verify",
            retry=False
        )
