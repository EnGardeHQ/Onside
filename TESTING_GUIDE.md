# OnSide Testing Guide

This guide provides comprehensive information on running, writing, and maintaining tests for the OnSide platform.

## Table of Contents

- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Performance Testing](#performance-testing)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set up test database
export DATABASE_URL="postgresql://postgres:password@localhost:5432/onside_test"
export TESTING=true

# Run migrations
alembic upgrade head
```

### Run All Tests

```bash
# Run all tests with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing -v

# View coverage report
open htmlcov/index.html
```

### Run Specific Test Suites

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# API tests only
pytest tests/api/ -v

# Performance tests only
pytest tests/performance/ -v -m performance

# Specific test file
pytest tests/services/test_gnews_service.py -v

# Specific test function
pytest tests/services/test_gnews_service.py::TestGNewsService::test_search_news -v
```

---

## Test Structure

### Directory Organization

```
tests/
├── conftest.py                 # Global fixtures and configuration
├── unit/                       # Unit tests (isolated, mocked)
│   ├── services/
│   │   ├── i18n/
│   │   └── ...
│   └── repositories/
├── integration/                # Integration tests (real dependencies)
│   ├── services/
│   └── ...
├── api/                        # API endpoint tests
│   ├── v1/
│   └── routes/
├── performance/                # Performance and load tests
│   ├── benchmarks/            # Stored performance baselines
│   └── ...
├── models/                     # Model validation tests
└── repositories/               # Repository layer tests
```

### File Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName><Feature>`
- Test functions: `test_<method>_<scenario>_<expected_result>`

Example:
```python
# File: tests/services/test_gnews_service.py
class TestGNewsServiceSearch:
    def test_search_with_valid_query_returns_articles(self):
        pass
```

---

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with extra verbose output (show all output)
pytest tests/ -vv -s

# Run and stop on first failure
pytest tests/ -x

# Run and show only failures
pytest tests/ -q

# Run tests matching a pattern
pytest tests/ -k "search"
```

### Coverage Analysis

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html

# Coverage with missing lines
pytest tests/ --cov=src --cov-report=term-missing

# Coverage with threshold enforcement
pytest tests/ --cov=src --cov-fail-under=90

# Coverage for specific module
pytest tests/ --cov=src.services.external_api
```

### Parallel Execution

```bash
# Auto-detect CPU cores and run in parallel
pytest tests/ -n auto

# Run with specific number of workers
pytest tests/ -n 4

# Parallel with coverage
pytest tests/ -n auto --cov=src
```

### Test Markers

```bash
# Run only unit tests
pytest tests/ -m unit

# Run only integration tests
pytest tests/ -m integration

# Run only performance tests
pytest tests/ -m performance

# Run slow tests
pytest tests/ -m slow

# Exclude slow tests
pytest tests/ -m "not slow"

# Combine markers
pytest tests/ -m "unit and not slow"
```

### Filtering Tests

```bash
# By test name pattern
pytest tests/ -k "test_search"

# By class name
pytest tests/ -k "TestGNewsService"

# By file path
pytest tests/services/

# Multiple patterns
pytest tests/ -k "search or create"
```

---

## Writing Tests

### BDD/TDD Test Structure

All tests should follow the Given-When-Then pattern:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestDomainRepository:
    """
    Feature: Domain Repository Operations
    As a developer,
    I want to perform domain CRUD operations,
    So I can manage domain data reliably.
    """

    @pytest.mark.asyncio
    async def test_get_by_id_returns_domain_when_exists(self, test_db):
        """
        Given a domain repository with an existing domain
        When I retrieve the domain by ID
        Then the correct domain should be returned
        """
        # Arrange - Set up test data and mocks
        repo = DomainRepository(test_db)
        expected_domain = Domain(id=1, domain="example.com")
        test_db.execute = AsyncMock(return_value=mock_result(expected_domain))

        # Act - Perform the action being tested
        result = await repo.get_by_id(1)

        # Assert - Verify the expected outcome
        assert result is not None
        assert result.id == 1
        assert result.domain == "example.com"
```

### Unit Test Best Practices

1. **Test Isolation**: Each test should be independent
```python
@pytest.fixture
def clean_database(test_db):
    """Ensure clean state for each test."""
    yield test_db
    # Rollback changes after test
```

2. **Mock External Dependencies**
```python
from unittest.mock import AsyncMock, patch

@patch('src.services.gnews_service.httpx.AsyncClient')
async def test_api_call(mock_client):
    mock_client.return_value.get = AsyncMock(return_value=mock_response)
    # Test code here
```

3. **Test Both Success and Failure Paths**
```python
def test_successful_operation(self):
    # Test happy path
    pass

def test_operation_with_invalid_input_raises_error(self):
    with pytest.raises(ValidationError):
        # Test error path
        pass
```

4. **Use Descriptive Test Names**
```python
# Good
def test_search_with_empty_query_raises_validation_error(self):
    pass

# Bad
def test_search_error(self):
    pass
```

### Async Testing

```python
import pytest

@pytest.mark.asyncio
async def test_async_function(self):
    """Test async functions properly."""
    result = await async_operation()
    assert result == expected_value

# Mock async functions
from unittest.mock import AsyncMock

@pytest.fixture
def mock_async_service():
    service = AsyncMock()
    service.fetch_data = AsyncMock(return_value={"data": "value"})
    return service
```

### Fixtures

```python
# Scope levels: function (default), class, module, session

@pytest.fixture(scope="function")
def test_user():
    """Create a test user for each test."""
    return User(id=1, email="test@example.com")

@pytest.fixture(scope="session")
def database_connection():
    """Create database connection once per test session."""
    conn = create_connection()
    yield conn
    conn.close()

# Fixture with cleanup
@pytest.fixture
def temp_file():
    file = create_temp_file()
    yield file
    file.cleanup()
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("Test", "TEST"),
])
def test_uppercase(input, expected):
    assert input.upper() == expected

@pytest.mark.parametrize("query,max_results,expected_count", [
    ("tech", 10, 10),
    ("news", 5, 5),
    ("python", 20, 20),
])
async def test_search_variations(query, max_results, expected_count):
    results = await search_service.search(query, max_results)
    assert len(results) == expected_count
```

---

## Performance Testing

### Running Performance Tests

```bash
# Run all performance tests
pytest tests/performance/ -v -m performance

# Run specific performance test
pytest tests/performance/test_performance_comprehensive.py::TestAPIPerformance -v

# Generate performance report
pytest tests/performance/ -v -m performance
cat tests/performance/benchmarks/performance_report.md
```

### Performance Test Structure

```python
from tests.performance.test_performance_comprehensive import (
    PerformanceMonitor,
    run_performance_benchmark,
    assert_performance_threshold
)

@pytest.mark.asyncio
@pytest.mark.performance
async def test_endpoint_performance(self, test_client):
    """
    Scenario: API endpoint performance
    Given a performance benchmark
    When I measure endpoint response time
    Then it should meet performance thresholds
    """
    @run_performance_benchmark
    async def benchmark_operation(client):
        response = await client.get("/api/endpoint")
        return response

    metrics = await benchmark_operation(test_client)
    assert_performance_threshold(metrics, 500, "Endpoint Name")
```

### Performance Thresholds

Current thresholds defined in `/tests/performance/test_performance_comprehensive.py`:

- API Response Time: <500ms
- Report Generation: <12s
- Database Query: <100ms
- Concurrent Success Rate: >95%

### Viewing Performance Baselines

```bash
# View stored baselines
cat tests/performance/benchmarks/performance_metrics.json

# View performance report
cat tests/performance/benchmarks/performance_report.md

# Clear baselines (re-establish)
rm tests/performance/benchmarks/performance_metrics.json
```

---

## CI/CD Integration

### GitHub Actions Workflow

Tests run automatically on:
- Push to `main` or `develop`
- Pull request creation
- Manual trigger via GitHub UI

### Workflow Stages

1. **Unit Tests** - Fast isolated tests with mocks
2. **Integration Tests** - Tests with real database
3. **API Tests** - Full stack endpoint tests
4. **Performance Tests** - Baseline and regression checks
5. **Quality Gates** - Linting, type checking, security

### Local CI Simulation

```bash
# Run all tests as CI would
pytest tests/ --cov=src --cov-fail-under=90 -n auto -v

# Run quality checks
flake8 src/ tests/ --max-line-length=100
black src/ tests/ --check
mypy src/ --ignore-missing-imports
```

### Coverage Reporting

Coverage is automatically uploaded to Codecov on CI runs:
- View at: https://codecov.io/gh/your-org/onside
- PR comments include coverage changes
- Branch protection requires 90% coverage

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Error: ModuleNotFoundError
# Solution: Ensure PYTHONPATH includes src/
export PYTHONPATH="${PYTHONPATH}:${PWD}"
pytest tests/
```

#### 2. Database Connection Errors

```bash
# Error: could not connect to database
# Solution: Verify DATABASE_URL and database is running
export DATABASE_URL="postgresql://user:pass@localhost:5432/onside_test"
docker-compose up -d postgres
```

#### 3. Async Test Warnings

```bash
# Warning: PytestUnraisableExceptionWarning
# Solution: Ensure pytest-asyncio is installed and configured
pip install pytest-asyncio
# Add to pytest.ini:
# asyncio_mode = auto
```

#### 4. Coverage Not Measuring

```bash
# Issue: Coverage shows 0%
# Solution: Ensure pytest-cov is installed
pip install pytest-cov

# Run with explicit source
pytest tests/ --cov=src --cov-report=term
```

#### 5. Slow Test Execution

```bash
# Issue: Tests take too long
# Solution: Use parallel execution
pytest tests/ -n auto

# Skip slow tests during development
pytest tests/ -m "not slow"
```

### Debug Mode

```bash
# Run with debugger on failure
pytest tests/ --pdb

# Show full output
pytest tests/ -vv -s

# Show local variables on failure
pytest tests/ -l

# Show captured logs
pytest tests/ --log-cli-level=DEBUG
```

### Cleaning Test Environment

```bash
# Remove test database
dropdb onside_test
createdb onside_test

# Clear pytest cache
pytest --cache-clear

# Remove coverage data
rm .coverage
rm -rf htmlcov/

# Remove performance baselines
rm -rf tests/performance/benchmarks/
```

---

## Test Checklist

Before submitting code, ensure:

- [ ] All tests pass locally
- [ ] Code coverage >= 90% for new code
- [ ] No flake8 linting errors
- [ ] Code formatted with black
- [ ] Type hints added for new functions
- [ ] Docstrings added in BDD format
- [ ] Performance tests added for critical paths
- [ ] Integration tests added for API changes
- [ ] No print statements or debug code
- [ ] All async functions properly awaited
- [ ] Fixtures properly scoped
- [ ] Mocks cleaned up after tests

---

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [OnSide Testing Standards](/.claude/testing-standards.md)
- [OnSide Architecture](/.claude/architecture.md)

---

## Getting Help

If you encounter issues not covered in this guide:

1. Check existing test examples in the codebase
2. Review error messages carefully
3. Search pytest documentation
4. Ask in team chat or create an issue
5. Review CI/CD logs for additional context

---

**Last Updated:** December 22, 2025
**Maintained By:** QA Team
