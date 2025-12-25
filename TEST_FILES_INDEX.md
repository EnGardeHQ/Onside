# En Garde Integration Test Files Index

This document provides an index of all test-related files created for the En Garde ↔ Onside integration.

## Configuration Files

| File | Path | Purpose |
|------|------|---------|
| pytest.ini | `/Users/cope/EnGardeHQ/Onside/pytest.ini` | Pytest configuration |
| .coveragerc | `/Users/cope/EnGardeHQ/Onside/.coveragerc` | Coverage settings |
| requirements-test.txt | `/Users/cope/EnGardeHQ/Onside/requirements-test.txt` | Test dependencies |

## Test Fixtures

| File | Path | Lines | Description |
|------|------|-------|-------------|
| brand_analysis_fixtures.py | `/Users/cope/EnGardeHQ/Onside/tests/fixtures/brand_analysis_fixtures.py` | 515 | Sample questionnaires, HTML, SERP data, keywords, competitors |

## Test Mocks

| File | Path | Lines | Description |
|------|------|-------|-------------|
| serp_mock.py | `/Users/cope/EnGardeHQ/Onside/tests/mocks/serp_mock.py` | 263 | Mock SERP API with deterministic results |
| http_mock.py | `/Users/cope/EnGardeHQ/Onside/tests/mocks/http_mock.py` | 212 | Mock HTTP responses for web scraping |

## Unit Tests

| File | Path | Lines | Tests | Coverage Target |
|------|------|-------|-------|----------------|
| test_data_transformer.py | `/Users/cope/EnGardeHQ/Onside/tests/unit/engarde/test_data_transformer.py` | 589 | 65 | >95% |
| test_seo_content_walker_extended.py | `/Users/cope/EnGardeHQ/Onside/tests/unit/engarde/test_seo_content_walker_extended.py` | 518 | 50 | >90% |

## Integration Tests

| File | Path | Lines | Tests | Coverage Target |
|------|------|-------|-------|----------------|
| test_brand_analysis_flow.py | `/Users/cope/EnGardeHQ/Onside/tests/integration/engarde/test_brand_analysis_flow.py` | 297 | 15 | >80% |

## API Tests

| File | Path | Lines | Tests | Coverage Target |
|------|------|-------|-------|----------------|
| test_engarde_endpoints.py | `/Users/cope/EnGardeHQ/Onside/tests/api/engarde/test_engarde_endpoints.py` | 489 | 30 | 100% |

## Documentation

| File | Path | Size | Description |
|------|------|------|-------------|
| ENGARDE_TESTING_SUITE.md | `/Users/cope/EnGardeHQ/Onside/ENGARDE_TESTING_SUITE.md` | 14KB | Comprehensive testing guide |
| TESTING_SUITE_SUMMARY.md | `/Users/cope/EnGardeHQ/Onside/TESTING_SUITE_SUMMARY.md` | 14KB | Executive summary report |
| TESTING_QUICK_START.md | `/Users/cope/EnGardeHQ/Onside/TESTING_QUICK_START.md` | 7.3KB | Quick reference guide |
| TEST_FILES_INDEX.md | `/Users/cope/EnGardeHQ/Onside/TEST_FILES_INDEX.md` | - | This file |

## Scripts

| File | Path | Description |
|------|------|-------------|
| run_engarde_tests.sh | `/Users/cope/EnGardeHQ/Onside/tests/run_engarde_tests.sh` | Automated test runner |

## Supporting Files

| File | Path | Description |
|------|------|-------------|
| __init__.py | `/Users/cope/EnGardeHQ/Onside/tests/fixtures/__init__.py` | Package marker |
| __init__.py | `/Users/cope/EnGardeHQ/Onside/tests/mocks/__init__.py` | Package marker |
| __init__.py | `/Users/cope/EnGardeHQ/Onside/tests/unit/engarde/__init__.py` | Package marker |
| __init__.py | `/Users/cope/EnGardeHQ/Onside/tests/integration/engarde/__init__.py` | Package marker |
| __init__.py | `/Users/cope/EnGardeHQ/Onside/tests/api/engarde/__init__.py` | Package marker |

## Quick Access Commands

### View Test Files
```bash
# List all test files
find /Users/cope/EnGardeHQ/Onside/tests -name "*.py" | grep engarde

# View specific test
cat /Users/cope/EnGardeHQ/Onside/tests/unit/engarde/test_data_transformer.py

# Count lines in all test files
wc -l /Users/cope/EnGardeHQ/Onside/tests/{unit,integration,api}/engarde/*.py
```

### Run Tests
```bash
# Run all En Garde tests
pytest /Users/cope/EnGardeHQ/Onside/tests/ -m engarde -v

# Run specific test file
pytest /Users/cope/EnGardeHQ/Onside/tests/unit/engarde/test_data_transformer.py -v

# Run with coverage
pytest /Users/cope/EnGardeHQ/Onside/tests/ --cov=src --cov-report=html
```

### View Documentation
```bash
# Comprehensive guide
less /Users/cope/EnGardeHQ/Onside/ENGARDE_TESTING_SUITE.md

# Summary report
less /Users/cope/EnGardeHQ/Onside/TESTING_SUITE_SUMMARY.md

# Quick start
less /Users/cope/EnGardeHQ/Onside/TESTING_QUICK_START.md
```

## File Statistics

| Category | Files | Lines | Tests |
|----------|-------|-------|-------|
| Configuration | 3 | ~50 | - |
| Fixtures | 1 | 515 | - |
| Mocks | 2 | 475 | - |
| Unit Tests | 2 | 1,107 | 115 |
| Integration Tests | 1 | 297 | 15 |
| API Tests | 1 | 489 | 30 |
| Documentation | 4 | ~2,000 | - |
| Scripts | 1 | ~100 | - |
| **Total** | **14** | **~4,650** | **160** |

## Directory Structure

```
/Users/cope/EnGardeHQ/Onside/
├── pytest.ini
├── .coveragerc
├── requirements-test.txt
├── ENGARDE_TESTING_SUITE.md
├── TESTING_SUITE_SUMMARY.md
├── TESTING_QUICK_START.md
├── TEST_FILES_INDEX.md
└── tests/
    ├── fixtures/
    │   ├── __init__.py
    │   └── brand_analysis_fixtures.py
    ├── mocks/
    │   ├── __init__.py
    │   ├── serp_mock.py
    │   └── http_mock.py
    ├── unit/
    │   └── engarde/
    │       ├── __init__.py
    │       ├── test_data_transformer.py
    │       └── test_seo_content_walker_extended.py
    ├── integration/
    │   └── engarde/
    │       ├── __init__.py
    │       └── test_brand_analysis_flow.py
    ├── api/
    │   └── engarde/
    │       ├── __init__.py
    │       └── test_engarde_endpoints.py
    └── run_engarde_tests.sh
```

---

**Index Version**: 1.0
**Last Updated**: December 24, 2025
**Total Files Indexed**: 14
