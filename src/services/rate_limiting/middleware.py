"""
Rate Limiting Middleware for FastAPI

This middleware applies rate limiting to all API endpoints and adds
rate limit headers to responses.
"""
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .rate_limiter import get_rate_limiter

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to apply rate limiting to API endpoints.

    Adds X-RateLimit-* headers to all responses:
    - X-RateLimit-Limit: Maximum number of requests allowed in the window
    - X-RateLimit-Remaining: Number of requests remaining in the window
    - X-RateLimit-Reset: Unix timestamp when the rate limit resets
    """

    def __init__(self, app: ASGIApp, redis_client=None):
        """Initialize rate limit middleware.

        Args:
            app: FastAPI application
            redis_client: Optional Redis client for distributed rate limiting
        """
        super().__init__(app)
        self.rate_limiter = get_rate_limiter(redis_client)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with rate limit headers

        Raises:
            HTTPException: 429 Too Many Requests if rate limit exceeded
        """
        # Skip rate limiting for health check and documentation endpoints
        if request.url.path in ['/health', '/api/docs', '/api/redoc', '/openapi.json']:
            return await call_next(request)

        # Get identifier (user ID or IP address)
        identifier = self._get_identifier(request)

        # Check if user is admin (admins bypass rate limits)
        is_admin = self._is_admin_user(request)

        # Get endpoint path
        endpoint = request.url.path

        # Check rate limit
        is_allowed, rate_info = self.rate_limiter.check_rate_limit(
            identifier=identifier,
            endpoint=endpoint,
            is_admin=is_admin
        )

        # If rate limit exceeded, return 429
        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for {identifier} on {endpoint}. "
                f"Limit: {rate_info['limit']}, Reset at: {rate_info['reset']}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    'error': 'Rate limit exceeded',
                    'message': f"Too many requests. Please try again after {rate_info['reset']}.",
                    'limit': rate_info['limit'],
                    'reset': rate_info['reset']
                },
                headers={
                    'X-RateLimit-Limit': str(rate_info['limit']),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(rate_info['reset']),
                    'Retry-After': str(rate_info['reset'] - int(request.state._time))
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
        response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
        response.headers['X-RateLimit-Reset'] = str(rate_info['reset'])

        return response

    def _get_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting.

        Uses authenticated user ID if available, otherwise falls back to IP address.

        Args:
            request: Incoming HTTP request

        Returns:
            Unique identifier string
        """
        # Try to get user from request state (set by auth middleware)
        if hasattr(request.state, 'user') and request.state.user:
            user = request.state.user
            if hasattr(user, 'id'):
                return f"user:{user.id}"

        # Fall back to IP address
        # Check for forwarded IP (when behind proxy)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Get first IP in chain
            client_ip = forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.client.host if request.client else 'unknown'

        return f"ip:{client_ip}"

    def _is_admin_user(self, request: Request) -> bool:
        """Check if request is from admin user.

        Args:
            request: Incoming HTTP request

        Returns:
            True if user is admin, False otherwise
        """
        if hasattr(request.state, 'user') and request.state.user:
            user = request.state.user
            # Check for admin role
            if hasattr(user, 'role'):
                return user.role == 'admin' or user.role == 'ADMIN'
            if hasattr(user, 'is_admin'):
                return user.is_admin

        return False
