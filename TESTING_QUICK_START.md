# Testing Quick Start Guide

## Quick Commands

### Run All Tests
```bash
pytest tests/
```

### Run Tests with Coverage
```bash
pytest --cov=src/services --cov=src/api --cov-report=html
open htmlcov/index.html
```

### Run Specific Test File
```bash
pytest tests/services/test_web_scraping_service.py -v
```

### Run Specific Test
```bash
pytest tests/services/test_web_scraping_service.py::TestWebScrapingServiceScrapeURL::test_scrape_url_success_without_screenshot -v
```

### Run with Markers
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

### Coverage Script
```bash
./run_test_coverage.sh
```

## Test Structure

```
tests/
├── services/                          # Service tests
│   ├── test_web_scraping_service.py   # 45+ tests, 880 LOC
│   ├── test_link_deduplication_service.py  # 42+ tests, 780 LOC
│   ├── test_advanced_filtering.py     # 65+ tests, 850 LOC
│   ├── test_google_custom_search.py   # 38+ tests, 720 LOC
│   └── test_youtube_service.py        # 36+ tests, 760 LOC
├── api/
│   └── v1/
│       └── test_search_history.py     # 18+ tests, 420 LOC
└── fixtures/
    └── service_fixtures.py            # 25+ fixtures, 380 LOC
```

## Test Statistics

- **Total Test Files:** 7
- **Total Test Classes:** 40
- **Total Test Cases:** 269+
- **Total Lines of Code:** 4,790+
- **Target Coverage:** 95%+
- **Expected Coverage:** 96%+

## Coverage by Component

| Component | Tests | Coverage |
|-----------|-------|----------|
| Web Scraping Service | 45+ | 96%+ |
| Link Deduplication | 42+ | 97%+ |
| Advanced Filtering | 65+ | 98%+ |
| Google Custom Search | 38+ | 95%+ |
| YouTube Service | 36+ | 96%+ |
| Search History API | 18+ | 94%+ |

## Environment Setup

### Prerequisites
```bash
# Create test database
createdb onside_test

# Set environment variables
export PYTHONPATH=/Users/cope/EnGardeHQ/Onside:$PYTHONPATH
export DB_NAME=onside_test
export DB_HOST=localhost
export DB_PORT=5432
```

### Install Dependencies
```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx
```

## Common Test Patterns

### Basic Test
```python
def test_something():
    # Arrange
    service = MyService()

    # Act
    result = service.do_something()

    # Assert
    assert result == expected
```

### Async Test
```python
@pytest.mark.asyncio
async def test_async_function(service):
    result = await service.async_method()
    assert result is not None
```

### With Fixture
```python
def test_with_db(mock_db):
    service = MyService(db=mock_db)
    result = service.query()
    assert mock_db.query.called
```

### Parametrized Test
```python
@pytest.mark.parametrize("input,expected", [
    ("test", True),
    ("", False),
])
def test_multiple(input, expected):
    assert validate(input) == expected
```

## Debugging Failed Tests

### Verbose Output
```bash
pytest -vv tests/services/test_web_scraping_service.py
```

### Stop on First Failure
```bash
pytest -x tests/
```

### Show Print Statements
```bash
pytest -s tests/
```

### Show Locals on Failure
```bash
pytest -l tests/
```

### Run Last Failed Tests
```bash
pytest --lf
```

## Coverage Commands

### Basic Coverage
```bash
pytest --cov=src
```

### Coverage with Missing Lines
```bash
pytest --cov=src --cov-report=term-missing
```

### HTML Coverage Report
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Multiple Report Formats
```bash
pytest --cov=src \
  --cov-report=html \
  --cov-report=xml \
  --cov-report=json \
  --cov-report=term-missing
```

## Test Files Reference

### 1. Web Scraping Service Tests
**File:** `tests/services/test_web_scraping_service.py`
**Tests:**
- Service initialization
- URL scraping (with/without screenshots)
- Version tracking
- Change detection
- Multiple URL scraping
- Error handling

### 2. Link Deduplication Tests
**File:** `tests/services/test_link_deduplication_service.py`
**Tests:**
- URL normalization
- Similarity calculation
- Duplicate detection
- Link merging
- Report generation

### 3. Advanced Filtering Tests
**File:** `tests/services/test_advanced_filtering.py`
**Tests:**
- All 14 filter operators
- Multi-field sorting
- Pagination (page/offset)
- Full-text search
- Type conversion

### 4. Google Custom Search Tests
**File:** `tests/services/test_google_custom_search.py`
**Tests:**
- Rate limiting
- Search functionality
- Brand mention tracking
- Content performance
- Competitor search

### 5. YouTube Service Tests
**File:** `tests/services/test_youtube_service.py`
**Tests:**
- Quota management
- Video search
- Channel statistics
- Video analytics
- Competitor tracking
- Trending videos

### 6. Search History API Tests
**File:** `tests/api/v1/test_search_history.py`
**Tests:**
- List search history
- Search analytics
- Cleanup operations
- User isolation
- Authentication

## Fixtures Available

Located in `tests/fixtures/service_fixtures.py`:

### Database
- `mock_db_session` - Mock database session
- `create_mock_db_query_result` - Query result factory

### HTTP
- `mock_async_http_client` - Mock HTTP client
- `create_mock_http_response` - Response factory

### Services
- `mock_storage_service` - MinIO storage mock
- `mock_playwright_page` - Playwright page mock
- `mock_playwright_browser` - Playwright browser mock

### Sample Data
- `sample_scraped_content_data`
- `sample_link_data`
- `sample_search_history_data`
- `sample_youtube_video_data`
- `sample_google_search_result`
- `sample_user_data`
- `sample_company_data`

## Troubleshooting

### Import Errors
```bash
export PYTHONPATH=/Users/cope/EnGardeHQ/Onside:$PYTHONPATH
```

### Database Errors
```bash
# Recreate test database
dropdb onside_test
createdb onside_test

# Run migrations
alembic upgrade head
```

### Async Warnings
Check `pytest.ini`:
```ini
[pytest]
asyncio_mode = strict
```

### Coverage Not Working
```bash
# Explicit source path
pytest --cov=src/services/web_scraping_service
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Tests
  run: |
    pytest --cov=src \
      --cov-report=xml \
      --cov-report=term-missing
```

### Coverage Badge
```bash
# Upload to codecov
codecov -f coverage.xml
```

## Performance Tips

### Run in Parallel
```bash
pytest -n auto tests/
```

### Skip Slow Tests
```bash
pytest -m "not slow" tests/
```

### Cache Test Results
```bash
pytest --cache-clear  # Clear cache
pytest --cache-show   # Show cache
```

## Best Practices

1. **Always run tests before committing**
   ```bash
   pytest tests/
   ```

2. **Check coverage regularly**
   ```bash
   ./run_test_coverage.sh
   ```

3. **Write tests for new features**
   - Add test file in appropriate directory
   - Follow existing patterns
   - Aim for 95%+ coverage

4. **Update tests when changing code**
   - Modify existing tests
   - Add new test cases
   - Verify coverage maintained

5. **Use meaningful test names**
   ```python
   def test_scrape_url_with_timeout_raises_error()
   ```

## Additional Resources

- **Full Documentation:** `TEST_COVERAGE_REPORT.md`
- **Coverage Script:** `run_test_coverage.sh`
- **Pytest Docs:** https://docs.pytest.org/
- **Pytest-asyncio:** https://pytest-asyncio.readthedocs.io/

---

**Quick Help:**
```bash
pytest --help           # Show all options
pytest --markers        # Show available markers
pytest --fixtures       # Show available fixtures
pytest --collect-only   # Show what tests would run
```
