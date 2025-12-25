# OnSide Testing Standards

## Testing Requirements

### Coverage Targets

| Component | Minimum Coverage |
|-----------|------------------|
| Core services | 80% |
| API endpoints | 80% |
| Repositories | 75% |
| Models | 70% |
| Utilities | 70% |
| New code | 80% |

### Test Types Required

#### 1. Unit Tests
Location: `tests/unit/`

- Test individual functions and methods in isolation
- Mock all external dependencies
- Fast execution (< 100ms per test)
- Use pytest fixtures for test data

#### 2. Integration Tests
Location: `tests/integration/`

- Test component interactions
- Test database operations with test database
- Test external API adapters with mocked responses
- May use real database connections

#### 3. API Tests
Location: `tests/api/`

- Test all API endpoints
- Verify request/response schemas
- Test authentication and authorization
- Test error responses

#### 4. Service Tests
Location: `tests/services/`

- Test business logic
- Mock repository layer
- Test error handling
- Test edge cases

#### 5. Performance Tests
Location: `tests/performance/`

- Benchmark critical operations
- Test under load
- Measure response times
- Identify bottlenecks

---

## Test Structure

### File Naming
```
tests/
├── unit/
│   └── services/
│       └── test_gnews_service.py
├── integration/
│   └── test_gnews_integration.py
├── api/
│   └── v1/
│       └── test_gnews_endpoints.py
└── conftest.py
```

### Test Function Naming
```python
def test_<method>_<scenario>_<expected_result>():
    # Example:
    def test_search_with_valid_query_returns_articles():
        pass

    def test_search_with_empty_query_raises_validation_error():
        pass
```

---

## Pytest Configuration

### conftest.py Fixtures

```python
# Required fixtures in tests/conftest.py

@pytest.fixture
def db_session():
    """Provides a test database session."""
    pass

@pytest.fixture
def async_client():
    """Provides async HTTP test client."""
    pass

@pytest.fixture
def mock_external_api():
    """Mocks external API calls."""
    pass

@pytest.fixture
def auth_headers():
    """Provides authenticated request headers."""
    pass

@pytest.fixture
def sample_competitor():
    """Provides sample competitor data."""
    pass
```

### pytest.ini Settings
```ini
[pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = -v --tb=short
markers =
    slow: marks tests as slow
    integration: marks tests requiring database
    external: marks tests calling external APIs
```

---

## Mocking Standards

### External APIs
Always mock external API calls in unit tests:

```python
@pytest.fixture
def mock_gnews_response():
    return {
        "totalArticles": 10,
        "articles": [
            {
                "title": "Test Article",
                "description": "Test description",
                "url": "https://example.com/article",
                "publishedAt": "2025-01-01T00:00:00Z"
            }
        ]
    }

@patch("src.services.external_api.gnews_service.httpx.AsyncClient")
async def test_gnews_search(mock_client, mock_gnews_response):
    mock_client.return_value.__aenter__.return_value.get.return_value.json.return_value = mock_gnews_response
    # Test implementation
```

### Database Operations
Use test fixtures for database:

```python
@pytest.fixture
async def test_db():
    """Create test database and clean up after."""
    # Setup
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()
```

---

## BDD/TDD Workflow

### 1. Red Phase (Write Failing Test)
```python
def test_competitor_news_sentiment_analysis():
    """
    Given a competitor with recent news articles
    When sentiment analysis is requested
    Then return aggregated sentiment scores
    """
    service = CompetitorNewsService()
    result = await service.get_sentiment(competitor_id=1)

    assert "positive" in result
    assert "negative" in result
    assert "neutral" in result
    assert result["total_articles"] > 0
```

### 2. Green Phase (Implement)
Write minimal code to pass the test.

### 3. Refactor Phase
Improve code quality while keeping tests green.

---

## Assertion Patterns

### Response Validation
```python
def test_api_response_structure():
    response = client.get("/api/v1/gnews/search?query=test")

    assert response.status_code == 200
    data = response.json()
    assert "articles" in data
    assert "total" in data
    assert isinstance(data["articles"], list)
```

### Error Handling
```python
def test_api_error_response():
    response = client.get("/api/v1/gnews/search")  # Missing required param

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
```

### Async Operations
```python
@pytest.mark.asyncio
async def test_async_service_call():
    service = GNewsService(api_key="test")
    result = await service.search("test query")

    assert result is not None
    assert len(result.articles) > 0
```

---

## Test Commands

### Run All Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
```

### Run Specific Test Types
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v -m integration

# API tests
pytest tests/api/ -v

# Exclude slow tests
pytest tests/ -v -m "not slow"
```

### Run Single Test File
```bash
pytest tests/services/test_gnews_service.py -v
```

### Run with Debug Output
```bash
pytest tests/ -v -s --log-cli-level=DEBUG
```

---

## CI/CD Integration

### Required Checks
1. All tests pass
2. Coverage >= 80% for new code
3. No test regressions
4. Performance benchmarks within thresholds

### Pre-commit Tests
```bash
# Run before each commit
pytest tests/unit/ -v --tb=short
flake8 src/ tests/
black src/ tests/ --check
mypy src/
```

---

## Common Test Patterns

### Testing Repository Layer
```python
@pytest.mark.asyncio
async def test_repository_create(db_session):
    repo = GNewsRepository(db_session)
    article = GNewsArticle(title="Test", url="https://test.com")

    result = await repo.create(article)

    assert result.id is not None
    assert result.title == "Test"
```

### Testing Service Layer
```python
@pytest.mark.asyncio
async def test_service_with_mocked_repo(mock_repository):
    mock_repository.get_by_id.return_value = sample_data
    service = GNewsService(repository=mock_repository)

    result = await service.get_article(1)

    assert result is not None
    mock_repository.get_by_id.assert_called_once_with(1)
```

### Testing API Endpoints
```python
def test_endpoint_authentication(client):
    # Without auth
    response = client.get("/api/v1/protected")
    assert response.status_code == 401

    # With auth
    response = client.get("/api/v1/protected", headers=auth_headers)
    assert response.status_code == 200
```

---

## Test Data Management

### Factories
Use factories for creating test data:

```python
# tests/factories.py
class CompetitorFactory:
    @staticmethod
    def create(**kwargs):
        defaults = {
            "name": "Test Competitor",
            "domain": "competitor.com",
            "industry": "Technology"
        }
        defaults.update(kwargs)
        return Competitor(**defaults)
```

### Fixtures
Organize fixtures by scope:

```python
@pytest.fixture(scope="session")
def database_url():
    """Session-scoped database URL."""
    return "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="function")
def clean_db(db_session):
    """Function-scoped clean database."""
    yield db_session
    # Cleanup after each test
```

---

## Performance Testing

### Benchmarks
```python
@pytest.mark.slow
def test_report_generation_performance(benchmark):
    def generate():
        return ReportGenerator().generate(competitor_id=1)

    result = benchmark(generate)
    assert benchmark.stats.mean < 5.0  # Max 5 seconds
```

### Load Testing
```python
@pytest.mark.slow
@pytest.mark.asyncio
async def test_concurrent_requests():
    tasks = [
        client.get("/api/v1/gnews/search?query=test")
        for _ in range(100)
    ]
    results = await asyncio.gather(*tasks)

    success_count = sum(1 for r in results if r.status_code == 200)
    assert success_count >= 95  # 95% success rate
```
