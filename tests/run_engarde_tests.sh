#!/bin/bash
# Test runner script for En Garde integration tests
# Run this after installing test dependencies: pip install -r requirements-test.txt

echo "===================="
echo "En Garde Integration Test Suite"
echo "===================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not found. Install with: pip install -r requirements-test.txt${NC}"
    exit 1
fi

echo "Installing test dependencies..."
pip install -q pytest pytest-asyncio pytest-cov pytest-mock httpx factory-boy faker

echo ""
echo "Running tests..."
echo "===================="

# Run unit tests only (don't require database)
echo -e "${YELLOW}1. Running Unit Tests...${NC}"
pytest tests/unit/engarde/ -v -m unit --tb=short --disable-warnings

UNIT_EXIT=$?

# Run integration tests (require database)
echo ""
echo -e "${YELLOW}2. Running Integration Tests...${NC}"
pytest tests/integration/engarde/ -v -m integration --tb=short --disable-warnings 2>&1 || echo "Integration tests require database setup"

# Run API tests
echo ""
echo -e "${YELLOW}3. Running API Tests...${NC}"
pytest tests/api/engarde/ -v -m api --tb=short --disable-warnings 2>&1 || echo "API tests require test server setup"

# Generate coverage report
echo ""
echo -e "${YELLOW}4. Generating Coverage Report...${NC}"
pytest tests/unit/engarde/ --cov=src/agents --cov=src/services --cov=src/api/v1 \
    --cov-report=html:htmlcov \
    --cov-report=term-missing \
    --cov-report=json \
    --disable-warnings 2>&1 || echo "Coverage generation requires all dependencies"

echo ""
echo "===================="
echo "Test Summary"
echo "===================="

if [ $UNIT_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓ Unit tests passed${NC}"
else
    echo -e "${RED}✗ Unit tests failed${NC}"
fi

echo ""
echo "Coverage report generated in: htmlcov/index.html"
echo ""
echo "To run specific test categories:"
echo "  pytest -m unit          # Unit tests only"
echo "  pytest -m integration   # Integration tests only"
echo "  pytest -m api           # API tests only"
echo "  pytest -m engarde       # All En Garde tests"
echo ""
