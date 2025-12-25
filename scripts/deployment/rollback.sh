#!/bin/bash

# =============================================================================
# OnSide Rollback Script
# =============================================================================
# This script handles rollback to a previous deployment state
# Usage: ./rollback.sh [environment] [backup-directory]
# Example: ./rollback.sh production backups/20231223-120000
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENVIRONMENT="${1:-production}"
BACKUP_DIR="${2:-}"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.prod.yml"
ENV_FILE="${PROJECT_ROOT}/.env.${ENVIRONMENT}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}=========================================="
echo "  OnSide Rollback Script"
echo "  Environment: ${ENVIRONMENT}"
echo "==========================================${NC}"
echo ""
echo -e "${YELLOW}WARNING: This will restore data from a backup and may cause data loss!${NC}"
echo ""

# Load environment variables
if [ -f "${ENV_FILE}" ]; then
    source "${ENV_FILE}"
fi

# -----------------------------------------------------------------------------
# List available backups
# -----------------------------------------------------------------------------
list_backups() {
    echo "Available backups:"
    echo ""
    
    if [ -d "${PROJECT_ROOT}/backups" ]; then
        ls -lht "${PROJECT_ROOT}/backups" | grep "^d" | awk '{print $9, "(" $6, $7, $8 ")"}'
    else
        echo "No backups found"
    fi
    
    echo ""
}

# -----------------------------------------------------------------------------
# Validate backup directory
# -----------------------------------------------------------------------------
validate_backup() {
    if [ -z "${BACKUP_DIR}" ]; then
        echo -e "${RED}[ERROR]${NC} No backup directory specified"
        echo ""
        list_backups
        echo "Usage: $0 ${ENVIRONMENT} <backup-directory>"
        exit 1
    fi
    
    # Handle relative paths
    if [[ ! "${BACKUP_DIR}" = /* ]]; then
        BACKUP_DIR="${PROJECT_ROOT}/${BACKUP_DIR}"
    fi
    
    if [ ! -d "${BACKUP_DIR}" ]; then
        echo -e "${RED}[ERROR]${NC} Backup directory not found: ${BACKUP_DIR}"
        echo ""
        list_backups
        exit 1
    fi
    
    echo -e "${BLUE}[INFO]${NC} Using backup: ${BACKUP_DIR}"
    
    # Show backup manifest if available
    if [ -f "${BACKUP_DIR}/manifest.txt" ]; then
        echo ""
        echo "Backup Manifest:"
        echo "================"
        cat "${BACKUP_DIR}/manifest.txt"
        echo ""
    fi
}

# -----------------------------------------------------------------------------
# Confirm rollback
# -----------------------------------------------------------------------------
confirm_rollback() {
    echo -e "${YELLOW}This operation will:${NC}"
    echo "1. Stop all running services"
    echo "2. Restore database from backup"
    echo "3. Restore Redis data from backup"
    echo "4. Restore MinIO data from backup"
    echo "5. Restart all services"
    echo ""
    echo -e "${RED}Current data will be overwritten!${NC}"
    echo ""
    
    read -p "Are you absolutely sure you want to proceed? (yes/no): " -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${BLUE}[INFO]${NC} Rollback cancelled"
        exit 0
    fi
}

# -----------------------------------------------------------------------------
# Create safety backup
# -----------------------------------------------------------------------------
create_safety_backup() {
    echo -e "${BLUE}[INFO]${NC} Creating safety backup before rollback..."
    
    bash "${SCRIPT_DIR}/backup.sh" "${ENVIRONMENT}" "full" || {
        echo -e "${YELLOW}[WARNING]${NC} Could not create safety backup"
        read -p "Continue anyway? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            exit 1
        fi
    }
}

# -----------------------------------------------------------------------------
# Stop services
# -----------------------------------------------------------------------------
stop_services() {
    echo -e "${BLUE}[INFO]${NC} Stopping services..."
    
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" down --timeout 30
    
    echo -e "${GREEN}[SUCCESS]${NC} Services stopped"
}

# -----------------------------------------------------------------------------
# Restore database
# -----------------------------------------------------------------------------
restore_database() {
    echo -e "${BLUE}[INFO]${NC} Restoring database..."
    
    local db_backup=$(find "${BACKUP_DIR}" -name "database.sql.gz" | head -1)
    
    if [ -z "${db_backup}" ]; then
        echo -e "${YELLOW}[WARNING]${NC} No database backup found in ${BACKUP_DIR}"
        return 0
    fi
    
    # Start only database service
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d onside-db-prod
    
    # Wait for database to be ready
    echo "Waiting for database to be ready..."
    sleep 10
    
    # Drop and recreate database
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T onside-db-prod \
        psql -U "${POSTGRES_USER}" -c "DROP DATABASE IF EXISTS ${POSTGRES_DB}_old;" || true
    
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T onside-db-prod \
        psql -U "${POSTGRES_USER}" -c "ALTER DATABASE ${POSTGRES_DB} RENAME TO ${POSTGRES_DB}_old;" || true
    
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T onside-db-prod \
        psql -U "${POSTGRES_USER}" -c "CREATE DATABASE ${POSTGRES_DB};"
    
    # Restore backup
    gunzip -c "${db_backup}" > /tmp/restore.sql
    
    docker cp /tmp/restore.sql $(docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps -q onside-db-prod):/tmp/
    
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T onside-db-prod \
        pg_restore -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -v /tmp/restore.sql || {
        echo -e "${RED}[ERROR]${NC} Database restore failed"
        # Restore old database
        docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T onside-db-prod \
            psql -U "${POSTGRES_USER}" -c "DROP DATABASE ${POSTGRES_DB};"
        docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T onside-db-prod \
            psql -U "${POSTGRES_USER}" -c "ALTER DATABASE ${POSTGRES_DB}_old RENAME TO ${POSTGRES_DB};"
        exit 1
    }
    
    # Clean up old database
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T onside-db-prod \
        psql -U "${POSTGRES_USER}" -c "DROP DATABASE IF EXISTS ${POSTGRES_DB}_old;"
    
    rm -f /tmp/restore.sql
    
    echo -e "${GREEN}[SUCCESS]${NC} Database restored"
}

# -----------------------------------------------------------------------------
# Restore Redis
# -----------------------------------------------------------------------------
restore_redis() {
    echo -e "${BLUE}[INFO]${NC} Restoring Redis data..."
    
    local redis_backup=$(find "${BACKUP_DIR}" -name "redis.rdb.gz" | head -1)
    
    if [ -z "${redis_backup}" ]; then
        echo -e "${YELLOW}[WARNING]${NC} No Redis backup found in ${BACKUP_DIR}"
        return 0
    fi
    
    # Stop Redis if running
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" stop onside-redis-prod || true
    
    # Extract backup
    gunzip -c "${redis_backup}" > /tmp/dump.rdb
    
    # Copy to Redis volume
    docker run --rm \
        -v onside-redis-data-prod:/data \
        -v /tmp:/backup \
        alpine cp /backup/dump.rdb /data/dump.rdb
    
    rm -f /tmp/dump.rdb
    
    echo -e "${GREEN}[SUCCESS]${NC} Redis data restored"
}

# -----------------------------------------------------------------------------
# Restore MinIO
# -----------------------------------------------------------------------------
restore_minio() {
    echo -e "${BLUE}[INFO]${NC} Restoring MinIO data..."
    
    local minio_backup=$(find "${BACKUP_DIR}" -name "minio-data.tar.gz" | head -1)
    
    if [ -z "${minio_backup}" ]; then
        echo -e "${YELLOW}[WARNING]${NC} No MinIO backup found in ${BACKUP_DIR}"
        return 0
    fi
    
    # Stop MinIO if running
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" stop onside-minio-prod || true
    
    # Clear existing data
    docker volume rm onside-minio-data-prod || true
    docker volume create onside-minio-data-prod
    
    # Restore from backup
    docker run --rm \
        -v onside-minio-data-prod:/data \
        -v "$(dirname ${minio_backup}):/backup" \
        alpine sh -c "tar xzf /backup/$(basename ${minio_backup}) -C /data"
    
    echo -e "${GREEN}[SUCCESS]${NC} MinIO data restored"
}

# -----------------------------------------------------------------------------
# Start services
# -----------------------------------------------------------------------------
start_services() {
    echo -e "${BLUE}[INFO]${NC} Starting all services..."
    
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d
    
    echo -e "${GREEN}[SUCCESS]${NC} Services started"
}

# -----------------------------------------------------------------------------
# Run health checks
# -----------------------------------------------------------------------------
run_health_checks() {
    echo -e "${BLUE}[INFO]${NC} Running health checks..."
    
    sleep 15
    
    bash "${SCRIPT_DIR}/health-check.sh" "${ENVIRONMENT}" || {
        echo -e "${YELLOW}[WARNING]${NC} Some health checks failed"
        return 1
    }
}

# -----------------------------------------------------------------------------
# Main rollback flow
# -----------------------------------------------------------------------------
main() {
    validate_backup
    confirm_rollback
    create_safety_backup
    stop_services
    restore_database
    restore_redis
    restore_minio
    start_services
    run_health_checks
    
    echo ""
    echo -e "${GREEN}=========================================="
    echo "  Rollback Complete!"
    echo "==========================================${NC}"
    echo "Restored from: ${BACKUP_DIR}"
    echo ""
    echo "Please verify that all services are functioning correctly."
    echo ""
}

main
