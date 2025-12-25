"""
Async Redis Cache Service for Onside Brand Analysis System

This module provides an async-first caching layer with:
- Async Redis client support (redis.asyncio)
- Cache-aside pattern implementation
- Automatic serialization/deserialization
- TTL management
- Cache statistics and monitoring
- Pattern-based invalidation
- Connection pooling
- Error handling and fallback strategies
"""

import logging
import json
import pickle
from typing import Any, Optional, Dict, List, Callable, Union
from datetime import datetime, timedelta
import hashlib
import asyncio
from functools import wraps
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

try:
    from redis import asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis[asyncio] not available, falling back to memory cache")


class AsyncCacheService:
    """
    Async-first Redis caching service with comprehensive features.

    Features:
    - Async operations for non-blocking I/O
    - Automatic JSON/pickle serialization
    - TTL-based expiration
    - Pattern-based key invalidation
    - Cache statistics tracking
    - Health monitoring
    - Connection pooling
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        namespace: str = "onside",
        default_ttl: int = 300
    ):
        """
        Initialize async cache service.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
            namespace: Cache key namespace for organization
            default_ttl: Default TTL in seconds (5 minutes)
        """
        self.redis_url = redis_url
        self.namespace = namespace
        self.default_ttl = default_ttl
        self.redis: Optional[aioredis.Redis] = None
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize Redis connection pool.

        Returns:
            True if Redis is available, False if using memory fallback
        """
        if self._initialized:
            return self.redis is not None

        if not REDIS_AVAILABLE or not self.redis_url:
            logger.warning("Redis not available, using in-memory cache")
            self._initialized = True
            return False

        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # We handle encoding ourselves
                max_connections=50,
                socket_connect_timeout=5,
                socket_keepalive=True
            )

            # Test connection
            await self.redis.ping()
            logger.info(f"Redis cache initialized: {self.redis_url}")
            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            logger.warning("Falling back to in-memory cache")
            self.redis = None
            self._initialized = True
            return False

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            try:
                await self.redis.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")

    def _make_key(self, key: str, category: Optional[str] = None) -> str:
        """
        Create namespaced cache key.

        Args:
            key: Base key
            category: Optional category for organization

        Returns:
            Namespaced key
        """
        if category:
            return f"{self.namespace}:{category}:{key}"
        return f"{self.namespace}:{key}"

    def _serialize(self, value: Any) -> bytes:
        """
        Serialize value for storage.

        Args:
            value: Value to serialize

        Returns:
            Serialized bytes
        """
        try:
            # Try JSON first (faster and more readable)
            return json.dumps(value).encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(value)

    def _deserialize(self, data: bytes) -> Any:
        """
        Deserialize data from storage.

        Args:
            data: Serialized data

        Returns:
            Deserialized value
        """
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(data)

    async def get(
        self,
        key: str,
        category: Optional[str] = None,
        default: Any = None
    ) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            category: Optional category
            default: Default value if not found

        Returns:
            Cached value or default
        """
        cache_key = self._make_key(key, category)

        try:
            if self.redis:
                # Redis backend
                data = await self.redis.get(cache_key)
                if data is None:
                    self._stats["misses"] += 1
                    return default

                self._stats["hits"] += 1
                return self._deserialize(data)
            else:
                # Memory backend
                if cache_key not in self._memory_cache:
                    self._stats["misses"] += 1
                    return default

                item = self._memory_cache[cache_key]

                # Check expiration
                if item["expires"] and item["expires"] < datetime.utcnow():
                    del self._memory_cache[cache_key]
                    self._stats["misses"] += 1
                    return default

                self._stats["hits"] += 1
                return item["value"]

        except Exception as e:
            logger.error(f"Error getting cache key {cache_key}: {e}")
            self._stats["errors"] += 1
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        category: Optional[str] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default_ttl if None)
            category: Optional category

        Returns:
            True if successful
        """
        cache_key = self._make_key(key, category)
        ttl = ttl if ttl is not None else self.default_ttl

        try:
            if self.redis:
                # Redis backend
                serialized = self._serialize(value)
                if ttl > 0:
                    await self.redis.setex(cache_key, ttl, serialized)
                else:
                    await self.redis.set(cache_key, serialized)

                self._stats["sets"] += 1
                return True
            else:
                # Memory backend
                expires = datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None
                self._memory_cache[cache_key] = {
                    "value": value,
                    "expires": expires
                }
                self._stats["sets"] += 1
                return True

        except Exception as e:
            logger.error(f"Error setting cache key {cache_key}: {e}")
            self._stats["errors"] += 1
            return False

    async def delete(
        self,
        key: str,
        category: Optional[str] = None
    ) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key
            category: Optional category

        Returns:
            True if key was deleted
        """
        cache_key = self._make_key(key, category)

        try:
            if self.redis:
                deleted = await self.redis.delete(cache_key)
                if deleted > 0:
                    self._stats["deletes"] += 1
                return deleted > 0
            else:
                if cache_key in self._memory_cache:
                    del self._memory_cache[cache_key]
                    self._stats["deletes"] += 1
                    return True
                return False

        except Exception as e:
            logger.error(f"Error deleting cache key {cache_key}: {e}")
            self._stats["errors"] += 1
            return False

    async def exists(
        self,
        key: str,
        category: Optional[str] = None
    ) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key
            category: Optional category

        Returns:
            True if key exists
        """
        cache_key = self._make_key(key, category)

        try:
            if self.redis:
                return await self.redis.exists(cache_key) > 0
            else:
                if cache_key not in self._memory_cache:
                    return False

                item = self._memory_cache[cache_key]
                if item["expires"] and item["expires"] < datetime.utcnow():
                    del self._memory_cache[cache_key]
                    return False

                return True

        except Exception as e:
            logger.error(f"Error checking existence of {cache_key}: {e}")
            return False

    async def clear_pattern(
        self,
        pattern: str,
        category: Optional[str] = None
    ) -> int:
        """
        Clear all keys matching pattern.

        Args:
            pattern: Pattern to match (e.g., "user:*")
            category: Optional category

        Returns:
            Number of keys deleted
        """
        full_pattern = self._make_key(pattern, category)

        try:
            if self.redis:
                # Use SCAN for better performance with large keyspaces
                deleted = 0
                async for key in self.redis.scan_iter(match=full_pattern, count=100):
                    await self.redis.delete(key)
                    deleted += 1

                self._stats["deletes"] += deleted
                return deleted
            else:
                # Memory backend - simple pattern matching
                deleted = 0
                pattern_prefix = full_pattern.replace("*", "")
                keys_to_delete = [
                    k for k in self._memory_cache.keys()
                    if k.startswith(pattern_prefix)
                ]

                for key in keys_to_delete:
                    del self._memory_cache[key]
                    deleted += 1

                self._stats["deletes"] += deleted
                return deleted

        except Exception as e:
            logger.error(f"Error clearing pattern {full_pattern}: {e}")
            self._stats["errors"] += 1
            return 0

    async def clear_all(self) -> bool:
        """
        Clear all cache entries in namespace.

        Warning: Use with caution in production!

        Returns:
            True if successful
        """
        try:
            if self.redis:
                # Clear only keys in our namespace
                pattern = f"{self.namespace}:*"
                deleted = 0
                async for key in self.redis.scan_iter(match=pattern, count=1000):
                    await self.redis.delete(key)
                    deleted += 1

                logger.info(f"Cleared {deleted} keys from cache")
                self._stats["deletes"] += deleted
                return True
            else:
                # Clear memory cache
                count = len(self._memory_cache)
                self._memory_cache.clear()
                logger.info(f"Cleared {count} keys from memory cache")
                self._stats["deletes"] += count
                return True

        except Exception as e:
            logger.error(f"Error clearing all cache: {e}")
            self._stats["errors"] += 1
            return False

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int] = None,
        category: Optional[str] = None
    ) -> Any:
        """
        Get value from cache or compute and cache it.

        Cache-aside pattern implementation.

        Args:
            key: Cache key
            factory: Callable that returns value to cache
            ttl: Time to live in seconds
            category: Optional category

        Returns:
            Cached or computed value
        """
        # Try to get from cache
        cached = await self.get(key, category=category)
        if cached is not None:
            return cached

        # Compute value
        try:
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()

            # Cache the value
            await self.set(key, value, ttl=ttl, category=category)
            return value

        except Exception as e:
            logger.error(f"Error in get_or_set for key {key}: {e}")
            self._stats["errors"] += 1
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_ops = sum([
            self._stats["hits"],
            self._stats["misses"],
            self._stats["sets"],
            self._stats["deletes"]
        ])

        hit_rate = 0.0
        if self._stats["hits"] + self._stats["misses"] > 0:
            hit_rate = self._stats["hits"] / (self._stats["hits"] + self._stats["misses"])

        return {
            "backend": "redis" if self.redis else "memory",
            "namespace": self.namespace,
            "statistics": {
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "sets": self._stats["sets"],
                "deletes": self._stats["deletes"],
                "errors": self._stats["errors"],
                "total_operations": total_ops,
                "hit_rate_percent": round(hit_rate * 100, 2)
            }
        }

    def reset_statistics(self):
        """Reset cache statistics."""
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform cache health check.

        Returns:
            Health status information
        """
        try:
            test_key = self._make_key("__health_check__")
            test_value = {"timestamp": datetime.utcnow().isoformat()}

            # Test write
            write_ok = await self.set("__health_check__", test_value, ttl=60)

            # Test read
            read_value = await self.get("__health_check__")
            read_ok = read_value is not None

            # Cleanup
            await self.delete("__health_check__")

            return {
                "healthy": write_ok and read_ok,
                "backend": "redis" if self.redis else "memory",
                "write_success": write_ok,
                "read_success": read_ok,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "backend": "redis" if self.redis else "memory",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Singleton instance
_cache_service: Optional[AsyncCacheService] = None


def get_cache_service(
    redis_url: Optional[str] = None,
    namespace: str = "onside",
    default_ttl: int = 300
) -> AsyncCacheService:
    """
    Get or create the global cache service instance.

    Args:
        redis_url: Redis connection URL
        namespace: Cache namespace
        default_ttl: Default TTL in seconds

    Returns:
        AsyncCacheService instance
    """
    global _cache_service

    if _cache_service is None:
        _cache_service = AsyncCacheService(
            redis_url=redis_url,
            namespace=namespace,
            default_ttl=default_ttl
        )

    return _cache_service


def cache_async(
    ttl: Optional[int] = None,
    category: Optional[str] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator for caching async function results.

    Args:
        ttl: Time to live in seconds
        category: Cache category
        key_func: Optional custom key generation function

    Example:
        @cache_async(ttl=3600, category="seo")
        async def fetch_serp_data(keyword: str):
            # Expensive API call
            return await serp_api.search(keyword)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                if kwargs:
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            # Try cache first
            cached = await cache.get(cache_key, category=category)
            if cached is not None:
                return cached

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache.set(cache_key, result, ttl=ttl, category=category)

            return result

        return wrapper
    return decorator
