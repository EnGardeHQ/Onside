#!/bin/bash

# =============================================================================
# OnSide Health Check Script
# =============================================================================
# This script verifies that all services are healthy and running correctly
# Usage: ./health-check.sh [environment]
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENVIRONMENT="${1:-production}"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.prod.yml"
ENV_FILE="${PROJECT_ROOT}/.env.${ENVIRONMENT}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load environment variables
if [ -f "${ENV_FILE}" ]; then
    source "${ENV_FILE}"
fi

API_PORT="${API_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-80}"
FLOWER_PORT="${FLOWER_PORT:-5555}"
MINIO_CONSOLE_PORT="${MINIO_CONSOLE_PORT:-9001}"

echo "=========================================="
echo "  OnSide Health Check"
echo "  Environment: ${ENVIRONMENT}"
echo "=========================================="
echo ""

# -----------------------------------------------------------------------------
# Check if services are running
# -----------------------------------------------------------------------------
check_service_running() {
    local service=$1
    local status=$(docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps -q ${service} 2>/dev/null)
    
    if [ -z "$status" ]; then
        echo -e "${RED}✗${NC} ${service}: Not running"
        return 1
    else
        local health=$(docker inspect --format='{{.State.Health.Status}}' $(docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps -q ${service}) 2>/dev/null || echo "N/A")
        if [ "$health" = "healthy" ] || [ "$health" = "N/A" ]; then
            echo -e "${GREEN}✓${NC} ${service}: Running (Health: ${health})"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} ${service}: Running but unhealthy (Health: ${health})"
            return 1
        fi
    fi
}

# -----------------------------------------------------------------------------
# Check HTTP endpoints
# -----------------------------------------------------------------------------
check_http_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓${NC} ${name}: Responding (HTTP ${response})"
        return 0
    else
        echo -e "${RED}✗${NC} ${name}: Not responding (HTTP ${response})"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Run checks
# -----------------------------------------------------------------------------
echo "Checking Docker containers..."
echo ""

FAILED=0

# Check services
check_service_running "onside-db-prod" || FAILED=$((FAILED + 1))
check_service_running "onside-redis-prod" || FAILED=$((FAILED + 1))
check_service_running "onside-minio-prod" || FAILED=$((FAILED + 1))
check_service_running "onside-api-prod" || FAILED=$((FAILED + 1))
check_service_running "onside-frontend" || FAILED=$((FAILED + 1))
check_service_running "onside-celery-worker" || FAILED=$((FAILED + 1))
check_service_running "onside-celery-beat" || FAILED=$((FAILED + 1))
check_service_running "onside-flower" || FAILED=$((FAILED + 1))

echo ""
echo "Checking HTTP endpoints..."
echo ""

# Check endpoints
check_http_endpoint "Frontend" "http://localhost:${FRONTEND_PORT}/health" || FAILED=$((FAILED + 1))
check_http_endpoint "API Health" "http://localhost:${API_PORT}/health" || FAILED=$((FAILED + 1))
check_http_endpoint "API Docs" "http://localhost:${API_PORT}/docs" || FAILED=$((FAILED + 1))
check_http_endpoint "Flower" "http://localhost:${FLOWER_PORT}" || FAILED=$((FAILED + 1))
check_http_endpoint "MinIO Console" "http://localhost:${MINIO_CONSOLE_PORT}/minio/health/live" || FAILED=$((FAILED + 1))

echo ""
echo "Checking database connection..."
echo ""

# Check database
DB_CHECK=$(docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T onside-db-prod pg_isready -U ${POSTGRES_USER} 2>/dev/null || echo "failed")
if [[ "$DB_CHECK" == *"accepting connections"* ]]; then
    echo -e "${GREEN}✓${NC} PostgreSQL: Accepting connections"
else
    echo -e "${RED}✗${NC} PostgreSQL: Not accepting connections"
    FAILED=$((FAILED + 1))
fi

# Check Redis
REDIS_CHECK=$(docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T onside-redis-prod redis-cli ping 2>/dev/null || echo "failed")
if [ "$REDIS_CHECK" = "PONG" ]; then
    echo -e "${GREEN}✓${NC} Redis: Responding"
else
    echo -e "${RED}✗${NC} Redis: Not responding"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All health checks passed!${NC}"
    echo "=========================================="
    exit 0
else
    echo -e "${RED}${FAILED} health check(s) failed!${NC}"
    echo "=========================================="
    exit 1
fi
