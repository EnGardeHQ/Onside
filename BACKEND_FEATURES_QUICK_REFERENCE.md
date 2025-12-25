# Backend Features Quick Reference Guide

**Last Updated:** December 22, 2025

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Run Migrations

```bash
alembic upgrade head
```

### 3. Configure Environment

Add to `.env`:

```env
# Google APIs
GOOGLE_SEARCH_API_KEY=your_key
GOOGLE_SEARCH_ENGINE_ID=your_engine_id
YOUTUBE_API_KEY=your_key

# Email (choose one)
SENDGRID_API_KEY=your_key
# OR
AWS_SES_ACCESS_KEY=your_key
AWS_SES_SECRET_KEY=your_secret
AWS_SES_REGION=us-east-1
# OR
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user
SMTP_PASSWORD=pass
```

---

## Feature Usage Examples

### 1. Scheduled Report Generation

```python
from src.models.report_schedule import ReportSchedule
from src.database import get_db

# Create a schedule
schedule = ReportSchedule(
    user_id=1,
    company_id=1,
    name="Weekly Competitor Analysis",
    description="Automated weekly reports",
    report_type="competitor",
    cron_expression="0 9 * * 1",  # Every Monday at 9 AM
    parameters={"competitor_id": 123, "timeframe": "7d"},
    email_recipients=["user@example.com"],
    notify_on_completion=True
)

# Validate cron expression
if schedule.validate_cron_expression():
    schedule.next_run_at = schedule.calculate_next_run()
    db.add(schedule)
    db.commit()

# Pause/Resume
schedule.pause()
schedule.resume()

# Get stats
stats = schedule.get_execution_stats()
print(f"Success rate: {stats['success_rate']}%")
```

### 2. Web Scraping

```python
from src.services.web_scraping_service import WebScrapingService
from src.database import get_db

async def scrape_example():
    async with WebScrapingService() as scraper:
        # Scrape a single URL
        result = await scraper.scrape_url(
            url="https://competitor.com/pricing",
            db=db,
            company_id=1,
            capture_screenshot=True
        )

        print(f"Scraped version {result.version}")
        print(f"Content hash: {result.content_hash}")
        print(f"Screenshot: {result.screenshot_url}")

        # Scrape multiple URLs
        urls = ["https://site1.com", "https://site2.com"]
        results = await scraper.scrape_multiple(urls, db)

        # Get history
        history = await scraper.get_content_history(db, url, limit=10)

        # Compare versions
        comparison = await scraper.compare_versions(db, v1_id, v2_id)
        print(f"Similarity: {comparison['similarity']}")
        print(f"Change: {comparison['change_percentage']}%")
```

### 3. Link Deduplication

```python
from src.services.link_deduplication_service import LinkDeduplicationService
from src.database import get_db

dedup = LinkDeduplicationService(similarity_threshold=0.85)

# Normalize URL
normalized = dedup.normalize_url("https://www.example.com/?utm_source=twitter")
# Result: "https://example.com/"

# Find duplicates for a URL
duplicates = dedup.find_duplicates_for_url(db, url, company_id=1)
for link, similarity in duplicates:
    print(f"{link.url} - {similarity:.2%} similar")

# Find all duplicates
all_dupes = dedup.find_all_duplicates(db, company_id=1)

# Merge duplicates
canonical = dedup.merge_duplicate_links(
    db,
    canonical_id=1,
    duplicate_ids=[2, 3, 4]
)

# Generate report
report = dedup.generate_duplicate_report(db, company_id=1)
print(f"Total duplicates: {report['summary']['total_duplicates']}")
print(f"Savings: {report['summary']['savings_percentage']}%")
```

### 4. Advanced Filtering

```python
from src.services.advanced_filtering import AdvancedFilter
from src.models.report import Report
from src.database import get_db

filter_service = AdvancedFilter()

# Build query
query = db.query(Report)

# Apply filters from request params
params = {
    'type__eq': 'competitor',
    'status__in': 'completed,processing',
    'created_at__gte': '2025-01-01',
    'confidence_score__gt': 0.8,
    'search': 'market analysis',
    'sort': '-created_at,type',
    'page': 1,
    'limit': 50
}

query, metadata = filter_service.apply_all(
    query=query,
    model=Report,
    params=params,
    search_fields=['parameters', 'result']
)

results = query.all()

print(f"Total: {metadata['total']}")
print(f"Page {metadata['page']} of {metadata['pages']}")
print(f"Has next: {metadata['has_next']}")
```

### 5. Google Custom Search

```python
from src.services.google_custom_search import GoogleCustomSearchService

async def google_search_example():
    async with GoogleCustomSearchService() as google:
        # Basic search
        results = await google.search(
            query="artificial intelligence",
            site="techcrunch.com",
            num_results=10
        )

        # Track brand mentions
        mentions = await google.track_brand_mentions(
            brand_name="OnSide",
            days_back=7,
            exclude_own_domain="onside.ai"
        )

        print(f"Total mentions: {mentions['totalMentions']}")
        print(f"Avg sentiment: {mentions['averageSentiment']}")

        # Analyze content performance
        performance = await google.analyze_content_performance(
            url="https://example.com/blog/post"
        )

        print(f"Indexed: {performance['isIndexed']}")
        print(f"Domain visibility: {performance['domainVisibility']}")

        # Competitor search
        comp = await google.competitor_search(
            competitor_domain="competitor.com",
            keywords=["AI", "machine learning", "analytics"]
        )
```

### 6. YouTube API

```python
from src.services.youtube_service import YouTubeService

async def youtube_example():
    async with YouTubeService() as youtube:
        # Search videos
        results = await youtube.search_videos(
            query="competitive intelligence",
            max_results=10,
            order='viewCount'
        )

        # Get channel stats
        channel = await youtube.get_channel_stats("UC_x5XG1OV2P6uZZ5FSM9Ttw")
        print(f"Subscribers: {channel['statistics']['subscriberCount']}")

        # Get video analytics
        video = await youtube.get_video_analytics("dQw4w9WgXcQ")
        print(f"Engagement rate: {video['statistics']['engagementRate']}%")

        # Track competitor
        tracking = await youtube.track_competitor_videos(
            competitor_id="competitor_channel_id",
            max_results=10,
            days_back=30
        )

        print(f"Recent videos: {tracking['recentVideos']}")
        print(f"Total views: {tracking['totalViews']}")
        print(f"Avg engagement: {tracking['averageEngagementRate']}%")
```

### 7. Email Delivery

```python
from src.models.email_delivery import EmailRecipient, EmailDelivery
from src.database import get_db

# Add recipient
recipient = EmailRecipient(
    company_id=1,
    email="user@example.com",
    name="John Doe",
    is_active=True
)
db.add(recipient)
db.commit()

# Create email delivery
email = EmailDelivery(
    report_id=123,
    recipient_email="user@example.com",
    subject="Your Weekly Report",
    body_html="<html>...</html>",
    body_text="Plain text version",
    attachment_path="/storage/reports/report_123.pdf"
)
db.add(email)
db.commit()

# Track delivery
email.mark_sent(provider_message_id="msg_123")
email.mark_opened()
email.mark_clicked()

# Get metrics
metrics = email.get_delivery_metrics()
print(f"Delivery time: {metrics['delivery_time_seconds']}s")
print(f"Time to open: {metrics['time_to_open_seconds']}s")
```

### 8. Search History

```python
from src.models.search_history import SearchHistory
from src.database import get_db

# Log search
search = SearchHistory(
    user_id=1,
    company_id=1,
    query="competitor pricing",
    search_type="link_search",
    filters={"category": "pricing", "region": "US"},
    results_count=42,
    execution_time_ms=123.45,
    language="en",
    ip_address=request.remote_addr,
    user_agent=request.user_agent.string
)
db.add(search)
db.commit()

# Query analytics
from sqlalchemy import func

# Trending queries
trending = (
    db.query(
        SearchHistory.query,
        func.count(SearchHistory.id).label('count')
    )
    .filter(SearchHistory.created_at >= one_week_ago)
    .group_by(SearchHistory.query)
    .order_by(func.count(SearchHistory.id).desc())
    .limit(10)
    .all()
)
```

### 9. i18n (Multilingual)

```python
from src.services.i18n.ui_translator import UITranslator
from src.services.i18n.language_service import SupportedLanguage

translator = UITranslator()

# Translate UI text
title = translator.translate(
    'app.title',
    language=SupportedLanguage.FRENCH
)
# Result: "OnSide - Plateforme d'Intelligence Compétitive"

# With variables
progress = translator.translate(
    'reports.progress.percent_complete',
    language=SupportedLanguage.JAPANESE,
    percent=75
)
# Result: "75% 完了"

# Get all translations
all_langs = translator.get_all('app.welcome')
# Result: {
#   'en': 'Welcome to OnSide',
#   'fr': 'Bienvenue sur OnSide',
#   'ja': 'OnSideへようこそ'
# }

# AI prompts
from src.services.i18n.prompt_translator import PromptTranslator

prompt_translator = PromptTranslator()

prompt = await prompt_translator.translate_prompt(
    template_id='competitor_analysis',
    language=SupportedLanguage.FRENCH,
    variables={
        'company_name': 'Competitor Inc.',
        'industry': 'SaaS',
        'metrics': 'Revenue: $10M'
    }
)
```

---

## Filter Operators Reference

| Operator | Example | Description |
|----------|---------|-------------|
| `eq` | `status__eq=completed` | Equal to |
| `ne` | `type__ne=content` | Not equal to |
| `gt` | `score__gt=0.8` | Greater than |
| `gte` | `age__gte=18` | Greater than or equal |
| `lt` | `views__lt=1000` | Less than |
| `lte` | `date__lte=2025-12-31` | Less than or equal |
| `contains` | `name__contains=test` | Contains (case-sensitive) |
| `icontains` | `title__icontains=report` | Contains (case-insensitive) |
| `startswith` | `url__startswith=https` | Starts with |
| `endswith` | `file__endswith=.pdf` | Ends with |
| `in` | `status__in=active,pending` | In list |
| `not_in` | `type__not_in=draft,archived` | Not in list |
| `is_null` | `deleted_at__is_null=true` | Is NULL |
| `not_null` | `completed_at__not_null=true` | Is not NULL |
| `between` | `score__between=0.5,0.9` | Between two values |

---

## Cron Expression Examples

| Schedule | Expression | Description |
|----------|------------|-------------|
| Every hour | `0 * * * *` | At minute 0 of every hour |
| Daily at 9 AM | `0 9 * * *` | Every day at 9:00 AM |
| Weekly Monday | `0 9 * * 1` | Every Monday at 9:00 AM |
| Monthly 1st | `0 9 1 * *` | 1st day of month at 9:00 AM |
| Every 15 min | `*/15 * * * *` | Every 15 minutes |
| Weekdays 10AM | `0 10 * * 1-5` | Weekdays at 10:00 AM |
| Every 6 hours | `0 */6 * * *` | Every 6 hours |

---

## Model Relationships

### Report Schedule
```
ReportSchedule
  ├── user (User)
  ├── company (Company)
  └── executions (List[ScheduleExecution])
      └── report (Report)
```

### Scraped Content
```
ScrapedContent
  ├── company (Company)
  ├── competitor (Competitor)
  ├── old_version_changes (List[ContentChange])
  └── new_version_changes (List[ContentChange])
```

### Email Delivery
```
EmailRecipient
  └── company (Company)

EmailDelivery
  └── report (Report)
```

### Search History
```
SearchHistory
  ├── user (User)
  └── company (Company)
```

---

## Testing Examples

### Unit Test

```python
import pytest
from src.services.link_deduplication_service import LinkDeduplicationService

def test_url_normalization():
    dedup = LinkDeduplicationService()

    # Test case 1: Remove tracking params
    result = dedup.normalize_url(
        "https://www.example.com/?utm_source=twitter&fbclid=123"
    )
    assert result == "https://example.com/"

    # Test case 2: Remove trailing slash
    result = dedup.normalize_url("https://example.com/page/")
    assert result == "https://example.com/page"

    # Test case 3: Sort query params
    result = dedup.normalize_url("https://example.com?b=2&a=1")
    assert "a=1" in result
    assert result.index("a=1") < result.index("b=2")

def test_similarity_calculation():
    dedup = LinkDeduplicationService()

    # Exact match after normalization
    score = dedup.calculate_similarity(
        "https://example.com/?utm_source=fb",
        "https://www.example.com/"
    )
    assert score == 1.0

    # Different domains
    score = dedup.calculate_similarity(
        "https://site1.com",
        "https://site2.com"
    )
    assert score == 0.0
```

### Integration Test

```python
import pytest
from src.services.web_scraping_service import WebScrapingService
from src.database import get_db

@pytest.mark.asyncio
async def test_web_scraping_workflow(db_session):
    async with WebScrapingService() as scraper:
        # First scrape
        v1 = await scraper.scrape_url(
            "https://example.com",
            db_session,
            company_id=1
        )

        assert v1.version == 1
        assert v1.url == "https://example.com"
        assert v1.content_hash is not None

        # Second scrape (should create version 2)
        v2 = await scraper.scrape_url(
            "https://example.com",
            db_session,
            company_id=1
        )

        assert v2.version == 2

        # Check change detection
        changes = await scraper.get_changes_for_url(
            db_session,
            "https://example.com"
        )

        assert len(changes) > 0
        assert changes[0].old_version_id == v1.id
        assert changes[0].new_version_id == v2.id
```

---

## Common Queries

### Get Scheduled Reports Due Soon

```python
from datetime import datetime, timedelta
from src.models.report_schedule import ReportSchedule

# Get schedules due in the next hour
upcoming = (
    db.query(ReportSchedule)
    .filter(
        ReportSchedule.is_active == True,
        ReportSchedule.next_run_at <= datetime.utcnow() + timedelta(hours=1),
        ReportSchedule.next_run_at > datetime.utcnow()
    )
    .all()
)
```

### Get Recent Content Changes

```python
from src.models.scraped_content import ContentChange

# Get significant changes in last 7 days
changes = (
    db.query(ContentChange)
    .filter(
        ContentChange.detected_at >= datetime.utcnow() - timedelta(days=7),
        ContentChange.change_type.in_(['major', 'significant'])
    )
    .order_by(ContentChange.detected_at.desc())
    .all()
)
```

### Get Email Delivery Stats

```python
from sqlalchemy import func
from src.models.email_delivery import EmailDelivery

stats = (
    db.query(
        func.count(EmailDelivery.id).label('total'),
        func.sum(
            case([(EmailDelivery.status == 'sent', 1)], else_=0)
        ).label('sent'),
        func.sum(
            case([(EmailDelivery.opened_at.isnot(None), 1)], else_=0)
        ).label('opened'),
        func.avg(EmailDelivery.retry_count).label('avg_retries')
    )
    .filter(EmailDelivery.created_at >= one_week_ago)
    .first()
)
```

---

## Troubleshooting

### Playwright Issues

```bash
# Reinstall browsers
playwright install chromium

# Run with debug logging
PLAYWRIGHT_DEBUG=1 python your_script.py

# Increase timeout
SCRAPING_TIMEOUT_MS=60000
```

### Rate Limit Exceeded

```python
# Google Search
service = GoogleCustomSearchService(daily_quota=100)
remaining = service.rate_limiter.get_remaining_calls()

# YouTube
service = YouTubeService(daily_quota=10000)
print(f"Quota used: {service.quota_used}/{service.daily_quota}")
```

### Migration Issues

```bash
# Check current version
alembic current

# Show migration history
alembic history

# Downgrade if needed
alembic downgrade -1

# Upgrade to specific version
alembic upgrade 20250312
```

---

## Performance Tips

1. **Use batch operations** for multiple URLs
2. **Enable caching** for repeated queries
3. **Limit concurrent scraping** (max 5 recommended)
4. **Index frequently queried fields**
5. **Use pagination** for large result sets
6. **Set appropriate timeouts** for external APIs
7. **Monitor quota usage** for external services

---

## Support

For issues or questions:
- Check the main implementation report: `BACKEND_FEATURES_IMPLEMENTATION_REPORT.md`
- Review test files in `tests/`
- Check service documentation in respective files
- Run tests with: `pytest tests/`

---

**Document Version:** 1.0
**Last Updated:** December 22, 2025
