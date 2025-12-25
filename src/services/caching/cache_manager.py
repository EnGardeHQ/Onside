"""
Enhanced Cache Manager for En Garde ↔ Onside Integration

Provides a comprehensive caching layer with:
- Redis connection management with connection pooling
- Consistent hashing for cache key generation
- TTL configuration for different data types
- Multiple cache invalidation strategies
- Cache warming for popular keywords
- Cache statistics and monitoring
- Graceful fallback to in-memory cache on Redis failure
"""
import logging
import json
import hashlib
import pickle
from typing import Any, Optional, Dict, List, Callable, Union
from datetime import datetime, timedelta
from functools import wraps
import asyncio

try:
    import redis.asyncio as aioredis
    from redis.asyncio import Redis, ConnectionPool
    from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None
    Redis = None
    ConnectionPool = None
    RedisError = Exception
    RedisConnectionError = Exception

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheManager:
    """
    Enhanced cache manager with Redis support and graceful fallbacks.

    Features:
    - Async Redis operations with connection pooling
    - Automatic serialization/deserialization
    - TTL-based expiration
    - Pattern-based invalidation
    - Cache warming strategies
    - Statistics tracking
    - Health monitoring
    - Graceful degradation
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        namespace: str = "onside",
        max_connections: int = 50,
        enable_fallback: bool = True
    ):
        """Initialize cache manager.

        Args:
            redis_url: Redis connection URL (default from settings)
            namespace: Cache key namespace for multi-tenancy
            max_connections: Maximum Redis connection pool size
            enable_fallback: Enable in-memory fallback on Redis failure
        """
        self.namespace = namespace
        self.enable_fallback = enable_fallback
        self.redis_client: Optional[Redis] = None
        self.connection_pool: Optional[ConnectionPool] = None
        self.fallback_cache: Dict[str, Any] = {}
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'fallback_ops': 0
        }

        # Initialize Redis if available
        if REDIS_AVAILABLE and settings.CACHE_ENABLED:
            redis_url = redis_url or settings.REDIS_URL
            self._initialize_redis(redis_url, max_connections)
        else:
            logger.warning("Redis not available or cache disabled, using in-memory fallback")

    def _initialize_redis(self, redis_url: str, max_connections: int):
        """Initialize Redis connection pool.

        Args:
            redis_url: Redis connection URL
            max_connections: Maximum pool connections
        """
        try:
            self.connection_pool = ConnectionPool.from_url(
                redis_url,
                max_connections=max_connections,
                decode_responses=False,  # Handle binary data
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            self.redis_client = Redis(connection_pool=self.connection_pool)
            logger.info(f"Redis cache initialized successfully: {redis_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.redis_client = None
            if not self.enable_fallback:
                raise

    def _generate_key(self, key: str, category: Optional[str] = None) -> str:
        """Generate namespaced cache key with consistent hashing.

        Args:
            key: Base cache key
            category: Optional category for organization

        Returns:
            Namespaced and hashed key
        """
        parts = [self.namespace]
        if category:
            parts.append(category)
        parts.append(key)

        full_key = ":".join(parts)

        # Use consistent hashing for very long keys
        if len(full_key) > 200:
            hash_key = hashlib.sha256(full_key.encode()).hexdigest()
            return f"{self.namespace}:{category or 'default'}:hash:{hash_key}"

        return full_key

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage.

        Args:
            value: Value to serialize

        Returns:
            Serialized bytes
        """
        try:
            # Try JSON first for better readability and debugging
            if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                return json.dumps(value).encode('utf-8')
            # Fall back to pickle for complex objects
            return pickle.dumps(value)
        except Exception as e:
            logger.warning(f"Serialization error, falling back to pickle: {e}")
            return pickle.dumps(value)

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize cached data.

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
            try:
                return pickle.loads(data)
            except Exception as e:
                logger.error(f"Deserialization error: {e}")
                return None

    async def get(
        self,
        key: str,
        category: Optional[str] = None,
        default: Any = None
    ) -> Any:
        """Get value from cache.

        Args:
            key: Cache key
            category: Optional category
            default: Default value if not found

        Returns:
            Cached value or default
        """
        cache_key = self._generate_key(key, category)

        try:
            if self.redis_client:
                data = await self.redis_client.get(cache_key)
                if data is not None:
                    self.stats['hits'] += 1
                    return self._deserialize(data)
                else:
                    self.stats['misses'] += 1
                    return default
            else:
                # Fallback to in-memory cache
                self.stats['fallback_ops'] += 1
                value = self.fallback_cache.get(cache_key)
                if value is not None:
                    # Check TTL in fallback
                    if isinstance(value, dict) and '__ttl__' in value:
                        if datetime.utcnow() > value['__ttl__']:
                            del self.fallback_cache[cache_key]
                            self.stats['misses'] += 1
                            return default
                        self.stats['hits'] += 1
                        return value['__value__']
                    self.stats['hits'] += 1
                    return value
                self.stats['misses'] += 1
                return default

        except (RedisError, RedisConnectionError) as e:
            logger.warning(f"Redis error in get operation: {e}")
            self.stats['errors'] += 1
            if self.enable_fallback:
                return self.fallback_cache.get(cache_key, default)
            return default
        except Exception as e:
            logger.error(f"Unexpected error in get operation: {e}")
            self.stats['errors'] += 1
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        category: Optional[str] = None
    ) -> bool:
        """Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = no expiration)
            category: Optional category

        Returns:
            True if successful, False otherwise
        """
        cache_key = self._generate_key(key, category)

        try:
            serialized = self._serialize(value)

            if self.redis_client:
                if ttl:
                    await self.redis_client.setex(cache_key, ttl, serialized)
                else:
                    await self.redis_client.set(cache_key, serialized)
                self.stats['sets'] += 1
                return True
            else:
                # Fallback to in-memory cache
                self.stats['fallback_ops'] += 1
                if ttl:
                    expiry = datetime.utcnow() + timedelta(seconds=ttl)
                    self.fallback_cache[cache_key] = {
                        '__value__': value,
                        '__ttl__': expiry
                    }
                else:
                    self.fallback_cache[cache_key] = value
                self.stats['sets'] += 1
                return True

        except (RedisError, RedisConnectionError) as e:
            logger.warning(f"Redis error in set operation: {e}")
            self.stats['errors'] += 1
            if self.enable_fallback:
                self.fallback_cache[cache_key] = value
                return True
            return False
        except Exception as e:
            logger.error(f"Unexpected error in set operation: {e}")
            self.stats['errors'] += 1
            return False

    async def delete(
        self,
        *keys: str,
        category: Optional[str] = None
    ) -> int:
        """Delete one or more keys from cache.

        Args:
            *keys: Keys to delete
            category: Optional category

        Returns:
            Number of keys deleted
        """
        cache_keys = [self._generate_key(key, category) for key in keys]

        try:
            if self.redis_client:
                count = await self.redis_client.delete(*cache_keys)
                self.stats['deletes'] += count
                return count
            else:
                # Fallback to in-memory cache
                self.stats['fallback_ops'] += 1
                count = 0
                for key in cache_keys:
                    if key in self.fallback_cache:
                        del self.fallback_cache[key]
                        count += 1
                self.stats['deletes'] += count
                return count

        except (RedisError, RedisConnectionError) as e:
            logger.warning(f"Redis error in delete operation: {e}")
            self.stats['errors'] += 1
            return 0
        except Exception as e:
            logger.error(f"Unexpected error in delete operation: {e}")
            self.stats['errors'] += 1
            return 0

    async def invalidate_pattern(
        self,
        pattern: str,
        category: Optional[str] = None
    ) -> int:
        """Invalidate all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "user:*" or "*keyword*")
            category: Optional category

        Returns:
            Number of keys invalidated
        """
        search_pattern = self._generate_key(pattern, category)

        try:
            if self.redis_client:
                # Use SCAN for better performance on large datasets
                count = 0
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(
                        cursor,
                        match=search_pattern,
                        count=100
                    )
                    if keys:
                        deleted = await self.redis_client.delete(*keys)
                        count += deleted
                    if cursor == 0:
                        break

                self.stats['deletes'] += count
                logger.info(f"Invalidated {count} keys matching pattern: {pattern}")
                return count
            else:
                # Fallback to in-memory cache
                self.stats['fallback_ops'] += 1
                pattern_prefix = search_pattern.replace('*', '')
                keys_to_delete = [
                    k for k in self.fallback_cache.keys()
                    if k.startswith(pattern_prefix)
                ]
                for key in keys_to_delete:
                    del self.fallback_cache[key]
                count = len(keys_to_delete)
                self.stats['deletes'] += count
                return count

        except (RedisError, RedisConnectionError) as e:
            logger.warning(f"Redis error in pattern invalidation: {e}")
            self.stats['errors'] += 1
            return 0
        except Exception as e:
            logger.error(f"Unexpected error in pattern invalidation: {e}")
            self.stats['errors'] += 1
            return 0

    # SERP-specific cache methods

    async def cache_serp_results(
        self,
        keyword: str,
        results: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache SERP results for a keyword.

        Args:
            keyword: Search keyword
            results: SERP results data
            ttl: TTL in seconds (default: 24 hours)

        Returns:
            True if successful
        """
        ttl = ttl or settings.CACHE_TTL_SERP_RESULTS  # Default 24 hours
        cache_key = hashlib.md5(f"serp:{keyword}".encode()).hexdigest()

        # Add metadata
        cached_data = {
            'keyword': keyword,
            'results': results,
            'cached_at': datetime.utcnow().isoformat(),
            'ttl': ttl
        }

        return await self.set(
            cache_key,
            cached_data,
            ttl=ttl,
            category="serp_results"
        )

    async def get_cached_serp_results(
        self,
        keyword: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached SERP results.

        Args:
            keyword: Search keyword

        Returns:
            Cached SERP data or None
        """
        cache_key = hashlib.md5(f"serp:{keyword}".encode()).hexdigest()

        cached_data = await self.get(cache_key, category="serp_results")

        if cached_data:
            logger.info(f"Cache hit for SERP keyword: {keyword}")
            return cached_data.get('results')

        logger.debug(f"Cache miss for SERP keyword: {keyword}")
        return None

    # Content scraping cache methods

    async def cache_scraped_content(
        self,
        url: str,
        content: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache scraped content from a URL.

        Args:
            url: Target URL
            content: Scraped content data
            ttl: TTL in seconds (default: 1 hour)

        Returns:
            True if successful
        """
        ttl = ttl or settings.CACHE_TTL_WEBSITE_CRAWL  # Default 1 hour
        cache_key = hashlib.md5(f"scraped:{url}".encode()).hexdigest()

        # Add metadata
        cached_data = {
            'url': url,
            'content': content,
            'cached_at': datetime.utcnow().isoformat(),
            'ttl': ttl
        }

        return await self.set(
            cache_key,
            cached_data,
            ttl=ttl,
            category="scraped_content"
        )

    async def get_cached_content(
        self,
        url: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached scraped content.

        Args:
            url: Target URL

        Returns:
            Cached content or None
        """
        cache_key = hashlib.md5(f"scraped:{url}".encode()).hexdigest()

        cached_data = await self.get(cache_key, category="scraped_content")

        if cached_data:
            logger.info(f"Cache hit for scraped URL: {url}")
            return cached_data.get('content')

        logger.debug(f"Cache miss for scraped URL: {url}")
        return None

    # Analysis results cache methods

    async def cache_analysis_results(
        self,
        job_id: str,
        results: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache analysis job results.

        Args:
            job_id: Analysis job ID
            results: Analysis results
            ttl: TTL in seconds (default: 7 days)

        Returns:
            True if successful
        """
        ttl = ttl or settings.CACHE_TTL_KEYWORD_DATA  # Default 7 days

        # Add metadata
        cached_data = {
            'job_id': job_id,
            'results': results,
            'cached_at': datetime.utcnow().isoformat(),
            'ttl': ttl
        }

        return await self.set(
            job_id,
            cached_data,
            ttl=ttl,
            category="analysis_results"
        )

    async def get_cached_analysis(
        self,
        job_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached analysis results.

        Args:
            job_id: Analysis job ID

        Returns:
            Cached analysis results or None
        """
        cached_data = await self.get(job_id, category="analysis_results")

        if cached_data:
            logger.info(f"Cache hit for analysis job: {job_id}")
            return cached_data.get('results')

        logger.debug(f"Cache miss for analysis job: {job_id}")
        return None

    # Cache warming methods

    async def warm_cache_for_keywords(
        self,
        keywords: List[str],
        fetch_fn: Callable[[str], Any],
        ttl: Optional[int] = None
    ) -> Dict[str, bool]:
        """Warm cache with SERP data for popular keywords.

        Args:
            keywords: List of keywords to warm
            fetch_fn: Async function to fetch SERP data
            ttl: TTL for cached data

        Returns:
            Dictionary mapping keyword to success status
        """
        logger.info(f"Warming cache for {len(keywords)} keywords")
        results = {}

        for keyword in keywords:
            try:
                # Check if already cached
                cached = await self.get_cached_serp_results(keyword)
                if cached:
                    results[keyword] = True
                    continue

                # Fetch and cache
                data = await fetch_fn(keyword)
                if data:
                    success = await self.cache_serp_results(keyword, data, ttl)
                    results[keyword] = success
                else:
                    results[keyword] = False

            except Exception as e:
                logger.error(f"Error warming cache for keyword '{keyword}': {e}")
                results[keyword] = False

        success_count = sum(1 for v in results.values() if v)
        logger.info(f"Cache warming complete: {success_count}/{len(keywords)} successful")

        return results

    # Statistics and monitoring

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics including hit/miss ratios and memory usage.

        Returns:
            Dictionary with cache statistics
        """
        total_ops = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_ops * 100) if total_ops > 0 else 0.0

        stats = {
            'backend': 'redis' if self.redis_client else 'memory',
            'namespace': self.namespace,
            'statistics': {
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'sets': self.stats['sets'],
                'deletes': self.stats['deletes'],
                'errors': self.stats['errors'],
                'fallback_ops': self.stats['fallback_ops'],
                'total_operations': total_ops,
                'hit_rate_percent': round(hit_rate, 2)
            },
            'timestamp': datetime.utcnow().isoformat()
        }

        # Add Redis-specific stats
        if self.redis_client:
            try:
                info = await self.redis_client.info('memory')
                stats['redis_memory'] = {
                    'used_memory': info.get('used_memory_human'),
                    'used_memory_peak': info.get('used_memory_peak_human'),
                    'used_memory_rss': info.get('used_memory_rss_human'),
                    'mem_fragmentation_ratio': info.get('mem_fragmentation_ratio')
                }

                # Get key count
                db_size = await self.redis_client.dbsize()
                stats['redis_keys'] = {
                    'total': db_size,
                    'namespace_pattern': f"{self.namespace}:*"
                }
            except Exception as e:
                logger.warning(f"Error fetching Redis stats: {e}")
        else:
            stats['fallback_cache_size'] = len(self.fallback_cache)

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check.

        Returns:
            Dictionary with health status
        """
        health = {
            'healthy': False,
            'backend': 'redis' if self.redis_client else 'memory',
            'timestamp': datetime.utcnow().isoformat()
        }

        try:
            # Test write
            test_key = '__health_check__'
            test_value = {'timestamp': datetime.utcnow().isoformat()}
            write_ok = await self.set(test_key, test_value, ttl=60, category='health')

            # Test read
            read_value = await self.get(test_key, category='health')
            read_ok = read_value is not None

            # Clean up
            await self.delete(test_key, category='health')

            health['healthy'] = write_ok and read_ok
            health['write_success'] = write_ok
            health['read_success'] = read_ok

            # Redis ping
            if self.redis_client:
                try:
                    ping_ok = await self.redis_client.ping()
                    health['redis_ping'] = ping_ok
                except Exception as e:
                    health['redis_ping'] = False
                    health['redis_error'] = str(e)

        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            health['error'] = str(e)

        return health

    async def close(self):
        """Close Redis connections gracefully."""
        if self.redis_client:
            try:
                await self.redis_client.close()
                if self.connection_pool:
                    await self.connection_pool.disconnect()
                logger.info("Redis connections closed successfully")
            except Exception as e:
                logger.error(f"Error closing Redis connections: {e}")


# Singleton instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create the global cache manager instance.

    Returns:
        CacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


async def init_cache_manager() -> CacheManager:
    """Initialize and return cache manager (for async startup).

    Returns:
        Initialized CacheManager instance
    """
    manager = get_cache_manager()
    # Perform health check on startup
    health = await manager.health_check()
    if health['healthy']:
        logger.info("Cache manager initialized and healthy")
    else:
        logger.warning(f"Cache manager initialized but not fully healthy: {health}")
    return manager
