# Capilytics API Usage Guide

Complete guide to using the Capilytics API for competitive intelligence and analytics.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Making Your First API Call](#making-your-first-api-call)
4. [Common Use Cases](#common-use-cases)
5. [Best Practices](#best-practices)
6. [SDKs and Client Libraries](#sdks-and-client-libraries)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [Testing and Development](#testing-and-development)
10. [Production Deployment](#production-deployment)

---

## Getting Started

### Prerequisites

- Python 3.8+ or Node.js 14+ (for SDK usage)
- API access credentials
- Basic understanding of REST APIs and JSON
- HTTP client (curl, Postman, or programming language HTTP library)

### Base URL

```
Development: http://localhost:8000/api/v1
Production: https://api.capilytics.com/api/v1
```

### Quick Start

1. **Register an account** via the API or web interface
2. **Login** to receive your JWT access token
3. **Store the token** securely for subsequent API calls
4. **Make authenticated requests** using the Bearer token

---

## Authentication

### Registration

Create a new user account:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "name": "John Doe"
  }'
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "USER"
}
```

### Login

Authenticate and receive an access token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

**Response:**
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

### Using the Token

Include the token in the `Authorization` header for all authenticated requests:

```bash
curl -X GET http://localhost:8000/api/v1/report-schedules \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Token Expiration

- **Default Token Lifetime:** 24 hours
- **Recommendation:** Implement token refresh logic in your application
- **On Expiration:** Re-authenticate using the login endpoint

---

## Making Your First API Call

### Step 1: Login and Get Token

```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json={
        'email': 'user@example.com',
        'password': 'SecurePassword123!'
    }
)

token = response.json()['access_token']
print(f"Access Token: {token}")
```

### Step 2: Make Authenticated Request

```python
# Set up headers
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# List report schedules
response = requests.get(
    'http://localhost:8000/api/v1/report-schedules',
    headers=headers
)

schedules = response.json()
print(f"Found {schedules['total']} schedules")
```

### Step 3: Create a Resource

```python
# Create a new report schedule
schedule_data = {
    'company_id': 1,
    'name': 'Daily Competitor Report',
    'description': 'Automated daily competitor analysis',
    'report_type': 'competitor_analysis',
    'cron_expression': '0 9 * * *',
    'parameters': {
        'competitors': [1, 2, 3],
        'metrics': ['traffic', 'engagement']
    },
    'email_recipients': ['team@company.com'],
    'notify_on_completion': True
}

response = requests.post(
    'http://localhost:8000/api/v1/report-schedules',
    headers=headers,
    json=schedule_data
)

if response.status_code == 201:
    schedule = response.json()
    print(f"Created schedule ID: {schedule['id']}")
else:
    print(f"Error: {response.json()['detail']}")
```

---

## Common Use Cases

### Use Case 1: Automated Competitive Intelligence Reports

**Scenario:** Schedule weekly competitor analysis reports to be emailed to your team.

```python
import requests

BASE_URL = 'http://localhost:8000/api/v1'
headers = {'Authorization': f'Bearer {token}'}

# Step 1: Add competitors
competitors = []
for competitor_name in ['CompetitorA', 'CompetitorB', 'CompetitorC']:
    response = requests.post(
        f'{BASE_URL}/competitors',
        headers=headers,
        json={
            'name': competitor_name,
            'website': f'https://{competitor_name.lower()}.com',
            'industry': 'Software'
        }
    )
    competitors.append(response.json()['id'])

# Step 2: Create email recipients
response = requests.post(
    f'{BASE_URL}/email/recipients',
    headers=headers,
    json={
        'company_id': 1,
        'email': 'team@mycompany.com',
        'name': 'Marketing Team'
    }
)

# Step 3: Create automated report schedule
response = requests.post(
    f'{BASE_URL}/report-schedules',
    headers=headers,
    json={
        'company_id': 1,
        'name': 'Weekly Competitor Analysis',
        'report_type': 'competitor_analysis',
        'cron_expression': '0 9 * * MON',  # Every Monday at 9 AM
        'parameters': {
            'competitor_ids': competitors,
            'metrics': ['traffic', 'seo', 'social_media'],
            'include_charts': True
        },
        'email_recipients': ['team@mycompany.com'],
        'notify_on_completion': True
    }
)

schedule = response.json()
print(f"Schedule created! Next run: {schedule['next_run_at']}")
```

### Use Case 2: Website Change Monitoring

**Scenario:** Monitor competitor website changes and receive alerts.

```python
# Step 1: Create scraping schedule
response = requests.post(
    f'{BASE_URL}/scraping/schedules',
    headers=headers,
    json={
        'name': 'Daily Homepage Monitor',
        'url': 'https://competitor.com',
        'company_id': 1,
        'competitor_id': 1,
        'cron_expression': '0 8 * * *',  # Daily at 8 AM
        'capture_screenshot': True,
        'scraping_config': {
            'wait_for_selector': '#main-content',
            'timeout': 30000
        }
    }
)

# Step 2: Check for content changes
response = requests.get(
    f'{BASE_URL}/scraping/content',
    headers=headers,
    params={'competitor_id': 1, 'page': 1, 'page_size': 10}
)

content_list = response.json()['content']

# Step 3: Compare versions
if len(content_list) >= 2:
    latest = content_list[0]
    previous = content_list[1]

    response = requests.get(
        f'{BASE_URL}/scraping/content/{latest["id"]}/diff',
        headers=headers,
        params={'compare_to': previous['id']}
    )

    diff = response.json()
    if diff['has_changed']:
        print(f"Website changed! {diff['change_percentage']}% difference")
        print(f"Changes: {diff['diff_summary']}")
```

### Use Case 3: SEO Performance Tracking

**Scenario:** Track your content's SEO performance and compare with competitors.

```python
# Step 1: Perform Google search for target keywords
response = requests.post(
    f'{BASE_URL}/seo/google-search',
    headers=headers,
    json={
        'query': 'competitive intelligence software',
        'max_results': 20,
        'language': 'en',
        'date_restrict': 'm1'  # Last month
    }
)

search_results = response.json()
print(f"Found {search_results['total_results']} results")

# Step 2: Analyze content performance
response = requests.post(
    f'{BASE_URL}/seo/content-performance',
    headers=headers,
    json={
        'url': 'https://mycompany.com/blog/competitive-intelligence',
        'competitors': [
            'https://competitor1.com/blog/ci-tools',
            'https://competitor2.com/resources/ci'
        ],
        'metrics': ['ranking', 'backlinks', 'social_shares']
    }
)

performance = response.json()
print(f"Ranking position: {performance['ranking_position']}")
print(f"Backlinks: {performance['backlink_estimate']}")
print(f"Social shares: {performance['social_shares']}")

# Step 3: Track brand mentions
response = requests.post(
    f'{BASE_URL}/seo/brand-mentions',
    headers=headers,
    json={
        'brand_name': 'Capilytics',
        'keywords': ['analytics', 'competitive intelligence'],
        'competitors': ['CompetitorA', 'CompetitorB'],
        'date_restrict': 'w1',  # Last week
        'max_results': 50
    }
)

mentions = response.json()
print(f"Brand mentions: {mentions['mentions_found']}")
print(f"Sentiment: {mentions['sentiment_distribution']}")
```

### Use Case 4: YouTube Competitor Analysis

**Scenario:** Monitor competitor YouTube channels and track video performance.

```python
# Step 1: Get competitor channel statistics
channel_id = 'UCcompetitor123'
response = requests.get(
    f'{BASE_URL}/seo/youtube/channel/{channel_id}/stats',
    headers=headers
)

channel_stats = response.json()
print(f"Channel: {channel_stats['title']}")
print(f"Subscribers: {channel_stats['subscriber_count']:,}")
print(f"Total views: {channel_stats['view_count']:,}")
print(f"Videos: {channel_stats['video_count']}")

# Step 2: Track competitor videos
response = requests.post(
    f'{BASE_URL}/seo/youtube/competitor/1/videos',
    headers=headers,
    json={
        'channel_id': channel_id,
        'max_videos': 20,
        'published_after': '2025-01-01T00:00:00Z'
    }
)

tracking = response.json()
print(f"Analyzed {tracking['videos_analyzed']} videos")
print(f"Average engagement rate: {tracking['avg_engagement_rate']:.2f}%")
print(f"Top topics: {', '.join(tracking['trending_topics'])}")

# Step 3: Analyze specific video
video_id = 'abc123xyz'
response = requests.get(
    f'{BASE_URL}/seo/youtube/video/{video_id}/analytics',
    headers=headers
)

video = response.json()
print(f"\nVideo: {video['title']}")
print(f"Views: {video['view_count']:,}")
print(f"Engagement rate: {video['engagement_rate']:.2f}%")
```

### Use Case 5: Link Deduplication and Cleanup

**Scenario:** Identify and merge duplicate links in your database.

```python
# Step 1: Detect duplicate links
response = requests.post(
    f'{BASE_URL}/links/detect-duplicates',
    headers=headers,
    json={
        'company_id': 1,
        'similarity_threshold': 0.85,
        'include_inactive': False
    }
)

duplicates = response.json()
print(f"Analyzed {duplicates['total_links_analyzed']} links")
print(f"Found {duplicates['duplicate_groups_found']} duplicate groups")

# Step 2: Review duplicate groups
for group in duplicates['duplicate_groups'][:5]:
    print(f"\nDuplicate group:")
    print(f"  Normalized URL: {group['normalized_url']}")
    print(f"  Similarity: {group['similarity_score']}")
    print(f"  Link IDs: {group['link_ids']}")
    print(f"  URLs: {group['urls']}")

# Step 3: Merge duplicates
if duplicates['duplicate_groups']:
    first_group = duplicates['duplicate_groups'][0]
    primary_id = first_group['link_ids'][0]
    duplicate_ids = first_group['link_ids'][1:]

    response = requests.post(
        f'{BASE_URL}/links/merge',
        headers=headers,
        json={
            'primary_link_id': primary_id,
            'duplicate_link_ids': duplicate_ids,
            'merge_metadata': True,
            'merge_tags': True
        }
    )

    result = response.json()
    print(f"\n{result['message']}")

# Step 4: Generate comprehensive report
response = requests.get(
    f'{BASE_URL}/links/duplicates/report',
    headers=headers,
    params={'company_id': 1, 'similarity_threshold': 0.85}
)

report = response.json()
print(f"\nDuplication Report:")
print(f"  Total links: {report['total_links']}")
print(f"  Unique links: {report['unique_links']}")
print(f"  Duplicate links: {report['duplicate_links']}")
print(f"  Duplication rate: {report['duplication_rate']:.2f}%")
print(f"  Recommendations: {', '.join(report['recommendations'])}")
```

### Use Case 6: Search Analytics and Insights

**Scenario:** Analyze search patterns and optimize search queries.

```python
# Step 1: Get search analytics
response = requests.get(
    f'{BASE_URL}/search-history/analytics',
    headers=headers,
    params={'company_id': 1, 'days': 30}
)

analytics = response.json()
print(f"Total searches: {analytics['total_searches']}")
print(f"Unique queries: {analytics['unique_queries']}")
print(f"Average execution time: {analytics['avg_execution_time_ms']:.2f}ms")

# Step 2: Review top queries
print("\nTop 10 Queries:")
for i, query in enumerate(analytics['top_queries'][:10], 1):
    print(f"  {i}. '{query['query']}' - {query['count']} searches")

# Step 3: Analyze search distribution
print("\nSearch Types:")
for search_type, count in analytics['search_types_distribution'].items():
    percentage = (count / analytics['total_searches']) * 100
    print(f"  {search_type}: {count} ({percentage:.1f}%)")

# Step 4: Peak search hours
print("\nPeak Search Hours:")
sorted_hours = sorted(
    analytics['searches_by_hour'].items(),
    key=lambda x: x[1],
    reverse=True
)
for hour, count in sorted_hours[:5]:
    print(f"  {hour}:00 - {count} searches")

# Step 5: Cleanup old searches (optional)
response = requests.delete(
    f'{BASE_URL}/search-history/cleanup',
    headers=headers,
    params={'days': 90}
)

cleanup = response.json()
print(f"\n{cleanup['message']}")
```

---

## Best Practices

### 1. Authentication and Security

**Store Tokens Securely:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Store token in environment variable
TOKEN = os.getenv('CAPILYTICS_API_TOKEN')

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}
```

**Rotate Tokens Regularly:**
```python
def refresh_token():
    """Re-authenticate to get fresh token"""
    response = requests.post(
        f'{BASE_URL}/auth/login',
        json={
            'email': os.getenv('API_EMAIL'),
            'password': os.getenv('API_PASSWORD')
        }
    )
    return response.json()['access_token']
```

### 2. Error Handling

**Always Handle Errors Gracefully:**
```python
def make_api_request(method, endpoint, **kwargs):
    """Wrapper for API requests with error handling"""
    try:
        response = requests.request(method, f'{BASE_URL}{endpoint}', **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Authentication failed. Please check your token.")
        elif e.response.status_code == 404:
            print("Resource not found.")
        elif e.response.status_code == 429:
            print("Rate limit exceeded. Please wait before retrying.")
        else:
            print(f"HTTP Error: {e.response.status_code}")
            print(f"Details: {e.response.json().get('detail', 'Unknown error')}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {str(e)}")
        raise
```

### 3. Rate Limiting

**Implement Exponential Backoff:**
```python
import time

def make_request_with_retry(func, max_retries=3):
    """Retry failed requests with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries exceeded")
```

### 4. Pagination

**Handle Pagination Efficiently:**
```python
def get_all_pages(endpoint, params=None):
    """Fetch all pages of paginated results"""
    all_items = []
    page = 1
    params = params or {}

    while True:
        params['page'] = page
        params['page_size'] = 100  # Max page size

        response = make_api_request('GET', endpoint, headers=headers, params=params)

        all_items.extend(response['items'])

        total_pages = (response['total'] + params['page_size'] - 1) // params['page_size']
        if page >= total_pages:
            break

        page += 1

    return all_items
```

### 5. Batch Operations

**Process Data in Batches:**
```python
def batch_create_recipients(email_list, batch_size=10):
    """Create email recipients in batches"""
    results = []

    for i in range(0, len(email_list), batch_size):
        batch = email_list[i:i + batch_size]

        for email_data in batch:
            try:
                response = make_api_request(
                    'POST',
                    '/email/recipients',
                    headers=headers,
                    json=email_data
                )
                results.append(response)
            except Exception as e:
                print(f"Failed to create recipient {email_data['email']}: {str(e)}")

        # Rate limiting delay between batches
        time.sleep(1)

    return results
```

### 6. Logging and Monitoring

**Implement Comprehensive Logging:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='api_client.log'
)

logger = logging.getLogger('capilytics_client')

def log_api_call(method, endpoint, status_code, duration):
    """Log API call details"""
    logger.info(
        f"{method} {endpoint} - Status: {status_code} - Duration: {duration:.2f}s"
    )
```

### 7. Caching

**Cache Frequently Accessed Data:**
```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def get_competitor_cached(competitor_id, cache_time=3600):
    """Cache competitor data for 1 hour"""
    response = make_api_request(
        'GET',
        f'/competitors/{competitor_id}',
        headers=headers
    )
    return response

# Invalidate cache after specified time
def get_competitor_with_ttl(competitor_id, ttl=3600):
    """Get competitor with time-to-live cache"""
    cache_key = f"competitor_{competitor_id}_{int(time.time() / ttl)}"
    # Implementation depends on your caching solution
    pass
```

### 8. Validation

**Validate Data Before Sending:**
```python
from pydantic import BaseModel, EmailStr, Field, validator

class ScheduleCreate(BaseModel):
    company_id: int
    name: str = Field(..., min_length=1, max_length=200)
    report_type: str
    cron_expression: str
    email_recipients: list[EmailStr]

    @validator('cron_expression')
    def validate_cron(cls, v):
        # Basic cron validation
        parts = v.split()
        if len(parts) != 5:
            raise ValueError('Invalid cron expression format')
        return v

# Use model for validation
schedule_data = ScheduleCreate(
    company_id=1,
    name='Weekly Report',
    report_type='competitor_analysis',
    cron_expression='0 9 * * MON',
    email_recipients=['team@company.com']
)

response = make_api_request(
    'POST',
    '/report-schedules',
    headers=headers,
    json=schedule_data.dict()
)
```

---

## SDKs and Client Libraries

### Python SDK

**Installation:**
```bash
pip install capilytics-python
```

**Usage:**
```python
from capilytics import CapilyticsClient

# Initialize client
client = CapilyticsClient(
    email='user@example.com',
    password='SecurePassword123!',
    base_url='http://localhost:8000/api/v1'
)

# Automatic authentication
client.authenticate()

# Use resource methods
schedules = client.report_schedules.list(company_id=1, is_active=True)
print(f"Found {len(schedules)} active schedules")

# Create resources
schedule = client.report_schedules.create(
    company_id=1,
    name='Weekly Report',
    report_type='competitor_analysis',
    cron_expression='0 9 * * MON',
    email_recipients=['team@company.com']
)

# Automatic token refresh
competitor = client.competitors.get(1)
```

### JavaScript/TypeScript SDK

**Installation:**
```bash
npm install @capilytics/sdk
```

**Usage:**
```typescript
import { CapilyticsClient } from '@capilytics/sdk';

// Initialize client
const client = new CapilyticsClient({
  email: 'user@example.com',
  password: 'SecurePassword123!',
  baseUrl: 'http://localhost:8000/api/v1'
});

// Authenticate
await client.authenticate();

// Use async/await
const schedules = await client.reportSchedules.list({
  companyId: 1,
  isActive: true
});

console.log(`Found ${schedules.total} schedules`);

// TypeScript types included
const schedule: ReportSchedule = await client.reportSchedules.create({
  companyId: 1,
  name: 'Weekly Report',
  reportType: 'competitor_analysis',
  cronExpression: '0 9 * * MON',
  emailRecipients: ['team@company.com']
});
```

### cURL Examples

**Basic Request:**
```bash
# Set token variable
TOKEN="your_jwt_token_here"

# List schedules
curl -X GET "http://localhost:8000/api/v1/report-schedules?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Create schedule
curl -X POST "http://localhost:8000/api/v1/report-schedules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 1,
    "name": "Weekly Report",
    "report_type": "competitor_analysis",
    "cron_expression": "0 9 * * MON",
    "email_recipients": ["team@company.com"]
  }'
```

---

## Error Handling

### Common Errors and Solutions

**401 Unauthorized:**
```
Problem: Token expired or invalid
Solution: Re-authenticate to get a new token
```

**404 Not Found:**
```
Problem: Resource doesn't exist
Solution: Verify resource ID and check existence
```

**429 Too Many Requests:**
```
Problem: Rate limit exceeded
Solution: Implement exponential backoff and retry
```

**500 Internal Server Error:**
```
Problem: Server-side error
Solution: Check request format, retry later, contact support
```

### Error Response Format

```json
{
  "detail": "Error message explaining the issue"
}
```

---

## Rate Limiting

### Rate Limit Information

- **Hourly Limit:** 1000 requests
- **Burst Limit:** 100 requests per minute
- **Headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### Best Practices

1. **Monitor Rate Limits:**
```python
def check_rate_limit(response):
    """Check rate limit from response headers"""
    remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))

    if remaining < 10:
        logger.warning(f"Rate limit low: {remaining} requests remaining")
        print(f"Rate limit resets at: {datetime.fromtimestamp(reset_time)}")
```

2. **Implement Throttling:**
```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            now = time.time()

            # Remove old calls outside the period
            while self.calls and self.calls[0] < now - self.period:
                self.calls.popleft()

            # Wait if rate limit reached
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.calls.popleft()

            self.calls.append(time.time())
            return func(*args, **kwargs)

        return wrapper

# Usage
@RateLimiter(max_calls=100, period=60)
def make_api_call():
    return make_api_request('GET', '/report-schedules', headers=headers)
```

---

## Testing and Development

### Development Environment Setup

```bash
# Clone repository
git clone https://github.com/capilytics/api-examples.git
cd api-examples

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your credentials

# Run tests
pytest tests/
```

### Testing with Postman

1. **Import Collection:** Load `POSTMAN_COLLECTION.json`
2. **Set Environment:** Configure base URL and authentication
3. **Test Endpoints:** Use pre-configured requests
4. **Automate Tests:** Set up Postman test scripts

### Unit Testing

```python
import pytest
from unittest.mock import Mock, patch
from capilytics import CapilyticsClient

@pytest.fixture
def client():
    return CapilyticsClient(
        email='test@example.com',
        password='test123',
        base_url='http://localhost:8000/api/v1'
    )

def test_authentication(client):
    """Test authentication flow"""
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = {
            'access_token': 'test_token',
            'token_type': 'bearer'
        }

        client.authenticate()
        assert client.token == 'test_token'

def test_list_schedules(client):
    """Test listing report schedules"""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {
            'schedules': [],
            'total': 0,
            'page': 1,
            'page_size': 20
        }

        schedules = client.report_schedules.list()
        assert schedules['total'] == 0
```

---

## Production Deployment

### Environment Configuration

```bash
# Production environment variables
export CAPILYTICS_API_URL=https://api.capilytics.com/api/v1
export CAPILYTICS_EMAIL=prod@company.com
export CAPILYTICS_PASSWORD=SecureProductionPassword
export LOG_LEVEL=INFO
export RATE_LIMIT_MAX_CALLS=1000
export RATE_LIMIT_PERIOD=3600
```

### Production Best Practices

1. **Use HTTPS Only**
2. **Store Credentials Securely** (use environment variables or secret management)
3. **Implement Comprehensive Logging**
4. **Monitor API Usage and Errors**
5. **Set Up Alerts for Rate Limits**
6. **Implement Circuit Breakers**
7. **Use Connection Pooling**
8. **Cache Frequently Accessed Data**

### Health Checks

```python
def health_check():
    """Check API health"""
    try:
        response = requests.get(f'{BASE_URL}/../health', timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False
```

### Monitoring and Alerting

```python
import sentry_sdk

# Initialize Sentry for error tracking
sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0
)

# Track API errors
try:
    response = make_api_request('GET', '/report-schedules', headers=headers)
except Exception as e:
    sentry_sdk.capture_exception(e)
    raise
```

---

## Additional Resources

- **API Reference:** [API_REFERENCE.md](API_REFERENCE.md)
- **Code Examples:** [examples/](examples/)
- **Postman Collection:** [POSTMAN_COLLECTION.json](POSTMAN_COLLECTION.json)
- **Interactive Docs:** http://localhost:8000/api/docs
- **Support:** support@capilytics.com
- **Status Page:** https://status.capilytics.com

---

## Changelog

### Version 1.0.0 (2025-01-15)

- Initial API release
- 41+ REST endpoints
- JWT authentication
- Comprehensive documentation
- Python and JavaScript SDKs
- Postman collection

---

For technical support or questions, please contact: support@capilytics.com
