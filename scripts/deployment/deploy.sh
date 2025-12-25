#!/bin/bash

# =============================================================================
# OnSide Deployment Script
# =============================================================================
# This script handles the deployment of the OnSide application to production
# Usage: ./deploy.sh [environment]
# Example: ./deploy.sh production
# =============================================================================

set -e  # Exit on any error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENVIRONMENT="${1:-production}"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.prod.yml"
ENV_FILE="${PROJECT_ROOT}/.env.${ENVIRONMENT}"
BACKUP_DIR="${PROJECT_ROOT}/backups"
LOG_FILE="${PROJECT_ROOT}/logs/deployment-$(date +%Y%m%d-%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# -----------------------------------------------------------------------------
# Logging Functions
# -----------------------------------------------------------------------------
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "${LOG_FILE}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "${LOG_FILE}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "${LOG_FILE}"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "${LOG_FILE}"
}

# -----------------------------------------------------------------------------
# Pre-deployment Checks
# -----------------------------------------------------------------------------
preflight_checks() {
    log_info "Running pre-flight checks..."
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        log_error "Do not run this script as root"
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if environment file exists
    if [ ! -f "${ENV_FILE}" ]; then
        log_error "Environment file not found: ${ENV_FILE}"
        log_info "Please create ${ENV_FILE} from .env.production.example"
        exit 1
    fi
    
    # Check if compose file exists
    if [ ! -f "${COMPOSE_FILE}" ]; then
        log_error "Compose file not found: ${COMPOSE_FILE}"
        exit 1
    fi
    
    # Check for required environment variables
    log_info "Validating environment variables..."
    source "${ENV_FILE}"
    
    required_vars=(
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "SECRET_KEY"
        "MINIO_ACCESS_KEY"
        "MINIO_SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            log_error "Required environment variable ${var} is not set"
            exit 1
        fi
        
        # Check if placeholder values are still present
        if [[ "${!var}" == *"CHANGE_ME"* ]]; then
            log_error "Environment variable ${var} contains placeholder value"
            exit 1
        fi
    done
    
    log_success "Pre-flight checks passed"
}

# -----------------------------------------------------------------------------
# Backup Database
# -----------------------------------------------------------------------------
backup_database() {
    log_info "Creating database backup..."
    
    mkdir -p "${BACKUP_DIR}"
    
    BACKUP_FILE="${BACKUP_DIR}/backup-$(date +%Y%m%d-%H%M%S).sql"
    
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T onside-db-prod \
        pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" > "${BACKUP_FILE}" 2>/dev/null || {
        log_warning "Could not create database backup (database may not be running yet)"
        return 0
    }
    
    # Compress backup
    gzip "${BACKUP_FILE}"
    
    log_success "Database backup created: ${BACKUP_FILE}.gz"
}

# -----------------------------------------------------------------------------
# Build and Deploy
# -----------------------------------------------------------------------------
build_images() {
    log_info "Building Docker images..."
    
    cd "${PROJECT_ROOT}"
    
    # Build backend
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build --no-cache onside-api
    
    # Build frontend
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build --no-cache onside-frontend
    
    # Build workers
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build --no-cache onside-celery-worker
    
    log_success "Docker images built successfully"
}

pull_images() {
    log_info "Pulling required Docker images..."
    
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" pull \
        onside-db onside-redis onside-minio onside-playwright
    
    log_success "Images pulled successfully"
}

deploy_services() {
    log_info "Deploying services..."
    
    cd "${PROJECT_ROOT}"
    
    # Stop existing services gracefully
    log_info "Stopping existing services..."
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" down --timeout 30
    
    # Start services
    log_info "Starting services..."
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d
    
    log_success "Services started"
}

# -----------------------------------------------------------------------------
# Database Migrations
# -----------------------------------------------------------------------------
run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 10
    
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T onside-api-prod \
        alembic upgrade head || {
        log_error "Database migration failed"
        exit 1
    }
    
    log_success "Database migrations completed"
}

# -----------------------------------------------------------------------------
# Health Checks
# -----------------------------------------------------------------------------
health_checks() {
    log_info "Running health checks..."
    
    # Run the health check script
    bash "${SCRIPT_DIR}/health-check.sh" "${ENVIRONMENT}" || {
        log_error "Health checks failed"
        exit 1
    }
    
    log_success "All health checks passed"
}

# -----------------------------------------------------------------------------
# Post-deployment Tasks
# -----------------------------------------------------------------------------
post_deployment() {
    log_info "Running post-deployment tasks..."
    
    # Clean up old Docker images
    log_info "Cleaning up old Docker images..."
    docker image prune -f
    
    # Show service status
    log_info "Service status:"
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps
    
    log_success "Post-deployment tasks completed"
}

# -----------------------------------------------------------------------------
# Main Deployment Flow
# -----------------------------------------------------------------------------
main() {
    log_info "Starting deployment for environment: ${ENVIRONMENT}"
    log_info "Project root: ${PROJECT_ROOT}"
    log_info "Compose file: ${COMPOSE_FILE}"
    log_info "Environment file: ${ENV_FILE}"
    
    echo ""
    echo "==========================================="
    echo "  OnSide Production Deployment"
    echo "  Environment: ${ENVIRONMENT}"
    echo "==========================================="
    echo ""
    
    # Confirm deployment
    read -p "Are you sure you want to deploy to ${ENVIRONMENT}? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_warning "Deployment cancelled by user"
        exit 0
    fi
    
    # Execute deployment steps
    preflight_checks
    backup_database
    pull_images
    build_images
    deploy_services
    run_migrations
    health_checks
    post_deployment
    
    echo ""
    echo "==========================================="
    log_success "Deployment completed successfully!"
    echo "==========================================="
    echo ""
    echo "Deployment log: ${LOG_FILE}"
    echo "Frontend: http://localhost:${FRONTEND_PORT:-80}"
    echo "API: http://localhost:${API_PORT:-8000}"
    echo "API Docs: http://localhost:${API_PORT:-8000}/docs"
    echo "Flower: http://localhost:${FLOWER_PORT:-5555}"
    echo "MinIO Console: http://localhost:${MINIO_CONSOLE_PORT:-9001}"
    echo ""
}

# -----------------------------------------------------------------------------
# Error Handler
# -----------------------------------------------------------------------------
trap 'log_error "Deployment failed at line $LINENO. Check ${LOG_FILE} for details."' ERR

# Run main function
main "$@"
