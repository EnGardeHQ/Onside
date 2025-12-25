"""
Redis Caching Service

Enhanced caching service with full Redis support including:
- Distributed caching across multiple instances
- Cache warming functionality
- Cache invalidation strategies (time-based, event-based)
- Cache statistics and monitoring
- Cache key namespacing
- TTL-based expiration
"""
import logging
import json
import pickle
from typing import Any, Optional, Dict, List, Callable
from datetime import datetime, timedelta
from functools import wraps
import hashlib

from src.core.cache import Cache  # Import existing cache for backward compatibility

logger = logging.getLogger(__name__)


class RedisCacheService:
    """
    Enhanced Redis caching service with advanced features.

    Builds upon the existing Cache class with additional functionality.
    """

    def __init__(self, redis_client=None, namespace: str = 'onside'):
        """Initialize Redis cache service.

        Args:
            redis_client: Redis client instance
            namespace: Cache key namespace
        """
        self.cache = Cache(backend='redis' if redis_client else 'memory', redis_client=redis_client)
        self.namespace = namespace
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }

    def _namespaced_key(self, key: str, category: Optional[str] = None) -> str:
        """Create a namespaced cache key.

        Args:
            key: Base cache key
            category: Optional category for organization

        Returns:
            Namespaced key
        """
        if category:
            return f"{self.namespace}:{category}:{key}"
        return f"{self.namespace}:{key}"

    def get(self, key: str, category: Optional[str] = None, default: Any = None) -> Any:
        """Get value from cache with statistics tracking.

        Args:
            key: Cache key
            category: Optional category
            default: Default value if not found

        Returns:
            Cached value or default
        """
        namespaced_key = self._namespaced_key(key, category)
        value = self.cache.get(namespaced_key, default=default)

        if value is not None and value != default:
            self.stats['hits'] += 1
        else:
            self.stats['misses'] += 1

        return value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        category: Optional[str] = None
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            category: Optional category

        Returns:
            True if successful, False otherwise
        """
        namespaced_key = self._namespaced_key(key, category)
        success = self.cache.set(namespaced_key, value, ttl=ttl)

        if success:
            self.stats['sets'] += 1
        else:
            self.stats['errors'] += 1

        return success

    def delete(self, *keys: str, category: Optional[str] = None) -> int:
        """Delete one or more keys from cache.

        Args:
            *keys: One or more keys to delete
            category: Optional category

        Returns:
            Number of keys deleted
        """
        namespaced_keys = [self._namespaced_key(key, category) for key in keys]
        count = self.cache.delete(*namespaced_keys)
        self.stats['deletes'] += count
        return count

    def invalidate_pattern(self, pattern: str, category: Optional[str] = None) -> int:
        """Invalidate all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "user:*")
            category: Optional category

        Returns:
            Number of keys invalidated
        """
        full_pattern = self._namespaced_key(pattern, category)

        try:
            if self.cache._backend == 'redis':
                keys = self.cache._client.keys(full_pattern)
                if keys:
                    count = self.cache._client.delete(*keys)
                    self.stats['deletes'] += count
                    return count
                return 0
            else:
                # In-memory pattern matching
                count = 0
                keys_to_delete = []
                for key in list(self.cache._client.keys()):
                    if key.startswith(full_pattern.replace('*', '')):
                        keys_to_delete.append(key)
                        count += 1

                for key in keys_to_delete:
                    del self.cache._client[key]

                self.stats['deletes'] += count
                return count
        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {e}")
            self.stats['errors'] += 1
            return 0

    def warm_cache(
        self,
        key: str,
        loader: Callable[[], Any],
        ttl: Optional[int] = None,
        category: Optional[str] = None,
        force: bool = False
    ) -> Any:
        """Warm cache with data from loader function.

        Args:
            key: Cache key
            loader: Function to load data if not cached
            ttl: Time to live in seconds
            category: Optional category
            force: Force reload even if cached

        Returns:
            Cached or loaded value
        """
        if not force:
            cached = self.get(key, category=category)
            if cached is not None:
                return cached

        # Load data
        try:
            data = loader()
            self.set(key, data, ttl=ttl, category=category)
            return data
        except Exception as e:
            logger.error(f"Error warming cache for key {key}: {e}")
            self.stats['errors'] += 1
            return None

    def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Any],
        ttl: Optional[int] = None,
        category: Optional[str] = None
    ) -> Any:
        """Get value from cache or compute if missing.

        Args:
            key: Cache key
            compute_fn: Function to compute value if not cached
            ttl: Time to live in seconds
            category: Optional category

        Returns:
            Cached or computed value
        """
        cached = self.get(key, category=category)
        if cached is not None:
            return cached

        try:
            value = compute_fn()
            self.set(key, value, ttl=ttl, category=category)
            return value
        except Exception as e:
            logger.error(f"Error computing value for key {key}: {e}")
            self.stats['errors'] += 1
            return None

    def memoize_with_category(
        self,
        category: str,
        ttl: Optional[int] = None
    ) -> Callable:
        """Decorator to memoize function results with category support.

        Args:
            category: Cache category
            ttl: Time to live in seconds

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                # Generate cache key from function name and arguments
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                if kwargs:
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

                cache_key = hashlib.md5(':'.join(key_parts).encode()).hexdigest()

                # Try to get from cache
                cached = self.get(cache_key, category=category)
                if cached is not None:
                    return cached

                # Compute and cache
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl=ttl, category=category)
                return result

            return wrapper
        return decorator

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_operations = sum([
            self.stats['hits'],
            self.stats['misses'],
            self.stats['sets'],
            self.stats['deletes']
        ])

        hit_rate = 0.0
        if self.stats['hits'] + self.stats['misses'] > 0:
            hit_rate = self.stats['hits'] / (self.stats['hits'] + self.stats['misses'])

        return {
            'backend': self.cache._backend,
            'namespace': self.namespace,
            'statistics': {
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'sets': self.stats['sets'],
                'deletes': self.stats['deletes'],
                'errors': self.stats['errors'],
                'total_operations': total_operations,
                'hit_rate': round(hit_rate * 100, 2)
            }
        }

    def reset_statistics(self) -> None:
        """Reset cache statistics."""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform cache health check.

        Returns:
            Dictionary with health status
        """
        try:
            # Test write
            test_key = self._namespaced_key('__health_check__')
            test_value = {'timestamp': datetime.utcnow().isoformat()}
            write_success = self.cache.set(test_key, test_value, ttl=60)

            # Test read
            read_value = self.cache.get(test_key)
            read_success = read_value is not None

            # Clean up
            self.cache.delete(test_key)

            return {
                'healthy': write_success and read_success,
                'backend': self.cache._backend,
                'write_success': write_success,
                'read_success': read_success,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                'healthy': False,
                'backend': self.cache._backend,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# Category-specific cache services
class APICacheService(RedisCacheService):
    """Cache service for API responses."""

    def __init__(self, redis_client=None):
        super().__init__(redis_client, namespace='api')

    def cache_response(
        self,
        endpoint: str,
        params: Dict[str, Any],
        response: Any,
        ttl: int = 300
    ) -> bool:
        """Cache API response.

        Args:
            endpoint: API endpoint
            params: Request parameters
            response: Response data
            ttl: Time to live in seconds (default 5 minutes)

        Returns:
            True if successful
        """
        # Create cache key from endpoint and params
        param_str = json.dumps(params, sort_keys=True)
        cache_key = hashlib.md5(f"{endpoint}:{param_str}".encode()).hexdigest()

        return self.set(cache_key, response, ttl=ttl, category='responses')

    def get_cached_response(
        self,
        endpoint: str,
        params: Dict[str, Any]
    ) -> Optional[Any]:
        """Get cached API response.

        Args:
            endpoint: API endpoint
            params: Request parameters

        Returns:
            Cached response or None
        """
        param_str = json.dumps(params, sort_keys=True)
        cache_key = hashlib.md5(f"{endpoint}:{param_str}".encode()).hexdigest()

        return self.get(cache_key, category='responses')

    def invalidate_endpoint(self, endpoint: str) -> int:
        """Invalidate all cached responses for an endpoint.

        Args:
            endpoint: API endpoint

        Returns:
            Number of invalidated entries
        """
        pattern = f"responses:*"
        return self.invalidate_pattern(pattern, category='responses')


# Singleton instances
_redis_cache_service = None
_api_cache_service = None


def get_redis_cache_service(redis_client=None) -> RedisCacheService:
    """Get the global Redis cache service instance.

    Args:
        redis_client: Optional Redis client

    Returns:
        RedisCacheService instance
    """
    global _redis_cache_service
    if _redis_cache_service is None:
        _redis_cache_service = RedisCacheService(redis_client)
    return _redis_cache_service


def get_api_cache_service(redis_client=None) -> APICacheService:
    """Get the global API cache service instance.

    Args:
        redis_client: Optional Redis client

    Returns:
        APICacheService instance
    """
    global _api_cache_service
    if _api_cache_service is None:
        _api_cache_service = APICacheService(redis_client)
    return _api_cache_service
