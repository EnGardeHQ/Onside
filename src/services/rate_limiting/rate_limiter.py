"""
Rate Limiting Service

This module provides comprehensive rate limiting functionality with Redis backend support
for distributed rate limiting across multiple application instances.

Features:
- Sliding window rate limiting algorithm
- Redis-backed distributed rate limiting
- Per-endpoint and per-user rate limits
- Rate limit headers in responses (X-RateLimit-*)
- Admin bypass functionality
- Configurable limits and windows
"""
import logging
import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Configuration for rate limits."""

    # Default rate limits per endpoint category
    DEFAULT_LIMITS = {
        # Authentication endpoints - stricter limits
        '/api/v1/auth/login': {'limit': 5, 'window': 60},  # 5 per minute
        '/api/v1/auth/register': {'limit': 3, 'window': 300},  # 3 per 5 minutes
        '/api/v1/auth/reset-password': {'limit': 3, 'window': 300},

        # Data ingestion - moderate limits
        '/api/v1/companies': {'limit': 100, 'window': 60},
        '/api/v1/competitors': {'limit': 100, 'window': 60},
        '/api/v1/domains': {'limit': 100, 'window': 60},

        # Report generation - resource intensive
        '/api/v1/reports/generate': {'limit': 10, 'window': 60},
        '/api/v1/reports/export': {'limit': 20, 'window': 60},

        # Search endpoints - moderate limits
        '/api/v1/links/search': {'limit': 50, 'window': 60},
        '/api/v1/content/search': {'limit': 50, 'window': 60},

        # External API calls - strict limits to conserve quota
        '/api/v1/seo/pagespeed': {'limit': 25, 'window': 60},
        '/api/v1/analytics/google': {'limit': 25, 'window': 60},

        # Default for all other endpoints
        'default': {'limit': 100, 'window': 60}
    }

    @classmethod
    def get_limit(cls, endpoint: str) -> Dict[str, int]:
        """Get rate limit configuration for an endpoint.

        Args:
            endpoint: The API endpoint path

        Returns:
            Dictionary with 'limit' and 'window' keys
        """
        # Exact match
        if endpoint in cls.DEFAULT_LIMITS:
            return cls.DEFAULT_LIMITS[endpoint]

        # Pattern matching for dynamic routes
        for pattern, config in cls.DEFAULT_LIMITS.items():
            if pattern != 'default' and endpoint.startswith(pattern.rstrip('*')):
                return config

        return cls.DEFAULT_LIMITS['default']


class RateLimiter:
    """
    Rate limiter with Redis backend support for distributed environments.

    Uses sliding window algorithm for accurate rate limiting.
    """

    def __init__(self, redis_client=None, prefix: str = 'rate_limit'):
        """Initialize the rate limiter.

        Args:
            redis_client: Optional Redis client for distributed rate limiting
            prefix: Prefix for rate limit keys
        """
        self.redis_client = redis_client
        self.prefix = prefix
        self.memory_store = defaultdict(list)  # Fallback in-memory store
        self.use_redis = redis_client is not None

        if self.use_redis:
            try:
                self.redis_client.ping()
                logger.info("Rate limiter initialized with Redis backend")
            except Exception as e:
                logger.warning(f"Redis unavailable, falling back to in-memory: {e}")
                self.use_redis = False
        else:
            logger.info("Rate limiter initialized with in-memory backend")

    def _make_key(self, identifier: str, endpoint: str) -> str:
        """Create a rate limit key.

        Args:
            identifier: User ID or IP address
            endpoint: API endpoint path

        Returns:
            Rate limit key
        """
        # Hash endpoint to keep key size manageable
        endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()[:8]
        return f"{self.prefix}:{identifier}:{endpoint_hash}"

    def check_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        limit: Optional[int] = None,
        window: Optional[int] = None,
        is_admin: bool = False
    ) -> Tuple[bool, Dict[str, int]]:
        """Check if request is within rate limit.

        Args:
            identifier: User ID or IP address
            endpoint: API endpoint path
            limit: Optional custom limit (overrides default)
            window: Optional custom window in seconds (overrides default)
            is_admin: Whether user is admin (bypasses limits)

        Returns:
            Tuple of (is_allowed, rate_limit_info)
            rate_limit_info contains: limit, remaining, reset_at
        """
        # Admin users bypass rate limits
        if is_admin:
            config = RateLimitConfig.get_limit(endpoint)
            return True, {
                'limit': config['limit'],
                'remaining': config['limit'],
                'reset': int(time.time()) + config['window']
            }

        # Get rate limit configuration
        config = RateLimitConfig.get_limit(endpoint)
        effective_limit = limit or config['limit']
        effective_window = window or config['window']

        current_time = time.time()
        key = self._make_key(identifier, endpoint)

        if self.use_redis:
            return self._check_redis(
                key, current_time, effective_limit, effective_window
            )
        else:
            return self._check_memory(
                key, current_time, effective_limit, effective_window
            )

    def _check_redis(
        self,
        key: str,
        current_time: float,
        limit: int,
        window: int
    ) -> Tuple[bool, Dict[str, int]]:
        """Check rate limit using Redis backend.

        Uses sorted set (ZSET) for sliding window implementation.
        """
        try:
            # Remove old entries outside the window
            window_start = current_time - window
            self.redis_client.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            request_count = self.redis_client.zcard(key)

            # Calculate remaining and reset time
            remaining = max(0, limit - request_count)
            reset_at = int(current_time + window)

            if request_count < limit:
                # Add current request
                self.redis_client.zadd(key, {str(current_time): current_time})
                # Set expiration to window size
                self.redis_client.expire(key, window)

                return True, {
                    'limit': limit,
                    'remaining': remaining - 1,  # Account for current request
                    'reset': reset_at
                }
            else:
                return False, {
                    'limit': limit,
                    'remaining': 0,
                    'reset': reset_at
                }
        except Exception as e:
            logger.error(f"Redis error in rate limiting: {e}")
            # Fall back to allowing the request on error
            return True, {
                'limit': limit,
                'remaining': limit - 1,
                'reset': int(current_time + window)
            }

    def _check_memory(
        self,
        key: str,
        current_time: float,
        limit: int,
        window: int
    ) -> Tuple[bool, Dict[str, int]]:
        """Check rate limit using in-memory backend.

        Uses list of timestamps for sliding window implementation.
        """
        # Clean up old entries
        window_start = current_time - window
        self.memory_store[key] = [
            ts for ts in self.memory_store[key] if ts > window_start
        ]

        request_count = len(self.memory_store[key])
        remaining = max(0, limit - request_count)
        reset_at = int(current_time + window)

        if request_count < limit:
            self.memory_store[key].append(current_time)
            return True, {
                'limit': limit,
                'remaining': remaining - 1,
                'reset': reset_at
            }
        else:
            return False, {
                'limit': limit,
                'remaining': 0,
                'reset': reset_at
            }

    def reset_limit(self, identifier: str, endpoint: str) -> bool:
        """Reset rate limit for a specific identifier and endpoint.

        Args:
            identifier: User ID or IP address
            endpoint: API endpoint path

        Returns:
            True if reset successful, False otherwise
        """
        key = self._make_key(identifier, endpoint)

        try:
            if self.use_redis:
                self.redis_client.delete(key)
            else:
                if key in self.memory_store:
                    del self.memory_store[key]
            return True
        except Exception as e:
            logger.error(f"Error resetting rate limit: {e}")
            return False

    def get_stats(self, identifier: str, endpoint: str) -> Dict:
        """Get current rate limit statistics.

        Args:
            identifier: User ID or IP address
            endpoint: API endpoint path

        Returns:
            Dictionary with rate limit statistics
        """
        key = self._make_key(identifier, endpoint)
        config = RateLimitConfig.get_limit(endpoint)
        current_time = time.time()
        window_start = current_time - config['window']

        try:
            if self.use_redis:
                self.redis_client.zremrangebyscore(key, 0, window_start)
                request_count = self.redis_client.zcard(key)
            else:
                self.memory_store[key] = [
                    ts for ts in self.memory_store[key] if ts > window_start
                ]
                request_count = len(self.memory_store[key])

            return {
                'endpoint': endpoint,
                'identifier': identifier,
                'limit': config['limit'],
                'window_seconds': config['window'],
                'requests_in_window': request_count,
                'remaining': max(0, config['limit'] - request_count),
                'reset_at': datetime.fromtimestamp(current_time + config['window']).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting rate limit stats: {e}")
            return {
                'error': str(e),
                'endpoint': endpoint,
                'identifier': identifier
            }


# Singleton instance
_rate_limiter_instance = None


def get_rate_limiter(redis_client=None) -> RateLimiter:
    """Get the global rate limiter instance.

    Args:
        redis_client: Optional Redis client for distributed rate limiting

    Returns:
        RateLimiter instance
    """
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter(redis_client)
    return _rate_limiter_instance
