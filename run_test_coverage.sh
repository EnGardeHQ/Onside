#!/bin/bash

# Test Coverage Report Generator for OnSide Backend
# This script runs all tests and generates comprehensive coverage reports

set -e

echo "========================================="
echo "OnSide Backend Test Coverage Report"
echo "========================================="
echo ""

# Set up environment
export PYTHONPATH=/Users/cope/EnGardeHQ/Onside:$PYTHONPATH
export DB_NAME="onside_test"

# Create test database if it doesn't exist
echo "Setting up test database..."
createdb $DB_NAME 2>/dev/null || echo "Test database already exists"

echo ""
echo "Running tests with coverage..."
echo ""

# Run pytest with coverage
pytest \
  --cov=src/services/web_scraping_service \
  --cov=src/services/link_deduplication_service \
  --cov=src/services/advanced_filtering \
  --cov=src/services/google_custom_search \
  --cov=src/services/youtube_service \
  --cov=src/api/v1/search_history \
  --cov=src/api/v1/email_delivery \
  --cov=src/api/v1/scraping \
  --cov=src/api/v1/link_deduplication \
  --cov=src/api/v1/report_schedules \
  --cov-report=term-missing \
  --cov-report=html:htmlcov \
  --cov-report=json:coverage.json \
  --cov-report=xml:coverage.xml \
  -v \
  tests/services/test_web_scraping_service.py \
  tests/services/test_link_deduplication_service.py \
  tests/services/test_advanced_filtering.py \
  tests/services/test_google_custom_search.py \
  tests/services/test_youtube_service.py \
  tests/api/v1/test_search_history.py

echo ""
echo "========================================="
echo "Coverage Summary"
echo "========================================="
echo ""

# Generate detailed coverage report
python3 <<EOF
import json
import os

# Read coverage data
if os.path.exists('coverage.json'):
    with open('coverage.json', 'r') as f:
        coverage_data = json.load(f)

    print("SERVICE COVERAGE SUMMARY:")
    print("-" * 80)

    services = {
        'Web Scraping Service': 'src/services/web_scraping_service.py',
        'Link Deduplication Service': 'src/services/link_deduplication_service.py',
        'Advanced Filtering Service': 'src/services/advanced_filtering.py',
        'Google Custom Search Service': 'src/services/google_custom_search.py',
        'YouTube Service': 'src/services/youtube_service.py',
    }

    total_coverage = 0
    count = 0

    for name, path in services.items():
        if path in coverage_data.get('files', {}):
            file_data = coverage_data['files'][path]
            summary = file_data['summary']
            percent = summary['percent_covered']
            total_coverage += percent
            count += 1

            print(f"{name:40s} {percent:6.2f}%")
            print(f"  - Lines: {summary['covered_lines']}/{summary['num_statements']}")
            print(f"  - Missing: {summary['missing_lines']}")
            print()

    if count > 0:
        avg_coverage = total_coverage / count
        print("-" * 80)
        print(f"{'AVERAGE SERVICE COVERAGE:':40s} {avg_coverage:6.2f}%")
        print("-" * 80)
        print()

        # Coverage goals
        if avg_coverage >= 95:
            print("✓ EXCELLENT: Coverage exceeds 95% target!")
        elif avg_coverage >= 90:
            print("✓ GOOD: Coverage meets 90% minimum target")
        elif avg_coverage >= 80:
            print("⚠ ACCEPTABLE: Coverage above 80% but below target")
        else:
            print("✗ NEEDS IMPROVEMENT: Coverage below 80%")

    print()
    print("Detailed HTML report generated in: htmlcov/index.html")
    print("Open with: open htmlcov/index.html")
else:
    print("Coverage data not found. Tests may not have run successfully.")
EOF

echo ""
echo "========================================="
echo "Test Execution Complete"
echo "========================================="
