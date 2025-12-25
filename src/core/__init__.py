"""
Core package for the OnSide application.

This package contains core functionality used throughout the application,
including caching, configuration, and other utilities.
"""

from .cache import Cache, cache, get_cache, cached

__all__ = [
    'Cache',
    'cache',
    'get_cache',
    'cached',
]
