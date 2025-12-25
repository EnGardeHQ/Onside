# Caching & Infrastructure Quick Reference

## Quick Start

### 1. Start Services

```bash
cd /Users/cope/EnGardeHQ/Onside
docker-compose up -d
```

### 2. Verify Redis

```bash
# Check Redis is running
docker exec onside-redis redis-cli ping
# Should return: PONG

# Check Redis info
docker exec onside-redis redis-cli INFO memory
```

### 3. Test Cache

```bash
# Cache health check
curl http://localhost:8000/health/cache

# Cache statistics
curl http://localhost:8000/api/v1/metrics/cache
```

---

## Cache Manager Usage

### Basic Operations

```python
from src.services.caching.cache_manager import get_cache_manager

# Get cache manager instance
cache = get_cache_manager()

# Set a value (expires in 1 hour)
await cache.set("my_key", {"data": "value"}, ttl=3600, category="my_category")

# Get a value
data = await cache.get("my_key", category="my_category")

# Delete a value
await cache.delete("my_key", category="my_category")

# Delete by pattern
await cache.invalidate_pattern("user:*", category="sessions")
```

### SERP Caching

```python
# Cache SERP results (24h default)
await cache.cache_serp_results(
    keyword="cloud computing",
    results={"ranking": [...], "volume": 12000}
)

# Get cached SERP results
results = await cache.get_cached_serp_results("cloud computing")
```

### Content Caching

```python
# Cache scraped content (1h default)
await cache.cache_scraped_content(
    url="https://example.com",
    content={"title": "...", "text": "..."}
)

# Get cached content
content = await cache.get_cached_content("https://example.com")
```

### Cache Statistics

```python
# Get comprehensive stats
stats = await cache.get_cache_stats()
print(f"Hit rate: {stats['statistics']['hit_rate_percent']}%")
print(f"Total keys: {stats['redis_keys']['total']}")
```

---

## Performance Monitoring

### Add to FastAPI App

```python
from fastapi import FastAPI
from src.middleware.performance_monitor import PerformanceMonitorMiddleware

app = FastAPI()

# Add middleware
performance_monitor = PerformanceMonitorMiddleware(
    app,
    slow_threshold=1.0,  # Log requests > 1s
    enable_memory_tracking=True
)
app.add_middleware(PerformanceMonitorMiddleware)
```

### Get Performance Stats

```python
from src.middleware.performance_monitor import get_performance_monitor

monitor = get_performance_monitor()
stats = monitor.get_stats()

# Check slow requests
slow = stats['slow_requests']
for req in slow:
    print(f"{req['method']} {req['endpoint']}: {req['duration']:.2f}s")
```

### Response Headers

Every response includes:
- `X-Process-Time`: Request duration in seconds
- `X-Memory-Usage`: Memory usage in MB

---

## Rate Limiting

### Add to FastAPI App

```python
from fastapi import FastAPI
from src.middleware.rate_limiter import RateLimiterMiddleware
import redis.asyncio as aioredis

app = FastAPI()
redis_client = await aioredis.from_url("redis://localhost:6379/0")

# Add middleware
rate_limiter = RateLimiterMiddleware(
    app,
    redis_client=redis_client,
    enable_rate_limiting=True
)
app.add_middleware(RateLimiterMiddleware)
```

### Default Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Brand Analysis | 5/hour | per user |
| SERP Analysis | 20/hour | per user |
| Report Generation | 10/hour | per user |
| Other Endpoints | 100/minute | per IP |

### Customize Limits

```python
# Add custom limit
rate_limiter.add_endpoint_limit(
    path="/api/v1/custom",
    requests=50,
    window=3600,  # 1 hour
    scope="user"
)

# Remove limit
rate_limiter.remove_endpoint_limit("/api/v1/custom")
```

### Rate Limit Headers

Every response includes:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets
- `X-RateLimit-Window`: Time window in seconds

### 429 Response

```json
{
    "error": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Maximum 5 requests per 3600 seconds.",
    "retry_after": 2847,
    "limit": 5,
    "window": 3600
}
```

---

## Environment Variables

### Cache Configuration

```bash
CACHE_ENABLED=true
CACHE_TTL_SERP_RESULTS=86400      # 24 hours
CACHE_TTL_WEBSITE_CRAWL=3600      # 1 hour
CACHE_TTL_KEYWORD_DATA=604800     # 7 days
CACHE_TTL_SCRAPED_CONTENT=3600    # 1 hour
```

### Performance Monitoring

```bash
ENABLE_PERFORMANCE_MONITORING=true
SLOW_REQUEST_THRESHOLD=1.0
ENABLE_MEMORY_TRACKING=true
LOG_SLOW_REQUESTS=true
```

### Rate Limiting

```bash
ENABLE_RATE_LIMITING=true
DEFAULT_RATE_LIMIT_REQUESTS=100
DEFAULT_RATE_LIMIT_WINDOW=60
BRAND_ANALYSIS_RATE_LIMIT=5
BRAND_ANALYSIS_RATE_WINDOW=3600
```

---

## Monitoring Endpoints

### Cache Metrics

```bash
curl http://localhost:8000/api/v1/metrics/cache
```

Response:
```json
{
    "backend": "redis",
    "statistics": {
        "hits": 1500,
        "misses": 300,
        "hit_rate_percent": 83.33
    },
    "redis_memory": {
        "used_memory": "45.2M"
    }
}
```

### Performance Metrics

```bash
curl http://localhost:8000/api/v1/metrics/performance
```

Response:
```json
{
    "endpoints": [
        {
            "endpoint": "/api/v1/brand-analysis/initiate",
            "avg_duration": 2.34,
            "p95_duration": 4.23,
            "error_rate": 3.33
        }
    ],
    "slow_requests": [...],
    "system": {...}
}
```

### Rate Limit Stats

```bash
curl http://localhost:8000/api/v1/metrics/rate-limiting
```

Response:
```json
{
    "enabled": true,
    "backend": "redis",
    "endpoint_limits": {
        "/api/v1/brand-analysis/initiate": {
            "requests": 5,
            "window": 3600
        }
    }
}
```

---

## Common Commands

### Redis CLI

```bash
# Enter Redis CLI
docker exec -it onside-redis redis-cli

# Get all keys
KEYS onside:*

# Get cache stats
INFO stats

# Get memory usage
INFO memory

# Monitor commands in real-time
MONITOR

# Get key value
GET onside:serp_results:abc123

# Delete key
DEL onside:serp_results:abc123

# Delete by pattern
EVAL "return redis.call('del', unpack(redis.call('keys', ARGV[1])))" 0 onside:serp_results:*

# Check TTL
TTL onside:serp_results:abc123
```

### Docker Commands

```bash
# View Redis logs
docker logs onside-redis

# Restart Redis
docker restart onside-redis

# Check Redis resource usage
docker stats onside-redis

# Backup Redis data
docker exec onside-redis redis-cli SAVE

# Flush all cache (DANGER!)
docker exec onside-redis redis-cli FLUSHALL
```

---

## Troubleshooting

### Cache Not Working

```bash
# 1. Check Redis is running
docker ps | grep redis

# 2. Check Redis health
docker exec onside-redis redis-cli ping

# 3. Check app logs
docker logs onside-api | grep -i cache

# 4. Verify environment variable
docker exec onside-api env | grep CACHE_ENABLED
```

### High Memory Usage

```bash
# 1. Check current memory
docker exec onside-redis redis-cli INFO memory

# 2. Check number of keys
docker exec onside-redis redis-cli DBSIZE

# 3. Reduce maxmemory in docker-compose.yml
# 4. Restart Redis
docker restart onside-redis
```

### Rate Limiting Issues

```bash
# 1. Check rate limiter stats
curl http://localhost:8000/api/v1/metrics/rate-limiting

# 2. Check Redis for rate limit keys
docker exec onside-redis redis-cli KEYS "ratelimit:*"

# 3. Clear rate limits (if needed)
docker exec onside-redis redis-cli EVAL "return redis.call('del', unpack(redis.call('keys', ARGV[1])))" 0 "ratelimit:*"
```

### Slow Requests

```bash
# 1. Check slow requests
curl http://localhost:8000/api/v1/metrics/performance | jq '.slow_requests'

# 2. Check database slow queries
# (if query profiling enabled)

# 3. Enable Redis slow log
docker exec onside-redis redis-cli CONFIG SET slowlog-log-slower-than 1000

# 4. View slow log
docker exec onside-redis redis-cli SLOWLOG GET 10
```

---

## Performance Tips

### Cache Warming

```python
# Warm cache for popular keywords
popular_keywords = ["cloud", "SaaS", "enterprise"]

async def fetch_serp(keyword):
    # Fetch from API
    return await serp_api.search(keyword)

results = await cache.warm_cache_for_keywords(
    keywords=popular_keywords,
    fetch_fn=fetch_serp,
    ttl=86400
)
```

### Optimal TTL Values

| Data Type | Recommended TTL | Reasoning |
|-----------|----------------|-----------|
| SERP Results | 24 hours | Search rankings change slowly |
| Website Content | 1 hour | Content updates periodically |
| Analysis Results | 7 days | Historical data, rarely changes |
| API Responses | 5 minutes | Balance freshness vs. caching |
| User Sessions | 1 hour | Security vs. convenience |

### Cache Invalidation

```python
# Invalidate on data update
async def update_brand_analysis(job_id: str, data: dict):
    # Update database
    await db.update(...)

    # Invalidate cache
    await cache.delete(job_id, category="analysis_results")
    await cache.invalidate_pattern(f"brand:{job_id}:*")
```

---

## File Locations

| Component | File Path |
|-----------|-----------|
| Cache Manager | `/Users/cope/EnGardeHQ/Onside/src/services/caching/cache_manager.py` |
| Performance Monitor | `/Users/cope/EnGardeHQ/Onside/src/middleware/performance_monitor.py` |
| Rate Limiter | `/Users/cope/EnGardeHQ/Onside/src/middleware/rate_limiter.py` |
| Environment Config | `/Users/cope/EnGardeHQ/Onside/.env.example` |
| Docker Compose | `/Users/cope/EnGardeHQ/Onside/docker-compose.yml` |
| Redis Config | `/Users/cope/EnGardeHQ/Onside/redis/redis.conf` |
| Full Documentation | `/Users/cope/EnGardeHQ/Onside/CACHING_INFRASTRUCTURE_IMPLEMENTATION.md` |

---

## Support & Resources

- **Full Documentation:** `CACHING_INFRASTRUCTURE_IMPLEMENTATION.md`
- **Redis Documentation:** https://redis.io/documentation
- **FastAPI Middleware:** https://fastapi.tiangolo.com/advanced/middleware/
- **Grafana Dashboards:** https://grafana.com/grafana/dashboards/

---

**Version:** 1.0
**Last Updated:** December 24, 2025
