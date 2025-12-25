# OnSide API Reference

## Base URL
- Development: `http://localhost:8000`
- Production: `https://api.onside.com`

## Authentication
All authenticated endpoints require Bearer token:
```
Authorization: Bearer <token>
```

## API Versioning
All endpoints are versioned under `/api/v1/`

---

## Core Endpoints

### Health Check
```
GET /health
```
Returns service health status.

### Authentication
```
POST /api/v1/auth/login
POST /api/v1/auth/register
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

---

## Competitor Intelligence

### GNews API (`/api/v1/gnews/`)
```
GET  /api/v1/gnews/search
     Query params: query, max_results, language

GET  /api/v1/gnews/competitor/{competitor_id}
     Query params: days_back (default: 7)

GET  /api/v1/gnews/headlines
     Query params: category, country

POST /api/v1/gnews/analyze-sentiment
     Body: { "articles": [...] }

GET  /api/v1/gnews/usage
     Returns API quota status
```

### Competitor News (`/api/v1/competitors/`)
```
GET  /api/v1/competitors/{id}/news
     Query params: days_back, limit

GET  /api/v1/competitors/{id}/news/sentiment
     Returns sentiment analysis

GET  /api/v1/competitors/{id}/news/trends
     Returns news volume trends

POST /api/v1/competitors/{id}/news/refresh
     Refreshes news data from API

GET  /api/v1/competitors/news/compare
     Query params: competitor_ids, days_back
```

### IPInfo API (`/api/v1/ipinfo/`)
```
GET  /api/v1/ipinfo/{ip_address}
     Returns IP geolocation data

POST /api/v1/ipinfo/batch
     Body: { "ip_addresses": [...] }

GET  /api/v1/ipinfo/domain/{domain_id}/geo
     Returns geographic distribution

GET  /api/v1/ipinfo/competitor/{competitor_id}/regions
     Returns regional presence analysis

GET  /api/v1/ipinfo/status
     Returns rate limit status
```

### WhoAPI (`/api/v1/whoapi/`)
```
GET  /api/v1/whoapi/whois/{domain}
     Returns WHOIS data

GET  /api/v1/whoapi/ssl/{domain}
     Returns SSL certificate info

GET  /api/v1/whoapi/dns/{domain}
     Returns DNS records

GET  /api/v1/whoapi/tech/{domain}
     Returns tech stack analysis

GET  /api/v1/whoapi/age/{domain}
     Returns domain age

GET  /api/v1/whoapi/availability/{domain}
     Returns availability check

GET  /api/v1/whoapi/expiring
     Query params: days (default: 30)
```

---

## SEO Services

### SEO Analysis (`/api/v1/seo/`)
```
GET  /api/v1/seo/analyze/{domain}
POST /api/v1/seo/score
GET  /api/v1/seo/trends/{domain}
```

### Google Analytics (`/api/v1/google-analytics/`)
```
GET  /api/v1/google-analytics/auth/url
GET  /api/v1/google-analytics/auth/callback
GET  /api/v1/google-analytics/properties
GET  /api/v1/google-analytics/metrics
```

---

## Reports

### Report Generation (`/api/v1/reports/`)
```
POST /api/v1/reports/generate
     Body: { "type": "...", "parameters": {...} }

GET  /api/v1/reports/{report_id}
GET  /api/v1/reports/{report_id}/status
GET  /api/v1/reports/{report_id}/download
GET  /api/v1/reports/list
```

### Report Types
- `CONTENT_ANALYSIS`
- `SENTIMENT_ANALYSIS`
- `COMPETITOR_INTELLIGENCE`
- `MARKET_ANALYSIS`
- `AUDIENCE_INSIGHTS`
- `SEO_ANALYSIS`

---

## Data Ingestion

### Data Import (`/api/v1/data-ingestion/`)
```
POST /api/v1/data-ingestion/import
POST /api/v1/data-ingestion/batch
GET  /api/v1/data-ingestion/status/{job_id}
```

---

## Error Responses

### Standard Error Format
```json
{
    "detail": "Error message",
    "error_code": "ERROR_CODE",
    "timestamp": "2025-12-22T00:00:00Z"
}
```

### HTTP Status Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |

---

## Rate Limiting

### Limits by Endpoint Type
| Endpoint Type | Limit |
|---------------|-------|
| Authentication | 10/minute |
| Read operations | 100/minute |
| Write operations | 30/minute |
| External API calls | Varies by API |

### Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

---

## External API Quotas

### Daily Limits (Free Tier)
| API | Daily Limit |
|-----|-------------|
| GNews | 1000 requests |
| IPInfo | 1000 requests |
| WhoAPI | 500 requests |

### Quota Tracking
Use `/api/v1/{service}/usage` to check remaining quota.

---

## Pagination

### Request
```
GET /api/v1/resource?page=1&per_page=20
```

### Response
```json
{
    "items": [...],
    "total": 100,
    "page": 1,
    "per_page": 20,
    "pages": 5
}
```

---

## WebSocket Endpoints

### Progress Tracking
```
WS /ws/progress/{task_id}
```
Real-time updates for long-running operations.

---

## SDK Examples

### Python
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/v1/gnews/search",
        params={"query": "competitor", "max_results": 10},
        headers={"Authorization": f"Bearer {token}"}
    )
    data = response.json()
```

### cURL
```bash
curl -X GET "http://localhost:8000/api/v1/gnews/search?query=competitor" \
     -H "Authorization: Bearer $TOKEN"
```
