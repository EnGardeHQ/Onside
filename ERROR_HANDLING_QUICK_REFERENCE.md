# En Garde Integration - Error Handling Quick Reference

## Quick Start

### Import Error Handling
```python
from src.services.engarde_integration.error_handling import (
    WebsiteUnreachableError,
    InsufficientDataError,
    AnalysisTimeoutError,
    SERPAPIError,
    ScrapingError,
    InvalidQuestionnaireError,
    handle_analysis_failure,
    retry_with_backoff,
    save_partial_results
)
```

### Import Validation
```python
from src.services.engarde_integration.validation import (
    validate_url,
    validate_domain,
    validate_questionnaire,
    sanitize_input,
    check_rate_limit
)
```

---

## Error Handling Patterns

### 1. Website Crawling with Fallback
```python
try:
    site_data = await crawl_website(url)
except WebsiteUnreachableError as e:
    logger.warning(f"Website unreachable: {e.url}")
    # Fallback to minimal data
    site_data = create_minimal_site_data(questionnaire)
except ScrapingError as e:
    logger.error(f"Scraping failed: {e.reason}")
    # Try alternative method or fail gracefully
    site_data = await try_simple_http_request(url)
```

### 2. SERP Analysis with Fallback
```python
try:
    serp_data = await analyze_serp(keywords)
except SERPAPIError as e:
    logger.warning(f"SERP API failed: {e.api_name}")
    # Use cached data or skip SERP analysis
    serp_data = await get_cached_serp_data(keywords) or {}
```

### 3. Retry with Backoff
```python
@retry_with_backoff(
    max_retries=3,
    initial_delay=1.0,
    exceptions=(ConnectionError, TimeoutError)
)
async def fetch_data(url):
    async with session.get(url) as response:
        return await response.text()
```

### 4. Comprehensive Error Handling
```python
try:
    results = await analyze_brand(job_id, questionnaire)
except Exception as e:
    # Use comprehensive error handler
    result = await handle_analysis_failure(
        job_id,
        e,
        questionnaire.to_dict(),
        db,
        partial_results
    )
    return result
```

---

## Validation Patterns

### 1. URL Validation
```python
# Basic validation (format only)
is_valid, error = await validate_url(url, check_reachability=False)
if not is_valid:
    raise InvalidQuestionnaireError("primary_website", error)

# Full validation (reachability check)
try:
    is_valid, error = await validate_url(url, check_reachability=True)
except WebsiteUnreachableError as e:
    # Handle unreachable website
    pass
```

### 2. Questionnaire Validation
```python
try:
    is_valid, errors = await validate_questionnaire(data)
except InvalidQuestionnaireError as e:
    return {
        "error": e.to_dict(),
        "status_code": 422
    }
```

### 3. Input Sanitization
```python
from src.services.engarde_integration.validation import sanitize_input

# Sanitize user input
brand_name = sanitize_input(data.get("brand_name"))
industry = sanitize_input(data.get("industry"))
```

### 4. Rate Limiting Check
```python
is_allowed, error = await check_rate_limit(user_id, db)
if not is_allowed:
    raise HTTPException(status_code=429, detail=error)
```

---

## Error Response Format

### Successful Analysis
```json
{
  "job_id": "uuid",
  "status": "completed",
  "results": {
    "keywords_found": 47,
    "competitors_identified": 12,
    "content_opportunities": 8
  }
}
```

### Analysis with Warnings
```json
{
  "job_id": "uuid",
  "status": "completed",
  "results": {
    "keywords_found": 15,
    "competitors_identified": 3,
    "warnings": [
      "SERP analysis unavailable - limited competitor data"
    ]
  }
}
```

### Failed Analysis
```json
{
  "job_id": "uuid",
  "status": "failed",
  "error": {
    "code": "WEBSITE_UNREACHABLE",
    "message": "Could not reach the specified website",
    "details": "Connection timeout after 30 seconds",
    "suggestion": "Please verify the URL or try manual setup",
    "fallback_available": true
  },
  "fallback": {
    "method": "manual_input",
    "message": "Please provide manual keywords and competitors"
  }
}
```

---

## Exception Hierarchy

```
BrandAnalysisError (Base)
├── WebsiteUnreachableError     # Website connection failures
├── InsufficientDataError       # Not enough content found
├── AnalysisTimeoutError        # Exceeded time limits
├── InvalidQuestionnaireError   # Validation failure
├── SERPAPIError               # SERP API failures
└── ScrapingError              # Web scraping failures
```

---

## Common Error Codes

| Code | Meaning | Fallback Available |
|------|---------|-------------------|
| `WEBSITE_UNREACHABLE` | Cannot connect to website | ✅ Manual input |
| `INSUFFICIENT_DATA` | Minimal content found | ✅ Industry defaults |
| `ANALYSIS_TIMEOUT` | Time limit exceeded | ✅ Partial results |
| `SERP_API_ERROR` | SERP API failed | ✅ Cached data |
| `SCRAPING_ERROR` | Scraping blocked | ✅ Alternative methods |
| `INVALID_QUESTIONNAIRE` | Validation failed | ❌ User must fix |
| `RATE_LIMIT_EXCEEDED` | Too many requests | ❌ User must wait |
| `UNKNOWN_ERROR` | Unexpected error | ⚠️ Maybe partial results |

---

## Logging Best Practices

### Error Logging
```python
logger.error(
    f"Analysis failed for job {job_id}",
    exc_info=True,
    extra={
        "job_id": job_id,
        "user_id": user_id,
        "error_type": type(error).__name__,
        "url": url[:100],  # Truncate URLs
        "duration": duration
    }
)
```

### Warning Logging
```python
logger.warning(
    f"SERP API rate limit reached, using cached data",
    extra={
        "api_name": "SerpAPI",
        "cache_age": cache_age,
        "keywords_count": len(keywords)
    }
)
```

### Info Logging
```python
logger.info(
    f"Completed analysis with fallbacks",
    extra={
        "job_id": job_id,
        "keywords_found": len(keywords),
        "fallbacks_used": ["serp", "crawl"],
        "duration": duration
    }
)
```

---

## Testing Error Scenarios

### Run All Error Tests
```bash
pytest tests/test_error_handling.py -v
```

### Run Specific Test Category
```bash
# Test exceptions
pytest tests/test_error_handling.py::TestCustomExceptions -v

# Test validation
pytest tests/test_error_handling.py::TestQuestionnaireValidation -v

# Test retry mechanism
pytest tests/test_error_handling.py::TestRetryMechanism -v
```

---

## Monitoring & Alerts

### Key Metrics to Monitor
- Error rate by type (target: <5%)
- Analysis success rate (target: >95%)
- Average analysis duration (target: <3 min)
- SERP API availability (target: >98%)
- Rate limit exceeded events

### Critical Alerts
- Total error rate >10% (5-min window)
- Unknown error rate >1% (1-hour window)
- Database connection failures (any)
- SERP API auth failures (any)

---

## Production Checklist

Before deploying:
- [ ] Error tracking service configured (Sentry)
- [ ] Monitoring alerts set up
- [ ] API keys in environment variables
- [ ] Rate limits configured
- [ ] Incident response runbook prepared
- [ ] Rollback plan tested

---

## Resources

- **Full QA Report:** `ENGARDE_INTEGRATION_QA_REPORT.md`
- **Error Handling Module:** `src/services/engarde_integration/error_handling.py`
- **Validation Module:** `src/services/engarde_integration/validation.py`
- **Test Suite:** `tests/test_error_handling.py`

---

**Version:** 1.0
**Last Updated:** December 24, 2025
