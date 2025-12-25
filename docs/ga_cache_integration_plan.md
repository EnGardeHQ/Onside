# Google Analytics Cache Integration Plan

**Date:** May 22, 2025  
**Owner:** Development Team  
**Status:** Draft

## 1. Overview

This document outlines the strategy for implementing caching in the Google Analytics client to improve performance and reduce API calls to Google's services.

## 2. Goals

1. Reduce Google Analytics API calls by implementing intelligent caching
2. Improve response times for frequently accessed data
3. Maintain data freshness with appropriate TTLs
4. Implement cache invalidation strategies
5. Maintain data consistency and reliability

## 3. Technical Approach

### 3.1 Cache Storage

- **Cache Provider**: Use the existing `CacheService` from `src/services/caching/cache_service.py`
- **Storage**: In-memory cache with optional persistence
- **Scope**: Application-level caching (shared across requests)

### 3.2 Cache Key Strategy

Cache keys will be generated using the following pattern:
```
ga:{user_id}:{method_name}:{md5_hash_of_arguments}
```

Example:
```
ga:123:get_site_metrics:a1b2c3d4e5f6...
```

### 3.3 Caching Strategy

| Method | Cache TTL | Notes |
|--------|-----------|-------|
| `get_site_metrics` | 5 minutes | High-frequency access, moderate data volatility |
| `get_page_views` | 15 minutes | Medium-frequency access, lower data volatility |
| `get_traffic_sources` | 15 minutes | Medium-frequency access, lower data volatility |
| `get_top_pages` | 15 minutes | Medium-frequency access, lower data volatility |

## 4. Implementation Plan

### 4.1 Phase 1: Core Caching Implementation

1. **Update GoogleAnalyticsClient**
   - Import cache utilities
   - Add cache key generation helper
   - Implement `@cache_async` decorator on methods

2. **Cache Key Generation**
   - Create `_generate_cache_key` helper method
   - Handle argument serialization for consistent keys

3. **TTL Configuration**
   - Define TTL constants
   - Make TTLs configurable via environment variables

### 4.2 Phase 2: Cache Invalidation

1. **Manual Invalidation**
   - Add `invalidate_cache` method to clear specific entries
   - Support pattern-based invalidation (e.g., by user_id)

2. **Automatic Invalidation**
   - Invalidate cache on data modification operations
   - Implement TTL-based expiration

### 4.3 Phase 3: Monitoring and Metrics

1. **Cache Statistics**
   - Track hit/miss rates
   - Monitor cache size and memory usage
   - Log cache performance metrics

2. **Health Checks**
   - Add cache health check endpoint
   - Monitor cache hit rates and response times

## 5. Code Changes

### 5.1 GoogleAnalyticsClient Updates

```python
# In src/services/google_analytics/client.py
from src.services.caching import cache_async
import hashlib
import json

class GoogleAnalyticsClient:
    # Default TTLs in seconds
    CACHE_TTL = {
        'get_site_metrics': 300,      # 5 minutes
        'get_page_views': 900,        # 15 minutes
        'get_traffic_sources': 900,   # 15 minutes
        'get_top_pages': 900,         # 15 minutes
    }
    
    def _generate_cache_key(self, method_name: str, **kwargs) -> str:
        """Generate a consistent cache key for method calls."""
        key_parts = [f"ga:{self.user_id}:{method_name}"]
        
        # Sort kwargs for consistent ordering
        for k, v in sorted(kwargs.items()):
            # Convert values to string and handle special cases
            if isinstance(v, (list, dict)):
                v = json.dumps(v, sort_keys=True)
            key_parts.append(f"{k}:{v}")
            
        # Create MD5 hash of the key parts
        key_str = "|".join(str(part) for part in key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    @cache_async(ttl=CACHE_TTL['get_site_metrics'])
    async def get_site_metrics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        cache_key = self._generate_cache_key(
            'get_site_metrics',
            start_date=start_date,
            end_date=end_date
        )
        # Rest of the method...
```

### 5.2 Cache Invalidation

```python
async def invalidate_cache(self, pattern: str = None) -> int:
    """
    Invalidate cache entries matching the given pattern.
    
    Args:
        pattern: Cache key pattern to match (e.g., 'ga:123:*')
        
    Returns:
        Number of cache entries invalidated
    """
    if not pattern:
        pattern = f"ga:{self.user_id}:*"
        
    return await cache_service.delete_matching(pattern)
```

## 6. Testing Strategy

### 6.1 Unit Tests

1. **Cache Key Generation**
   - Test different argument combinations
   - Verify consistent hashing

2. **Cache Behavior**
   - Verify cache hit/miss scenarios
   - Test TTL expiration
   - Verify cache invalidation

### 6.2 Integration Tests

1. **API Endpoints**
   - Verify cached responses
   - Test cache invalidation endpoints
   - Monitor API response times

2. **Load Testing**
   - Measure performance with and without cache
   - Test cache under concurrent access

## 7. Rollout Plan

1. **Development**
   - Implement and test in feature branch
   - Code review and approval

2. **Staging**
   - Deploy to staging environment
   - Monitor cache performance
   - Verify data consistency

3. **Production**
   - Gradual rollout (feature flag)
   - Monitor error rates and performance
   - Full deployment after validation

## 8. Rollback Plan

1. Disable caching via feature flag
2. Clear all cache entries
3. Verify normal operation without cache

## 9. Monitoring and Alerting

1. **Key Metrics**
   - Cache hit/miss ratio
   - Average response time
   - Memory usage
   - Error rates

2. **Alerts**
   - Cache miss rate > 80%
   - Memory usage > 80% of limit
   - Error rate > 1%

## 10. Future Enhancements

1. **Distributed Caching**
   - Redis or Memcached integration
   - Support for multi-instance deployments

2. **Advanced Invalidation**
   - Event-based invalidation
   - Partial cache updates

3. **Adaptive TTL**
   - Dynamic TTL based on data volatility
   - Machine learning for optimal TTL prediction

---
*Document Status: Draft | Last Updated: 2025-05-22*
