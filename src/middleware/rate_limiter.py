"""
Rate Limiting Middleware

Provides comprehensive rate limiting for FastAPI using Redis backend:
- Per-user rate limits
- Per-endpoint rate limits
- IP-based rate limits
- Sliding window algorithm
- Rate limit headers (X-RateLimit-*)
- Configurable limits and windows
- Redis-backed distributed rate limiting
- Graceful fallback to in-memory limiting
"""
import time
import logging
from typing import Callable, Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import FastAPI, status
import hashlib

try:
    import redis.asyncio as aioredis
    from redis.asyncio import Redis
    from redis.exceptions import RedisError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None
    Redis = None
    RedisError = Exception

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimitRule:
    """Define a rate limit rule."""

    def __init__(
        self,
        requests: int,
        window: int,
        scope: str = "global"
    ):
        """Initialize rate limit rule.

        Args:
            requests: Maximum number of requests
            window: Time window in seconds
            scope: Scope of the limit (global, user, ip, endpoint)
        """
        self.requests = requests
        self.window = window
        self.scope = scope

    def __repr__(self):
        return f"RateLimitRule({self.requests} requests per {self.window}s, scope={self.scope})"


class InMemoryRateLimiter:
    """In-memory rate limiter using sliding window."""

    def __init__(self):
        """Initialize in-memory rate limiter."""
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window: int
    ) -> Tuple[bool, int, int]:
        """Check if request is within rate limit.

        Args:
            key: Rate limit key
            max_requests: Maximum allowed requests
            window: Time window in seconds

        Returns:
            Tuple of (allowed, remaining, reset_time)
        """
        now = time.time()
        cutoff = now - window

        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > cutoff
        ]

        current_requests = len(self.requests[key])

        if current_requests < max_requests:
            self.requests[key].append(now)
            remaining = max_requests - current_requests - 1
            reset_time = int(now + window)
            return True, remaining, reset_time
        else:
            # Calculate when the oldest request expires
            if self.requests[key]:
                oldest = min(self.requests[key])
                reset_time = int(oldest + window)
            else:
                reset_time = int(now + window)
            return False, 0, reset_time


class RedisRateLimiter:
    """Redis-backed distributed rate limiter using sliding window."""

    def __init__(self, redis_client: Redis):
        """Initialize Redis rate limiter.

        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window: int
    ) -> Tuple[bool, int, int]:
        """Check if request is within rate limit using Redis.

        Args:
            key: Rate limit key
            max_requests: Maximum allowed requests
            window: Time window in seconds

        Returns:
            Tuple of (allowed, remaining, reset_time)
        """
        now = time.time()
        cutoff = now - window

        try:
            # Use Redis sorted set for sliding window
            pipe = self.redis.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(key, 0, cutoff)

            # Count current requests
            pipe.zcard(key)

            # Add current request timestamp
            pipe.zadd(key, {str(now): now})

            # Set expiration on the key
            pipe.expire(key, window)

            # Execute pipeline
            results = await pipe.execute()
            current_requests = results[1]  # Result of ZCARD

            if current_requests < max_requests:
                remaining = max_requests - current_requests - 1
                reset_time = int(now + window)
                return True, remaining, reset_time
            else:
                # Request limit exceeded
                # Get the oldest timestamp to calculate reset time
                oldest_entries = await self.redis.zrange(key, 0, 0, withscores=True)
                if oldest_entries:
                    oldest_time = oldest_entries[0][1]
                    reset_time = int(oldest_time + window)
                else:
                    reset_time = int(now + window)

                # Remove the request we just added since we're rejecting it
                await self.redis.zrem(key, str(now))

                return False, 0, reset_time

        except RedisError as e:
            logger.error(f"Redis error in rate limiting: {e}")
            # Fail open - allow the request if Redis is down
            return True, max_requests, int(now + window)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting API requests.

    Features:
    - Per-user rate limits
    - Per-IP rate limits
    - Per-endpoint rate limits
    - Redis-backed distributed limiting
    - Configurable rules
    - Rate limit headers in responses
    - Graceful degradation
    """

    def __init__(
        self,
        app: FastAPI,
        redis_client: Optional[Redis] = None,
        default_limit: Optional[RateLimitRule] = None,
        enable_rate_limiting: bool = True
    ):
        """Initialize rate limiter middleware.

        Args:
            app: FastAPI application instance
            redis_client: Optional Redis client for distributed limiting
            default_limit: Default rate limit rule
            enable_rate_limiting: Enable/disable rate limiting
        """
        super().__init__(app)
        self.enable_rate_limiting = enable_rate_limiting

        # Initialize rate limiter backend
        if redis_client and REDIS_AVAILABLE:
            self.limiter = RedisRateLimiter(redis_client)
            self.backend = "redis"
            logger.info("Rate limiting using Redis backend")
        else:
            self.limiter = InMemoryRateLimiter()
            self.backend = "memory"
            logger.info("Rate limiting using in-memory backend")

        # Default rate limit: 100 requests per minute
        self.default_limit = default_limit or RateLimitRule(
            requests=100,
            window=60,
            scope="ip"
        )

        # Endpoint-specific rate limits
        self.endpoint_limits: Dict[str, RateLimitRule] = {
            # Brand analysis endpoint - more restrictive
            "/api/v1/brand-analysis/initiate": RateLimitRule(
                requests=5,
                window=3600,  # 5 requests per hour
                scope="user"
            ),
            # SERP analysis endpoints
            "/api/v1/seo/serp-analysis": RateLimitRule(
                requests=20,
                window=3600,  # 20 requests per hour
                scope="user"
            ),
            # Report generation
            "/api/v1/reports/generate": RateLimitRule(
                requests=10,
                window=3600,  # 10 requests per hour
                scope="user"
            ),
        }

        # Exempt paths (no rate limiting)
        self.exempt_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]

    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting.

        Args:
            request: Incoming request

        Returns:
            Client identifier string
        """
        # Try to get user ID from auth
        user_id = None
        if hasattr(request.state, 'user'):
            user_id = getattr(request.state.user, 'id', None)

        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}"

    def _get_rate_limit_key(
        self,
        request: Request,
        rule: RateLimitRule
    ) -> str:
        """Generate rate limit key.

        Args:
            request: Incoming request
            rule: Rate limit rule

        Returns:
            Rate limit key
        """
        endpoint = request.url.path
        client_id = self._get_client_identifier(request)

        # Construct key based on scope
        if rule.scope == "user":
            key = f"ratelimit:user:{client_id}:{endpoint}"
        elif rule.scope == "ip":
            key = f"ratelimit:ip:{client_id}:{endpoint}"
        elif rule.scope == "endpoint":
            key = f"ratelimit:endpoint:{endpoint}"
        else:  # global
            key = f"ratelimit:global:{endpoint}"

        return key

    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from rate limiting.

        Args:
            path: Request path

        Returns:
            True if exempt, False otherwise
        """
        return any(path.startswith(exempt) for exempt in self.exempt_paths)

    async def _check_rate_limit(
        self,
        request: Request,
        rule: RateLimitRule
    ) -> Tuple[bool, int, int]:
        """Check rate limit for request.

        Args:
            request: Incoming request
            rule: Rate limit rule to apply

        Returns:
            Tuple of (allowed, remaining, reset_time)
        """
        key = self._get_rate_limit_key(request, rule)

        if self.backend == "redis":
            return await self.limiter.check_rate_limit(
                key,
                rule.requests,
                rule.window
            )
        else:
            # Synchronous in-memory check
            return self.limiter.check_rate_limit(
                key,
                rule.requests,
                rule.window
            )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response from application or rate limit error
        """
        # Skip if rate limiting is disabled
        if not self.enable_rate_limiting:
            return await call_next(request)

        # Skip exempt paths
        if self._is_exempt(request.url.path):
            return await call_next(request)

        # Get rate limit rule for endpoint
        rule = self.endpoint_limits.get(
            request.url.path,
            self.default_limit
        )

        # Check rate limit
        allowed, remaining, reset_time = await self._check_rate_limit(
            request,
            rule
        )

        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(rule.requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
            "X-RateLimit-Window": str(rule.window)
        }

        if not allowed:
            # Rate limit exceeded
            retry_after = reset_time - int(time.time())

            logger.warning(
                f"Rate limit exceeded for {request.url.path} - "
                f"Client: {self._get_client_identifier(request)}, "
                f"Rule: {rule}"
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Maximum {rule.requests} requests per {rule.window} seconds.",
                    "retry_after": retry_after,
                    "limit": rule.requests,
                    "window": rule.window
                },
                headers={
                    **headers,
                    "Retry-After": str(retry_after)
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response

    def add_endpoint_limit(
        self,
        path: str,
        requests: int,
        window: int,
        scope: str = "user"
    ):
        """Add or update rate limit for specific endpoint.

        Args:
            path: Endpoint path
            requests: Maximum requests
            window: Time window in seconds
            scope: Rate limit scope
        """
        self.endpoint_limits[path] = RateLimitRule(
            requests=requests,
            window=window,
            scope=scope
        )
        logger.info(f"Added rate limit for {path}: {requests} requests per {window}s")

    def remove_endpoint_limit(self, path: str):
        """Remove rate limit for specific endpoint.

        Args:
            path: Endpoint path
        """
        if path in self.endpoint_limits:
            del self.endpoint_limits[path]
            logger.info(f"Removed rate limit for {path}")

    def get_stats(self) -> Dict:
        """Get rate limiting statistics.

        Returns:
            Dictionary with rate limit statistics
        """
        return {
            'enabled': self.enable_rate_limiting,
            'backend': self.backend,
            'default_limit': {
                'requests': self.default_limit.requests,
                'window': self.default_limit.window,
                'scope': self.default_limit.scope
            },
            'endpoint_limits': {
                path: {
                    'requests': rule.requests,
                    'window': rule.window,
                    'scope': rule.scope
                }
                for path, rule in self.endpoint_limits.items()
            },
            'exempt_paths': self.exempt_paths
        }


# Global instance
_rate_limiter: Optional[RateLimiterMiddleware] = None


def get_rate_limiter() -> Optional[RateLimiterMiddleware]:
    """Get the global rate limiter instance.

    Returns:
        RateLimiterMiddleware instance or None
    """
    return _rate_limiter


def set_rate_limiter(limiter: RateLimiterMiddleware):
    """Set the global rate limiter instance.

    Args:
        limiter: RateLimiterMiddleware instance
    """
    global _rate_limiter
    _rate_limiter = limiter
