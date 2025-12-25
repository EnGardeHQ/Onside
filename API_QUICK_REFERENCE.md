# REST API Endpoints - Quick Reference Guide

## Authentication
All endpoints require JWT authentication via Bearer token:
```bash
Authorization: Bearer <your-jwt-token>
```

---

## Report Schedules API
**Base:** `/api/v1/report-schedules`

```bash
# Create schedule
POST /api/v1/report-schedules
{
  "company_id": 1,
  "name": "Weekly Report",
  "report_type": "content",
  "cron_expression": "0 9 * * 1",
  "parameters": {...},
  "email_recipients": ["user@example.com"]
}

# List schedules
GET /api/v1/report-schedules?company_id=1&is_active=true&page=1

# Get schedule
GET /api/v1/report-schedules/{id}

# Update schedule
PUT /api/v1/report-schedules/{id}

# Delete schedule
DELETE /api/v1/report-schedules/{id}

# Pause/Resume
POST /api/v1/report-schedules/{id}/pause
POST /api/v1/report-schedules/{id}/resume

# Get executions
GET /api/v1/report-schedules/{id}/executions
```

---

## Search History API
**Base:** `/api/v1/search-history`

```bash
# List history
GET /api/v1/search-history?days=30&search_type=content&page=1

# Get analytics
GET /api/v1/search-history/analytics?company_id=1&days=30

# Cleanup old searches
DELETE /api/v1/search-history/cleanup?days=90
```

---

## Web Scraping API
**Base:** `/api/v1/scraping`

```bash
# Initiate scrape
POST /api/v1/scraping/scrape
{
  "url": "https://example.com",
  "capture_screenshot": true,
  "timeout": 30000
}

# List scraped content
GET /api/v1/scraping/content?domain=example.com&page=1

# Get content details
GET /api/v1/scraping/content/{id}

# Get versions
GET /api/v1/scraping/content/{id}/versions

# Compare versions
GET /api/v1/scraping/content/{id}/diff?compare_to={old_id}

# Create scraping schedule
POST /api/v1/scraping/schedules
{
  "name": "Daily Scrape",
  "url": "https://example.com",
  "cron_expression": "0 2 * * *"
}

# List schedules
GET /api/v1/scraping/schedules?is_active=true

# Delete schedule
DELETE /api/v1/scraping/schedules/{id}
```

---

## Email Delivery API
**Base:** `/api/v1/email`

```bash
# Create recipient
POST /api/v1/email/recipients
{
  "company_id": 1,
  "email": "team@example.com",
  "name": "Marketing Team"
}

# List recipients
GET /api/v1/email/recipients?company_id=1

# Update recipient
PUT /api/v1/email/recipients/{id}

# Delete recipient
DELETE /api/v1/email/recipients/{id}

# List deliveries
GET /api/v1/email/deliveries?status_filter=failed&page=1

# Get delivery
GET /api/v1/email/deliveries/{id}

# Retry delivery
POST /api/v1/email/deliveries/{id}/retry

# Get metrics
GET /api/v1/email/deliveries/{id}/metrics
```

---

## Link Deduplication API
**Base:** `/api/v1/links`

```bash
# Detect duplicates
POST /api/v1/links/detect-duplicates
{
  "company_id": 1,
  "similarity_threshold": 0.85,
  "include_inactive": false
}

# Merge duplicates
POST /api/v1/links/merge
{
  "primary_link_id": 100,
  "duplicate_link_ids": [101, 102],
  "merge_metadata": true,
  "merge_tags": true
}

# Generate report
GET /api/v1/links/duplicates/report?company_id=1&similarity_threshold=0.85
```

---

## User Preferences API
**Base:** `/api/v1/users/me`

```bash
# Get language
GET /api/v1/users/me/language

# Set language
PUT /api/v1/users/me/language
{
  "language": "es"
}
```

---

## SEO Services API
**Base:** `/api/v1/seo`

### Google Custom Search

```bash
# Perform search
POST /api/v1/seo/google-search
{
  "query": "content marketing",
  "max_results": 20,
  "language": "en",
  "date_restrict": "m6"
}

# Track brand mentions
POST /api/v1/seo/brand-mentions
{
  "brand_name": "OnSide",
  "keywords": ["analytics"],
  "competitors": ["CompetitorA"],
  "max_results": 50
}

# Analyze content performance
POST /api/v1/seo/content-performance
{
  "url": "https://example.com/article",
  "competitors": ["https://competitor.com/article"],
  "metrics": ["ranking", "backlinks", "shares"]
}
```

### YouTube

```bash
# Search videos
POST /api/v1/seo/youtube/search
{
  "query": "tutorial",
  "max_results": 25,
  "order": "viewCount",
  "video_duration": "medium"
}

# Get channel stats
GET /api/v1/seo/youtube/channel/{channel_id}/stats

# Get video analytics
GET /api/v1/seo/youtube/video/{video_id}/analytics

# Track competitor videos
POST /api/v1/seo/youtube/competitor/{competitor_id}/videos
{
  "competitor_id": 5,
  "channel_id": "UCxxxxxx",
  "max_videos": 20
}
```

---

## Common Query Parameters

### Pagination
```bash
?page=1              # Page number (default: 1)
&page_size=20        # Items per page (default: 20, max: 100)
```

### Filtering
```bash
?company_id=1        # Filter by company
&is_active=true      # Filter by active status
&search_type=content # Filter by search type
&days=30             # Time range in days
```

---

## Response Format

### Success Response
```json
{
  "id": 1,
  "name": "Example",
  "created_at": "2025-12-23T10:00:00Z",
  "updated_at": "2025-12-23T10:00:00Z"
}
```

### List Response
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### Error Response
```json
{
  "detail": "Error message description"
}
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async operation) |
| 204 | No Content (successful deletion) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Environment Variables Required

```bash
# Google Custom Search
GOOGLE_SEARCH_API_KEY=your_api_key
GOOGLE_SEARCH_ENGINE_ID=your_engine_id

# YouTube
YOUTUBE_API_KEY=your_api_key

# Email (choose one)
SENDGRID_API_KEY=your_key
AWS_SES_ACCESS_KEY=your_key
SMTP_HOST=smtp.example.com
```

---

## Testing with cURL

```bash
# Login to get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Use token in requests
TOKEN="your-jwt-token"

curl -X GET http://localhost:8000/api/v1/report-schedules \
  -H "Authorization: Bearer $TOKEN"
```

---

## File Locations

### Schemas
- `/Users/cope/EnGardeHQ/Onside/src/schemas/report_schedule.py`
- `/Users/cope/EnGardeHQ/Onside/src/schemas/search_history.py`
- `/Users/cope/EnGardeHQ/Onside/src/schemas/web_scraping.py`
- `/Users/cope/EnGardeHQ/Onside/src/schemas/email_delivery.py`
- `/Users/cope/EnGardeHQ/Onside/src/schemas/link_deduplication.py`
- `/Users/cope/EnGardeHQ/Onside/src/schemas/seo_services.py`

### Routers
- `/Users/cope/EnGardeHQ/Onside/src/api/v1/report_schedules.py`
- `/Users/cope/EnGardeHQ/Onside/src/api/v1/search_history.py`
- `/Users/cope/EnGardeHQ/Onside/src/api/v1/scraping.py`
- `/Users/cope/EnGardeHQ/Onside/src/api/v1/email_delivery.py`
- `/Users/cope/EnGardeHQ/Onside/src/api/v1/link_deduplication.py`
- `/Users/cope/EnGardeHQ/Onside/src/api/v1/user_preferences.py`
- `/Users/cope/EnGardeHQ/Onside/src/api/v1/seo_services.py`

---

**Last Updated:** December 23, 2025
