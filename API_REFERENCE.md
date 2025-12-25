# Capilytics API Reference

**Version:** 1.0.0
**Base URL:** `http://localhost:8000/api/v1`
**Authentication:** Bearer Token (JWT)

## Table of Contents

1. [Authentication](#authentication)
2. [Report Schedules](#report-schedules)
3. [Search History](#search-history)
4. [Web Scraping](#web-scraping)
5. [Email Delivery](#email-delivery)
6. [Link Deduplication](#link-deduplication)
7. [User Preferences](#user-preferences)
8. [SEO Services](#seo-services)
9. [Competitors](#competitors)
10. [Domains](#domains)
11. [GNews Integration](#gnews-integration)
12. [IPInfo Integration](#ipinfo-integration)
13. [WhoAPI Integration](#whoapi-integration)
14. [Error Handling](#error-handling)
15. [Rate Limiting](#rate-limiting)

---

## Authentication

### Register User

Create a new user account.

**Endpoint:** `POST /api/v1/auth/register`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "USER"
}
```

**Error Responses:**
- `400 Bad Request` - Email already registered

---

### Login

Authenticate and receive an access token.

**Endpoint:** `POST /api/v1/auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "USER"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Incorrect email or password

---

### Logout

Logout the current user (client-side token invalidation).

**Endpoint:** `POST /api/v1/auth/logout`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "message": "Successfully logged out"
}
```

---

### Get User Profile

Retrieve user profile information.

**Endpoint:** `GET /api/v1/auth/users/{user_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "user@example.com",
  "role": "USER",
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Error Responses:**
- `403 Forbidden` - Not authorized to view this profile
- `404 Not Found` - User not found

---

## Report Schedules

Manage automated report schedules with CRON expressions.

### Create Report Schedule

**Endpoint:** `POST /api/v1/report-schedules`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "company_id": 1,
  "name": "Weekly Competitor Report",
  "description": "Automated weekly analysis of competitor activities",
  "report_type": "competitor_analysis",
  "cron_expression": "0 9 * * MON",
  "parameters": {
    "competitors": [1, 2, 3],
    "metrics": ["traffic", "engagement", "seo"]
  },
  "email_recipients": ["manager@company.com", "team@company.com"],
  "notify_on_completion": true
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "user_id": 1,
  "company_id": 1,
  "name": "Weekly Competitor Report",
  "description": "Automated weekly analysis of competitor activities",
  "report_type": "competitor_analysis",
  "cron_expression": "0 9 * * MON",
  "parameters": {
    "competitors": [1, 2, 3],
    "metrics": ["traffic", "engagement", "seo"]
  },
  "email_recipients": ["manager@company.com", "team@company.com"],
  "notify_on_completion": true,
  "is_active": true,
  "next_run_at": "2025-01-20T09:00:00Z",
  "last_run_at": null,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid cron expression
- `500 Internal Server Error` - Failed to create schedule

---

### List Report Schedules

**Endpoint:** `GET /api/v1/report-schedules`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `company_id` (optional): Filter by company ID
- `report_type` (optional): Filter by report type
- `is_active` (optional): Filter by active status (true/false)
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 20, max: 100): Items per page

**Example:** `GET /api/v1/report-schedules?company_id=1&is_active=true&page=1&page_size=20`

**Response:** `200 OK`
```json
{
  "schedules": [
    {
      "id": 1,
      "user_id": 1,
      "company_id": 1,
      "name": "Weekly Competitor Report",
      "report_type": "competitor_analysis",
      "cron_expression": "0 9 * * MON",
      "is_active": true,
      "next_run_at": "2025-01-20T09:00:00Z",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

---

### Get Report Schedule

**Endpoint:** `GET /api/v1/report-schedules/{schedule_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": 1,
  "company_id": 1,
  "name": "Weekly Competitor Report",
  "description": "Automated weekly analysis of competitor activities",
  "report_type": "competitor_analysis",
  "cron_expression": "0 9 * * MON",
  "parameters": {
    "competitors": [1, 2, 3],
    "metrics": ["traffic", "engagement", "seo"]
  },
  "email_recipients": ["manager@company.com"],
  "is_active": true,
  "next_run_at": "2025-01-20T09:00:00Z",
  "last_run_at": "2025-01-13T09:00:00Z",
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Report schedule not found

---

### Update Report Schedule

**Endpoint:** `PUT /api/v1/report-schedules/{schedule_id}`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "name": "Updated Weekly Report",
  "cron_expression": "0 10 * * MON",
  "is_active": true
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Updated Weekly Report",
  "cron_expression": "0 10 * * MON",
  "is_active": true,
  "updated_at": "2025-01-15T11:00:00Z"
}
```

---

### Delete Report Schedule

**Endpoint:** `DELETE /api/v1/report-schedules/{schedule_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `204 No Content`

---

### Pause Report Schedule

**Endpoint:** `POST /api/v1/report-schedules/{schedule_id}/pause`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "is_active": false,
  "updated_at": "2025-01-15T11:00:00Z"
}
```

---

### Resume Report Schedule

**Endpoint:** `POST /api/v1/report-schedules/{schedule_id}/resume`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "is_active": true,
  "next_run_at": "2025-01-20T09:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

---

### Get Schedule Executions

Retrieve execution history for a schedule.

**Endpoint:** `GET /api/v1/report-schedules/{schedule_id}/executions`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 20, max: 100): Items per page

**Response:** `200 OK`
```json
{
  "executions": [
    {
      "id": 1,
      "schedule_id": 1,
      "status": "completed",
      "started_at": "2025-01-13T09:00:00Z",
      "completed_at": "2025-01-13T09:05:30Z",
      "execution_time_seconds": 330,
      "error_message": null,
      "report_id": 123
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

---

### Get Schedule Statistics

**Endpoint:** `GET /api/v1/report-schedules/{schedule_id}/stats`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "total_executions": 52,
  "successful_executions": 50,
  "failed_executions": 2,
  "success_rate": 96.15,
  "avg_execution_time_seconds": 285.4,
  "last_execution_status": "completed",
  "last_execution_at": "2025-01-13T09:00:00Z"
}
```

---

## Search History

Track and analyze search history with analytics.

### List Search History

**Endpoint:** `GET /api/v1/search-history`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `company_id` (optional): Filter by company ID
- `search_type` (optional): Filter by search type (e.g., "google", "youtube")
- `days` (optional, default: 30, max: 365): Number of days to retrieve
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 20, max: 100): Items per page

**Example:** `GET /api/v1/search-history?days=7&page=1&page_size=20`

**Response:** `200 OK`
```json
{
  "searches": [
    {
      "id": 1,
      "user_id": 1,
      "company_id": 1,
      "query": "competitor analysis tools",
      "search_type": "google",
      "results_count": 150,
      "execution_time_ms": 342,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

---

### Get Search Analytics

**Endpoint:** `GET /api/v1/search-history/analytics`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `company_id` (optional): Filter by company ID
- `days` (optional, default: 30, max: 365): Number of days to analyze

**Response:** `200 OK`
```json
{
  "total_searches": 1250,
  "unique_queries": 450,
  "avg_execution_time_ms": 285.4,
  "top_queries": [
    {
      "query": "competitor analysis",
      "count": 45
    },
    {
      "query": "seo metrics",
      "count": 38
    }
  ],
  "search_types_distribution": {
    "google": 800,
    "youtube": 300,
    "gnews": 150
  },
  "searches_by_hour": {
    "9": 120,
    "10": 150,
    "14": 180
  },
  "searches_by_day": {
    "2025-01-15": 85,
    "2025-01-14": 92
  },
  "avg_results_count": 125.5
}
```

---

### Cleanup Old Searches

Delete search history older than specified days.

**Endpoint:** `DELETE /api/v1/search-history/cleanup`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `days` (optional, default: 90, min: 30, max: 365): Delete searches older than this many days

**Response:** `200 OK`
```json
{
  "deleted_count": 350,
  "message": "Successfully deleted 350 search records older than 90 days"
}
```

---

## Web Scraping

Manage web scraping operations with content versioning and change tracking.

### Initiate Scraping

**Endpoint:** `POST /api/v1/scraping/scrape`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "url": "https://example.com/page",
  "company_id": 1,
  "competitor_id": 2,
  "capture_screenshot": true,
  "wait_for_selector": "#main-content",
  "timeout": 30000
}
```

**Response:** `202 Accepted`
```json
{
  "message": "Scraping initiated",
  "url": "https://example.com/page",
  "status": "processing"
}
```

**Note:** Scraping happens asynchronously in the background.

---

### List Scraped Content

**Endpoint:** `GET /api/v1/scraping/content`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `company_id` (optional): Filter by company ID
- `competitor_id` (optional): Filter by competitor ID
- `domain` (optional): Filter by domain
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 20, max: 100): Items per page

**Response:** `200 OK`
```json
{
  "content": [
    {
      "id": 1,
      "url": "https://example.com/page",
      "domain": "example.com",
      "title": "Example Page Title",
      "company_id": 1,
      "competitor_id": 2,
      "version": 3,
      "content_hash": "a1b2c3d4e5f6...",
      "screenshot_url": "/screenshots/example-com-123.png",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

---

### Get Scraped Content Detail

Retrieve full content including HTML and text.

**Endpoint:** `GET /api/v1/scraping/content/{content_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "url": "https://example.com/page",
  "domain": "example.com",
  "title": "Example Page Title",
  "text_content": "Full extracted text content...",
  "html_content": "<!DOCTYPE html>...",
  "meta_description": "Page meta description",
  "meta_keywords": ["keyword1", "keyword2"],
  "version": 3,
  "content_hash": "a1b2c3d4e5f6...",
  "screenshot_url": "/screenshots/example-com-123.png",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### Get Content Versions

Retrieve version history for scraped content.

**Endpoint:** `GET /api/v1/scraping/content/{content_id}/versions`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
[
  {
    "id": 3,
    "version": 3,
    "content_hash": "a1b2c3d4e5f6...",
    "created_at": "2025-01-15T10:30:00Z",
    "has_changes": true
  },
  {
    "id": 2,
    "version": 2,
    "content_hash": "f6e5d4c3b2a1...",
    "created_at": "2025-01-10T10:30:00Z",
    "has_changes": true
  },
  {
    "id": 1,
    "version": 1,
    "content_hash": "123456789abc...",
    "created_at": "2025-01-05T10:30:00Z",
    "has_changes": false
  }
]
```

---

### Compare Content Versions

**Endpoint:** `GET /api/v1/scraping/content/{content_id}/diff`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `compare_to` (required): Version ID to compare to

**Example:** `GET /api/v1/scraping/content/3/diff?compare_to=2`

**Response:** `200 OK`
```json
{
  "url": "https://example.com/page",
  "old_version": 2,
  "new_version": 3,
  "has_changed": true,
  "change_percentage": 15.5,
  "diff_summary": {
    "added_lines": 45,
    "removed_lines": 12,
    "modified_lines": 8
  },
  "diff_data": {
    "text_diff": "Detailed diff information...",
    "html_diff": "HTML diff information..."
  }
}
```

---

### Create Scraping Schedule

**Endpoint:** `POST /api/v1/scraping/schedules`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "name": "Daily Homepage Scrape",
  "url": "https://competitor.com",
  "company_id": 1,
  "competitor_id": 2,
  "cron_expression": "0 8 * * *",
  "capture_screenshot": true,
  "scraping_config": {
    "wait_for_selector": "#content",
    "timeout": 30000
  }
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "name": "Daily Homepage Scrape",
  "url": "https://competitor.com",
  "company_id": 1,
  "competitor_id": 2,
  "cron_expression": "0 8 * * *",
  "capture_screenshot": true,
  "scraping_config": {
    "wait_for_selector": "#content",
    "timeout": 30000
  },
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### List Scraping Schedules

**Endpoint:** `GET /api/v1/scraping/schedules`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `company_id` (optional): Filter by company ID
- `is_active` (optional): Filter by active status
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 20, max: 100): Items per page

**Response:** `200 OK`
```json
{
  "schedules": [
    {
      "id": 1,
      "name": "Daily Homepage Scrape",
      "url": "https://competitor.com",
      "is_active": true,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

---

### Delete Scraping Schedule

**Endpoint:** `DELETE /api/v1/scraping/schedules/{schedule_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `204 No Content`

---

## Email Delivery

Manage email recipients and track email delivery status.

### Create Email Recipient

**Endpoint:** `POST /api/v1/email/recipients`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "company_id": 1,
  "email": "manager@company.com",
  "name": "Marketing Manager"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "company_id": 1,
  "email": "manager@company.com",
  "name": "Marketing Manager",
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Email recipient already exists for this company

---

### List Email Recipients

**Endpoint:** `GET /api/v1/email/recipients`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `company_id` (optional): Filter by company ID
- `is_active` (optional): Filter by active status
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 20, max: 100): Items per page

**Response:** `200 OK`
```json
{
  "recipients": [
    {
      "id": 1,
      "company_id": 1,
      "email": "manager@company.com",
      "name": "Marketing Manager",
      "is_active": true,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

---

### Update Email Recipient

**Endpoint:** `PUT /api/v1/email/recipients/{recipient_id}`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "name": "Updated Name",
  "is_active": true
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Updated Name",
  "is_active": true,
  "updated_at": "2025-01-15T11:00:00Z"
}
```

---

### Delete Email Recipient

**Endpoint:** `DELETE /api/v1/email/recipients/{recipient_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `204 No Content`

---

### List Email Deliveries

**Endpoint:** `GET /api/v1/email/deliveries`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `status_filter` (optional): Filter by status (queued, sending, sent, failed, bounced)
- `report_id` (optional): Filter by report ID
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 20, max: 100): Items per page

**Response:** `200 OK`
```json
{
  "deliveries": [
    {
      "id": 1,
      "recipient_email": "manager@company.com",
      "subject": "Weekly Competitor Report",
      "status": "sent",
      "report_id": 123,
      "sent_at": "2025-01-15T10:30:00Z",
      "retry_count": 0,
      "created_at": "2025-01-15T10:28:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

---

### Get Email Delivery

**Endpoint:** `GET /api/v1/email/deliveries/{delivery_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "recipient_email": "manager@company.com",
  "subject": "Weekly Competitor Report",
  "status": "sent",
  "report_id": 123,
  "sent_at": "2025-01-15T10:30:00Z",
  "opened_at": "2025-01-15T11:00:00Z",
  "clicked_at": "2025-01-15T11:05:00Z",
  "error_message": null,
  "retry_count": 0,
  "created_at": "2025-01-15T10:28:00Z"
}
```

---

### Retry Failed Delivery

**Endpoint:** `POST /api/v1/email/deliveries/{delivery_id}/retry`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "message": "Email delivery queued for retry",
  "delivery_id": 1,
  "new_retry_count": 1,
  "status": "queued"
}
```

**Error Responses:**
- `400 Bad Request` - Delivery cannot be retried (max retries exceeded or not in failed status)

---

### Get Delivery Metrics

**Endpoint:** `GET /api/v1/email/deliveries/{delivery_id}/metrics`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "delivery_id": 1,
  "status": "sent",
  "time_to_send_seconds": 2.5,
  "time_to_open_seconds": 1800,
  "time_to_click_seconds": 2100,
  "was_opened": true,
  "was_clicked": true,
  "bounce_type": null
}
```

---

## Link Deduplication

Detect and merge duplicate links using URL normalization and similarity matching.

### Detect Duplicate Links

**Endpoint:** `POST /api/v1/links/detect-duplicates`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "company_id": 1,
  "similarity_threshold": 0.85,
  "include_inactive": false
}
```

**Response:** `200 OK`
```json
{
  "total_links_analyzed": 500,
  "duplicate_groups_found": 15,
  "duplicate_groups": [
    {
      "normalized_url": "https://example.com/page",
      "similarity_score": 1.0,
      "link_ids": [1, 45, 89],
      "urls": [
        "https://example.com/page",
        "https://example.com/page?utm_source=email",
        "https://www.example.com/page/"
      ],
      "titles": [
        "Example Page",
        "Example Page",
        "Example Page - Home"
      ]
    }
  ]
}
```

---

### Merge Duplicate Links

**Endpoint:** `POST /api/v1/links/merge`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "primary_link_id": 1,
  "duplicate_link_ids": [45, 89],
  "merge_metadata": true,
  "merge_tags": true
}
```

**Response:** `200 OK`
```json
{
  "message": "Successfully merged 2 duplicate links",
  "primary_link_id": 1,
  "merged_count": 2,
  "deleted_link_ids": [45, 89]
}
```

**Error Responses:**
- `404 Not Found` - Primary link or duplicate links not found

---

### Generate Duplicate Report

**Endpoint:** `GET /api/v1/links/duplicates/report`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `company_id` (optional): Filter by company ID
- `similarity_threshold` (optional, default: 0.85): Similarity threshold for detection

**Response:** `200 OK`
```json
{
  "generated_at": "2025-01-15T10:30:00Z",
  "total_links": 500,
  "unique_links": 450,
  "duplicate_links": 50,
  "duplication_rate": 10.0,
  "duplicate_groups": [
    {
      "normalized_url": "https://example.com/page",
      "similarity_score": 1.0,
      "link_ids": [1, 45, 89],
      "urls": ["https://example.com/page", "..."],
      "titles": ["Example Page", "..."]
    }
  ],
  "recommendations": [
    "Low duplication rate. Link management is healthy."
  ]
}
```

---

## User Preferences

Manage user preferences including language settings.

### Get User Language Preference

**Endpoint:** `GET /api/v1/users/me/language`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "language": "en",
  "user_id": 1
}
```

---

### Set User Language Preference

**Endpoint:** `PUT /api/v1/users/me/language`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "language": "es"
}
```

**Supported language codes:** `en`, `es`, `fr`, `de`, `it`, `pt`, etc. (2-5 characters)

**Response:** `200 OK`
```json
{
  "language": "es",
  "user_id": 1
}
```

---

## SEO Services

Google Custom Search and YouTube Data API integration for SEO analysis.

### Google Custom Search

**Endpoint:** `POST /api/v1/seo/google-search`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "query": "competitive intelligence tools",
  "max_results": 10,
  "language": "en",
  "date_restrict": "d7",
  "site_search": null,
  "exclude_site": null
}
```

**Response:** `200 OK`
```json
{
  "query": "competitive intelligence tools",
  "total_results": 15000,
  "search_time": 0.45,
  "results": [
    {
      "title": "Top 10 Competitive Intelligence Tools",
      "link": "https://example.com/article",
      "snippet": "Comprehensive guide to competitive intelligence...",
      "displayLink": "example.com",
      "formattedUrl": "https://example.com/article"
    }
  ],
  "next_page_token": "CAoQABgA"
}
```

---

### Track Brand Mentions

**Endpoint:** `POST /api/v1/seo/brand-mentions`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "brand_name": "Capilytics",
  "keywords": ["analytics", "competitive intelligence"],
  "competitors": ["CompetitorA", "CompetitorB"],
  "date_restrict": "m1",
  "max_results": 50
}
```

**Response:** `200 OK`
```json
{
  "brand_name": "Capilytics",
  "mentions_found": 127,
  "sentiment_distribution": {
    "positive": 85,
    "neutral": 30,
    "negative": 12
  },
  "top_sources": [
    {
      "domain": "techcrunch.com",
      "mentions": 15
    }
  ],
  "competitor_comparison": {
    "CompetitorA": 95,
    "CompetitorB": 110
  },
  "trending_topics": [
    "AI-powered analytics",
    "real-time monitoring"
  ]
}
```

---

### Analyze Content Performance

**Endpoint:** `POST /api/v1/seo/content-performance`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "url": "https://mycompany.com/blog/article",
  "competitors": ["https://competitor1.com", "https://competitor2.com"],
  "metrics": ["ranking", "backlinks", "social_shares"]
}
```

**Response:** `200 OK`
```json
{
  "url": "https://mycompany.com/blog/article",
  "ranking_position": 3,
  "indexed_pages": 1,
  "backlink_estimate": 45,
  "social_shares": 230,
  "competitor_comparison": {
    "https://competitor1.com": {
      "ranking_position": 1,
      "backlinks": 120
    }
  },
  "recommendations": [
    "Increase backlinks to improve ranking",
    "Optimize meta description for better CTR"
  ]
}
```

---

### YouTube Video Search

**Endpoint:** `POST /api/v1/seo/youtube/search`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "query": "competitive analysis tutorial",
  "max_results": 10,
  "order": "relevance",
  "published_after": "2025-01-01T00:00:00Z",
  "video_duration": "medium",
  "video_type": "video"
}
```

**Response:** `200 OK`
```json
{
  "query": "competitive analysis tutorial",
  "total_results": 5000,
  "videos": [
    {
      "video_id": "abc123xyz",
      "title": "Complete Competitive Analysis Guide",
      "description": "Learn how to perform competitive analysis...",
      "channel_title": "Business Academy",
      "published_at": "2025-01-10T10:00:00Z",
      "thumbnail_url": "https://i.ytimg.com/vi/abc123xyz/default.jpg"
    }
  ],
  "next_page_token": "CAoQAA"
}
```

---

### Get YouTube Channel Statistics

**Endpoint:** `GET /api/v1/seo/youtube/channel/{channel_id}/stats`

**Headers:** `Authorization: Bearer {token}`

**Path Parameters:**
- `channel_id`: YouTube channel ID

**Response:** `200 OK`
```json
{
  "channel_id": "UCabc123xyz",
  "title": "Business Academy",
  "description": "Educational content for entrepreneurs...",
  "subscriber_count": 250000,
  "video_count": 450,
  "view_count": 15000000,
  "avg_views_per_video": 33333.33,
  "upload_frequency": "3 videos per week",
  "top_videos": [
    {
      "video_id": "top1",
      "title": "Most Popular Video",
      "view_count": 500000
    }
  ]
}
```

---

### Get YouTube Video Analytics

**Endpoint:** `GET /api/v1/seo/youtube/video/{video_id}/analytics`

**Headers:** `Authorization: Bearer {token}`

**Path Parameters:**
- `video_id`: YouTube video ID

**Response:** `200 OK`
```json
{
  "video_id": "abc123xyz",
  "title": "Complete Competitive Analysis Guide",
  "channel_title": "Business Academy",
  "published_at": "2025-01-10T10:00:00Z",
  "view_count": 50000,
  "like_count": 2500,
  "dislike_count": 50,
  "comment_count": 350,
  "favorite_count": 0,
  "duration": "PT15M30S",
  "tags": ["competitive analysis", "business", "strategy"],
  "category_id": "22",
  "engagement_rate": 5.7,
  "likes_to_views_ratio": 0.05,
  "comments_to_views_ratio": 0.007
}
```

---

### Track Competitor Videos

**Endpoint:** `POST /api/v1/seo/youtube/competitor/{competitor_id}/videos`

**Headers:** `Authorization: Bearer {token}`

**Path Parameters:**
- `competitor_id`: Competitor ID

**Request Body:**
```json
{
  "channel_id": "UCcompetitor123",
  "max_videos": 20,
  "published_after": "2025-01-01T00:00:00Z"
}
```

**Response:** `200 OK`
```json
{
  "competitor_id": 1,
  "channel_id": "UCcompetitor123",
  "channel_title": "Competitor Channel",
  "videos_analyzed": 20,
  "total_views": 500000,
  "total_likes": 25000,
  "total_comments": 3500,
  "avg_engagement_rate": 5.7,
  "top_performing_videos": [
    {
      "video_id": "video1",
      "title": "Top Video",
      "view_count": 100000,
      "engagement_rate": 8.5
    }
  ],
  "upload_frequency": "2 videos per week",
  "trending_topics": [
    "AI integration",
    "automation"
  ]
}
```

---

## Competitors

Manage competitor information.

### Create Competitor

**Endpoint:** `POST /api/v1/competitors`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "name": "Competitor Inc",
  "website": "https://competitor.com",
  "description": "Major competitor in analytics space",
  "industry": "Software"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "name": "Competitor Inc",
  "website": "https://competitor.com",
  "description": "Major competitor in analytics space",
  "industry": "Software",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### Get Competitor

**Endpoint:** `GET /api/v1/competitors/{competitor_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Competitor Inc",
  "website": "https://competitor.com",
  "description": "Major competitor in analytics space",
  "industry": "Software",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### List Competitors

**Endpoint:** `GET /api/v1/competitors`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `skip` (optional, default: 0): Number of records to skip
- `limit` (optional, default: 100): Maximum records to return

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Competitor Inc",
    "website": "https://competitor.com",
    "industry": "Software"
  }
]
```

---

### Update Competitor

**Endpoint:** `PUT /api/v1/competitors/{competitor_id}`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "name": "Updated Competitor Name",
  "description": "Updated description"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Updated Competitor Name",
  "description": "Updated description",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

---

### Delete Competitor

**Endpoint:** `DELETE /api/v1/competitors/{competitor_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `204 No Content`

---

## Error Handling

All API errors follow a consistent format:

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

**HTTP Status Codes:**
- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `202 Accepted` - Request accepted for processing
- `204 No Content` - Request succeeded with no content to return
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required or failed
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

**Example Error Response:**
```json
{
  "detail": "Invalid cron expression"
}
```

---

## Rate Limiting

API rate limiting is applied per user account:

- **Default Rate Limit:** 1000 requests per hour
- **Burst Limit:** 100 requests per minute

**Rate Limit Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1642339200
```

When rate limit is exceeded:

**Response:** `429 Too Many Requests`
```json
{
  "detail": "Rate limit exceeded. Please retry after 60 seconds."
}
```

---

## Pagination

List endpoints support pagination with the following query parameters:

- `page` (default: 1): Page number (1-indexed)
- `page_size` (default: 20, max: 100): Number of items per page

**Paginated Response Format:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

**Pagination Calculation:**
- Total pages = ceil(total / page_size)
- Has next page = (page * page_size) < total
- Has previous page = page > 1

---

## Filtering

Many list endpoints support filtering via query parameters:

**Example Filters:**
- `company_id` - Filter by company
- `is_active` - Filter by active status (true/false)
- `search_type` - Filter by type
- `status` - Filter by status
- `days` - Filter by date range (number of days)

**Example Request:**
```
GET /api/v1/report-schedules?company_id=1&is_active=true&page=1&page_size=20
```

---

## OpenAPI Documentation

Interactive API documentation is available at:

- **Swagger UI:** `http://localhost:8000/api/docs`
- **ReDoc:** `http://localhost:8000/api/redoc`

These interfaces provide:
- Complete endpoint listing
- Request/response schemas
- Try-it-out functionality
- Authentication testing

---

## Changelog

### Version 1.0.0 (2025-01-15)

**New Features:**
- Report Schedules API (8 endpoints)
- Search History API (3 endpoints)
- Web Scraping API (8 endpoints)
- Email Delivery API (10 endpoints)
- Link Deduplication API (3 endpoints)
- User Preferences API (2 endpoints)
- SEO Services API (7 endpoints)

**Integrations:**
- Google Custom Search API
- YouTube Data API
- GNews API
- IPInfo API
- WhoAPI integration

---

For more information, see:
- [API Usage Guide](API_USAGE_GUIDE.md)
- [Code Examples](examples/)
- [Postman Collection](POSTMAN_COLLECTION.json)
