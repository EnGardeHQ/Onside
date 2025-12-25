"""
Cache Service for OnSide
Following Semantic Seed BDD/TDD Coding Standards V2.0

This module provides caching capabilities to improve performance
by storing frequently accessed data in memory.
"""

import time
import logging
import asyncio
import functools
from typing import Dict, Any, Optional, Callable, TypeVar, Union, Awaitable, Generic, cast
from datetime import datetime, timedelta
import json
import os
import pickle
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for function decorators
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])
AFT = TypeVar('AFT', bound=Callable[..., Awaitable[Any]])

class CacheItem(Generic[T]):
    """Generic class for cache items with expiration."""
    
    def __init__(self, value: T, ttl_seconds: int):
        """Initialize a cache item with a value and TTL."""
        self.value = value
        self.expiration = time.time() + ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if the cache item has expired."""
        return time.time() > self.expiration


class CacheService:
    """
    Cache service for storing frequently accessed data.
    
    Features:
    - In-memory caching with configurable TTL
    - Function/method result caching
    - Async operation result caching
    - Cache statistics tracking
    - Cache persistence (optional)
    """
    
    def __init__(self, default_ttl: int = 300, persistence_dir: str = "exports/cache"):
        """Initialize the cache service with a default TTL in seconds."""
        self.cache: Dict[str, CacheItem[Any]] = {}
        self.default_ttl = default_ttl
        self.persistence_dir = persistence_dir
        self.hits = 0
        self.misses = 0
        
        # Create persistence directory if it doesn't exist
        os.makedirs(persistence_dir, exist_ok=True)
        
        logger.info(f"Cache service initialized with default TTL of {default_ttl} seconds")
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache by key."""
        if key not in self.cache:
            self.misses += 1
            return None
        
        item = self.cache[key]
        if item.is_expired():
            self.delete(key)
            self.misses += 1
            return None
        
        self.hits += 1
        return item.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the cache with optional TTL override."""
        ttl_seconds = ttl if ttl is not None else self.default_ttl
        self.cache[key] = CacheItem(value, ttl_seconds)
    
    def delete(self, key: str) -> None:
        """Delete a value from the cache by key."""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """Clear all items from the cache."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache),
            "active_keys": list(self.cache.keys())
        }
    
    def cache_function(self, ttl: Optional[int] = None) -> Callable[[F], F]:
        """Decorator to cache the results of a function."""
        def decorator(func: F) -> F:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Create a cache key from the function name and arguments
                key_parts = [func.__name__]
                for arg in args:
                    key_parts.append(str(arg))
                for k, v in sorted(kwargs.items()):
                    key_parts.append(f"{k}:{v}")
                
                cache_key = ":".join(key_parts)
                
                # Check cache first
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Call the function if not cached
                result = func(*args, **kwargs)
                
                # Cache the result
                self.set(cache_key, result, ttl)
                
                return result
            
            return cast(F, wrapper)
        return decorator
    
    def cache_async_function(self, ttl: Optional[int] = None) -> Callable[[AFT], AFT]:
        """Decorator to cache the results of an async function."""
        def decorator(func: AFT) -> AFT:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Create a cache key from the function name and arguments
                key_parts = [func.__name__]
                for arg in args:
                    key_parts.append(str(arg))
                for k, v in sorted(kwargs.items()):
                    key_parts.append(f"{k}:{v}")
                
                cache_key = ":".join(key_parts)
                
                # Check cache first
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Call the function if not cached
                result = await func(*args, **kwargs)
                
                # Cache the result
                self.set(cache_key, result, ttl)
                
                return result
            
            return cast(AFT, wrapper)
        return decorator
    
    def save_to_disk(self) -> str:
        """Save the current cache to disk and return the file path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.persistence_dir, f"cache_{timestamp}.pickle")
        
        with open(filepath, 'wb') as f:
            pickle.dump(self.cache, f)
        
        logger.info(f"Cache saved to {filepath}")
        return filepath
    
    def load_from_disk(self, filepath: str) -> None:
        """Load cache from a disk file."""
        if not os.path.exists(filepath):
            logger.warning(f"Cache file not found: {filepath}")
            return
        
        try:
            with open(filepath, 'rb') as f:
                loaded_cache = pickle.load(f)
                
                # Only use non-expired items
                for key, item in loaded_cache.items():
                    if not item.is_expired():
                        self.cache[key] = item
                
                logger.info(f"Cache loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading cache from {filepath}: {str(e)}")


# Create a global instance for easy import
cache_service = CacheService()

# Convenience decorators
def cache(ttl: Optional[int] = None) -> Callable[[F], F]:
    """Decorator to cache function results using the global cache service."""
    return cache_service.cache_function(ttl)

def cache_async(ttl: Optional[int] = None) -> Callable[[AFT], AFT]:
    """Decorator to cache async function results using the global cache service."""
    return cache_service.cache_async_function(ttl)
