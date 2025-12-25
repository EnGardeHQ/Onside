"""
Base API Client for external service integrations.

This module provides a base class for making API requests to external services
with built-in rate limiting, retries, and error handling.
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional, TypeVar, Callable, Type, Union

import aiohttp
from aiohttp import ClientSession, ClientResponse, ClientError
from pydantic import BaseModel, ValidationError
from ratelimit import limits, sleep_and_retry

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class APIError(Exception):
    """Base exception for API-related errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Any = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    pass

class APIClient(ABC):
    """Base class for API clients.
    
    Features:
    - Rate limiting
    - Retry mechanism
    - Request/response validation
    - Error handling
    - Session management
    """
    
    BASE_URL: str = ""
    RATE_LIMIT: int = 100  # Requests per minute
    RATE_PERIOD: int = 60  # Seconds
    DEFAULT_TIMEOUT: int = 30  # Seconds
    
    def __init__(self, api_key: Optional[str] = None, session: Optional[ClientSession] = None):
        """Initialize the API client.
        
        Args:
            api_key: API key for authentication
            session: Optional aiohttp ClientSession for connection pooling
        """
        self.api_key = api_key
        self._session = session
        self._session_owner = session is None
        self._base_headers = self._get_base_headers()
    
    async def __aenter__(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session_owner and self._session:
            await self._session.close()
            self._session = None
    
    def _get_base_headers(self) -> Dict[str, str]:
        """Get base headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    @sleep_and_retry
    @limits(calls=RATE_LIMIT, period=RATE_PERIOD)
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        model: Optional[Type[T]] = None,
    ) -> Union[Dict[str, Any], T]:
        """Make an HTTP request with rate limiting and retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body
            headers: Additional headers
            timeout: Request timeout in seconds
            model: Pydantic model for response validation
            
        Returns:
            Parsed JSON response or validated model instance
            
        Raises:
            APIError: For API-related errors
            RateLimitError: When rate limit is exceeded
            ValidationError: When response validation fails
        """
        url = f"{self.BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = {**self._base_headers, **(headers or {})}
        timeout = aiohttp.ClientTimeout(total=timeout or self.DEFAULT_TIMEOUT)
        
        try:
            async with self._session.request(
                method=method,
                url=url,
                params=params,
                json=data if isinstance(data, dict) else None,
                data=data if isinstance(data, str) else None,
                headers=headers,
                timeout=timeout,
            ) as response:
                return await self._handle_response(response, model)
                
        except asyncio.TimeoutError as e:
            raise APIError(f"Request to {url} timed out") from e
        except ClientError as e:
            raise APIError(f"Request failed: {str(e)}") from e
    
    async def _handle_response(
        self, response: ClientResponse, model: Optional[Type[T]] = None
    ) -> Union[Dict[str, Any], T]:
        """Handle API response."""
        try:
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            
            if "application/json" in content_type:
                data = await response.json()
            else:
                data = await response.text()
                
            if model:
                try:
                    if isinstance(data, list):
                        return [model.parse_obj(item) for item in data]
                    return model.parse_obj(data)
                except ValidationError as e:
                    logger.error(f"Response validation failed: {e}")
                    raise
                    
            return data
            
        except aiohttp.ClientResponseError as e:
            if e.status == 429:  # Rate limit exceeded
                retry_after = int(response.headers.get("Retry-After", 60))
                raise RateLimitError(
                    f"Rate limit exceeded. Try again in {retry_after} seconds",
                    status_code=429,
                    details={"retry_after": retry_after},
                ) from e
                
            error_msg = f"API request failed with status {e.status}"
            try:
                error_data = await response.json()
                error_msg = error_data.get("error", error_data)
            except (ValueError, KeyError):
                pass
                
            raise APIError(
                error_msg,
                status_code=e.status,
                details={"response": str(e)},
            ) from e
    
    # Convenience methods
    async def get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None, 
        model: Optional[Type[T]] = None,
        **kwargs
    ) -> Union[Dict[str, Any], T]:
        """Make a GET request."""
        return await self._request("GET", endpoint, params=params, model=model, **kwargs)
    
    async def post(
        self, 
        endpoint: str, 
        data: Optional[Union[Dict[str, Any], str]] = None,
        model: Optional[Type[T]] = None,
        **kwargs
    ) -> Union[Dict[str, Any], T]:
        """Make a POST request."""
        return await self._request("POST", endpoint, data=data, model=model, **kwargs)
    
    # Abstract methods
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the API connection."""
        pass
    
    @abstractmethod
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        pass
