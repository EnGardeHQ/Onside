"""
Cache Module

This module provides caching functionality for the application using Redis or an in-memory cache.
"""
import logging
from typing import Any, Optional, Union, Callable, TypeVar, cast
from functools import wraps
import json
import pickle
from datetime import datetime, timedelta
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variable for generic function typing
F = TypeVar('F', bound=Callable[..., Any])


class Cache:
    """A simple cache implementation that can use different backends."""
    
    _instance = None
    _client = None
    _backend = 'memory'  # Default to in-memory cache
    _prefix = 'onside_'
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(Cache, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, backend: str = 'memory', **kwargs):
        """Initialize the cache with the specified backend.
        
        Args:
            backend: The cache backend to use ('memory' or 'redis')
            **kwargs: Additional backend-specific configuration
        """
        if not hasattr(self, '_initialized'):
            self._backend = backend
            self._prefix = kwargs.get('prefix', 'onside_')
            self._initialized = True
            
            if backend == 'redis':
                self._init_redis(**kwargs)
            else:
                self._init_memory()
    
    def _init_redis(self, **kwargs):
        """Initialize Redis client."""
        try:
            import redis
            self._client = redis.Redis(
                host=kwargs.get('host', 'localhost'),
                port=kwargs.get('port', 6379),
                db=kwargs.get('db', 0),
                password=kwargs.get('password'),
                decode_responses=kwargs.get('decode_responses', False),
                **kwargs
            )
            # Test connection
            self._client.ping()
            self._backend = 'redis'
            logger.info("Redis cache initialized successfully")
        except ImportError:
            logger.warning("Redis not installed, falling back to in-memory cache")
            self._init_memory()
        except Exception as e:
            logger.error("Failed to initialize Redis cache: %s", e)
            logger.warning("Falling back to in-memory cache")
            self._init_memory()
    
    def _init_memory(self):
        """Initialize in-memory cache."""
        self._client = {}
        self._backend = 'memory'
        logger.info("In-memory cache initialized")
    
    def _make_key(self, key: str) -> str:
        """Create a namespaced cache key.
        
        Args:
            key: The base key to namespace
            
        Returns:
            Namespaced cache key
        """
        return f"{self._prefix}{key}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve an item from the cache.
        
        Args:
            key: The cache key
            default: Default value if key is not found
            
        Returns:
            The cached value or default if not found
        """
        cache_key = self._make_key(key)
        
        try:
            if self._backend == 'redis':
                value = self._client.get(cache_key)
                if value is None:
                    return default
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return pickle.loads(value) if value else default
            else:
                if cache_key not in self._client:
                    return default
                
                # Check if the item has expired
                item = self._client[cache_key]
                if item['expires'] is not None and item['expires'] < datetime.utcnow():
                    del self._client[cache_key]
                    return default
                    
                return item['value']
        except Exception as e:
            logger.error("Error getting value from cache: %s", e)
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Store an item in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds or as timedelta. If None, the item will not expire.
            
        Returns:
            True if successful, False otherwise
            
        Examples:
            >>> cache = Cache()
            >>> cache.set('key', 'value')  # No expiration
            True
            >>> cache.set('key2', 'value2', ttl=300)  # 5 minutes
            True
            >>> from datetime import timedelta
            >>> cache.set('key3', 'value3', ttl=timedelta(hours=1))  # 1 hour
            True
        """
        if not key:
            logger.warning("Empty key provided to cache.set()")
            return False
            
        cache_key = self._make_key(key)
        
        try:
            if self._backend == 'redis':
                try:
                    serialized = json.dumps(value)
                    serialization_method = 'json'
                except (TypeError, OverflowError, ValueError) as e:
                    logger.debug("JSON serialization failed, falling back to pickle: %s", e)
                    try:
                        serialized = pickle.dumps(value)
                        serialization_method = 'pickle'
                    except (pickle.PicklingError, TypeError) as e:
                        logger.error("Failed to serialize value for caching: %s", e)
                        return False
                
                try:
                    if ttl is not None:
                        if isinstance(ttl, timedelta):
                            ttl = int(ttl.total_seconds())
                        if ttl <= 0:
                            logger.warning("TTL must be positive, got: %s", ttl)
                            return False
                        return bool(self._client.setex(cache_key, ttl, serialized))
                    return bool(self._client.set(cache_key, serialized))
                except Exception as e:
                    logger.error("Redis error in cache.set(): %s", e)
                    return False
            else:
                # In-memory cache
                expires = None
                if ttl is not None:
                    if isinstance(ttl, timedelta):
                        expires = datetime.utcnow() + ttl
                    else:
                        expires = datetime.utcnow() + timedelta(seconds=ttl)
                
                self._client[cache_key] = {
                    'value': value,
                    'expires': expires
                }
                return True
        except Exception as e:
            logger.error("Error setting value in cache: %s", e)
            return False
    
    def delete(self, *keys: str) -> int:
        """Delete one or more keys from the cache.
        
        Args:
            *keys: One or more keys to delete
            
        Returns:
            Number of keys successfully deleted
            
        Examples:
            >>> cache = Cache()
            >>> cache.set('key1', 'value1')
            True
            >>> cache.set('key2', 'value2')
            True
            >>> cache.delete('key1', 'key2', 'nonexistent')
            2
        """
        if not keys:
            return 0
            
        # Filter out None or empty keys
        valid_keys = [str(key) for key in keys if key]
        if not valid_keys:
            return 0
            
        cache_keys = [self._make_key(key) for key in valid_keys]
        
        try:
            if self._backend == 'redis':
                try:
                    return self._client.delete(*cache_keys)
                except TypeError:
                    # Handle case where no keys were provided after filtering
                    return 0
            else:
                deleted = 0
                for key in cache_keys:
                    try:
                        if key in self._client:
                            del self._client[key]
                            deleted += 1
                    except KeyError:
                        # Key might have been deleted by another operation
                        continue
                return deleted
        except Exception as e:
            logger.error("Error deleting keys from cache: %s", e)
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache and has not expired.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists and has not expired, False otherwise
            
        Examples:
            >>> cache = Cache()
            >>> cache.set('key1', 'value1', ttl=60)
            True
            >>> cache.exists('key1')
            True
            >>> cache.exists('nonexistent')
            False
        """
        if not key:
            return False
            
        cache_key = self._make_key(key)
        
        try:
            if self._backend == 'redis':
                # Redis handles TTL internally, so we can just check existence
                return bool(self._client.exists(cache_key))
            else:
                # For in-memory cache, check both existence and expiration
                if cache_key not in self._client:
                    return False
                    
                item = self._client[cache_key]
                if item['expires'] is not None and item['expires'] < datetime.utcnow():
                    # Clean up expired item
                    try:
                        del self._client[cache_key]
                    except KeyError:
                        pass  # Already deleted by another operation
                    return False
                return True
        except Exception as e:
            logger.error("Error checking if key exists in cache: %s", e)
            return False
    
    def clear(self, pattern: Optional[str] = None) -> bool:
        """Clear keys from the cache.
        
        Args:
            pattern: Optional pattern to match keys against. If None, all keys will be cleared.
                    Only supported with Redis backend. For in-memory cache, this will clear all keys.
                    
        Returns:
            True if operation was successful, False otherwise
            
        Warning:
            Be extremely careful with this method in production, especially when not providing a pattern,
            as it will remove all cached data.
            
        Examples:
            >>> cache = Cache()
            >>> cache.set('user:1', 'John')
            True
            >>> cache.set('config:app', {...})
            True
            >>> cache.clear(pattern='user:*')  # Only clear user-related keys
            True
            >>> cache.clear()  # Clear all keys (use with caution!)
            True
        """
        try:
            if self._backend == 'redis':
                if pattern:
                    # Delete keys matching pattern
                    keys = self._client.keys(self._make_key(pattern))
                    if keys:
                        return bool(self._client.delete(*keys) > 0)
                    return True
                else:
                    # Clear entire database
                    return self._client.flushdb()
            else:
                # In-memory cache - clear everything
                # Note: We don't support pattern matching for in-memory cache
                # as it would be inefficient for large caches
                self._client.clear()
                return True
        except Exception as e:
            logger.error("Error clearing cache: %s", e)
            return False
    
    def get_or_set(self, key: str, default: Any, ttl: Optional[Union[int, timedelta]] = None) -> Any:
        """Get a value from the cache, or set it if it doesn't exist.
        
        This is an atomic operation that first tries to get the value for the given key.
        If the key doesn't exist, it sets the key to the default value and returns it.
        
        Args:
            key: The cache key
            default: Default value to set if key doesn't exist. Can be a callable.
            ttl: Time to live in seconds or as timedelta for the default value
            
        Returns:
            The cached value if it exists, otherwise the default value
            
        Examples:
            >>> cache = Cache()
            
            # With a direct value
            >>> cache.get_or_set('username', 'guest', ttl=300)
            'guest'
            
            # With a callable that generates the default value
            >>> import time
            >>> cache.get_or_set('last_updated', time.time)
            1621456789.123456
            
            # With a lambda
            >>> cache.get_or_set('config', lambda: {'debug': True, 'version': '1.0'})
            {'debug': True, 'version': '1.0'}
        """
        if not key:
            raise ValueError("Key cannot be empty")
            
        # First try to get the value
        value = self.get(key)
        if value is not None:
            return value
        
        # If we get here, the key doesn't exist or is expired
        try:
            # Handle callable default
            if callable(default):
                default_value = default()
            else:
                default_value = default
                
            # Set the value in cache
            if not self.set(key, default_value, ttl):
                logger.warning("Failed to set value in cache for key: %s", key)
                
            return default_value
            
        except Exception as e:
            logger.error("Error in get_or_set for key %s: %s", key, e)
            if callable(default):
                # If we can't set the value, at least return the default
                try:
                    return default()
                except Exception as inner_e:
                    logger.error("Error calling default callable: %s", inner_e)
                    raise
            return default
    
    def memoize(  # noqa: C901
        self,
        ttl: Optional[Union[int, timedelta]] = None,
        key_func: Optional[Callable[..., str]] = None,
    ) -> Callable:
        """Decorator to cache function results.
        
        This decorator caches the return value of a function based on its arguments.
        It works with both synchronous and asynchronous functions.
        
        Args:
            ttl: Time to live in seconds or as timedelta for the cached result
            key_func: Optional function to generate custom cache keys. If not provided,
                    a default key will be generated based on the function's module,
                    name, and arguments.
                    
        Returns:
            A decorator that can be applied to functions to cache their results
            
        Examples:
            # Basic usage
            @cache.memoize(ttl=300)  # Cache for 5 minutes
            def expensive_operation(x, y):
                return x * y
                
            # With custom key function
            def custom_key(x, y):
                return f"custom_key_{x}_{y}"
                
            @cache.memoize(ttl=3600, key_func=custom_key)
            def another_operation(x, y):
                return x + y
                
            # With async function
            @cache.memoize(ttl=60)
            async def fetch_data(url):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        return await response.json()
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Generate cache key
                try:
                    if key_func is not None:
                        cache_key = key_func(*args, **kwargs)
                    else:
                        # Default key generation
                        key_parts = [func.__module__, func.__name__]
                        key_parts.extend(str(arg) for arg in args)
                        
                        # Sort kwargs for consistent key generation
                        if kwargs:
                            key_parts.extend(
                                f"{k}={v}" for k, v in sorted(kwargs.items())
                            )
                            
                        cache_key = ":".join(key_parts)
                    
                    # Try to get from cache
                    cached = self.get(cache_key)
                    if cached is not None:
                        logger.debug("Cache hit for key: %s", cache_key)
                        return cached
                    
                    logger.debug("Cache miss for key: %s", cache_key)
                    result = func(*args, **kwargs)
                    
                    # Handle coroutines
                    if asyncio.iscoroutine(result):
                        async def async_wrapper() -> Any:
                            try:
                                result_value = await result
                                self.set(cache_key, result_value, ttl)
                                return result_value
                            except Exception as e:
                                logger.error(
                                    "Error in memoized async function: %s", e
                                )
                                raise
                        return async_wrapper()
                    
                    # Handle regular functions
                    self.set(cache_key, result, ttl)
                    return result
                    
                except Exception as e:
                    logger.error("Error in memoize wrapper: %s", e)
                    # If there's an error with caching, still try to run the function
                    return func(*args, **kwargs)
            
            return wrapper
        return decorator


# Create a default cache instance
cache = Cache()

# For backward compatibility
def get_cache() -> Cache:
    """Get the default cache instance."""
    return cache


def cached(ttl: Optional[Union[int, timedelta]] = None, key: Optional[str] = None):
    """Decorator to cache function results with a time-to-live.
    
    Args:
        ttl: Time to live in seconds or as timedelta
        key: Optional custom cache key
        
    Returns:
        Decorated function with caching
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = key or f"{func.__module__}:{func.__name__}:{args}:{frozenset(kwargs.items())}"
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
