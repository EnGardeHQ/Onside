#!/bin/bash

# =============================================================================
# OnSide Backup Script
# =============================================================================
# This script creates backups of the database and important data
# Usage: ./backup.sh [environment] [backup-type]
# Example: ./backup.sh production full
# Backup types: full, database, volumes
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENVIRONMENT="${1:-production}"
BACKUP_TYPE="${2:-full}"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.prod.yml"
ENV_FILE="${PROJECT_ROOT}/.env.${ENVIRONMENT}"
BACKUP_DIR="${PROJECT_ROOT}/backups/$(date +%Y%m%d-%H%M%S)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Load environment variables
if [ -f "${ENV_FILE}" ]; then
    source "${ENV_FILE}"
fi

echo -e "${BLUE}=========================================="
echo "  OnSide Backup Script"
echo "  Environment: ${ENVIRONMENT}"
echo "  Backup Type: ${BACKUP_TYPE}"
echo "==========================================${NC}"
echo ""

mkdir -p "${BACKUP_DIR}"

# -----------------------------------------------------------------------------
# Backup PostgreSQL Database
# -----------------------------------------------------------------------------
backup_database() {
    echo -e "${BLUE}[INFO]${NC} Backing up PostgreSQL database..."
    
    local db_backup="${BACKUP_DIR}/database.sql"
    
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T onside-db-prod \
        pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
        --format=custom \
        --verbose \
        --file=/tmp/backup.dump 2>&1 || {
        echo -e "${RED}[ERROR]${NC} Database backup failed"
        return 1
    }
    
    docker cp $(docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps -q onside-db-prod):/tmp/backup.dump "${db_backup}"
    
    # Compress backup
    gzip "${db_backup}"
    
    # Get backup size
    local size=$(du -h "${db_backup}.gz" | cut -f1)
    echo -e "${GREEN}[SUCCESS]${NC} Database backup created: ${db_backup}.gz (${size})"
}

# -----------------------------------------------------------------------------
# Backup Redis Data
# -----------------------------------------------------------------------------
backup_redis() {
    echo -e "${BLUE}[INFO]${NC} Backing up Redis data..."
    
    # Trigger Redis save
    docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T onside-redis-prod \
        redis-cli SAVE 2>&1 || {
        echo -e "${RED}[ERROR]${NC} Redis backup failed"
        return 1
    }
    
    # Copy Redis dump
    local redis_backup="${BACKUP_DIR}/redis.rdb"
    docker cp $(docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps -q onside-redis-prod):/data/dump.rdb "${redis_backup}" || {
        echo -e "${RED}[ERROR]${NC} Could not copy Redis dump"
        return 1
    }
    
    gzip "${redis_backup}"
    local size=$(du -h "${redis_backup}.gz" | cut -f1)
    echo -e "${GREEN}[SUCCESS]${NC} Redis backup created: ${redis_backup}.gz (${size})"
}

# -----------------------------------------------------------------------------
# Backup MinIO Data
# -----------------------------------------------------------------------------
backup_minio() {
    echo -e "${BLUE}[INFO]${NC} Backing up MinIO data..."
    
    local minio_backup="${BACKUP_DIR}/minio-data.tar"
    
    # Create tarball of MinIO data volume
    docker run --rm \
        -v onside-minio-data-prod:/data \
        -v "${BACKUP_DIR}:/backup" \
        alpine tar czf /backup/minio-data.tar.gz -C /data . 2>&1 || {
        echo -e "${RED}[ERROR]${NC} MinIO backup failed"
        return 1
    }
    
    local size=$(du -h "${BACKUP_DIR}/minio-data.tar.gz" | cut -f1)
    echo -e "${GREEN}[SUCCESS]${NC} MinIO backup created: ${BACKUP_DIR}/minio-data.tar.gz (${size})"
}

# -----------------------------------------------------------------------------
# Backup Application Logs
# -----------------------------------------------------------------------------
backup_logs() {
    echo -e "${BLUE}[INFO]${NC} Backing up application logs..."
    
    if [ -d "${PROJECT_ROOT}/logs" ]; then
        tar czf "${BACKUP_DIR}/logs.tar.gz" -C "${PROJECT_ROOT}" logs 2>&1
        local size=$(du -h "${BACKUP_DIR}/logs.tar.gz" | cut -f1)
        echo -e "${GREEN}[SUCCESS]${NC} Logs backup created: ${BACKUP_DIR}/logs.tar.gz (${size})"
    else
        echo -e "${BLUE}[INFO]${NC} No logs directory found"
    fi
}

# -----------------------------------------------------------------------------
# Backup Exports
# -----------------------------------------------------------------------------
backup_exports() {
    echo -e "${BLUE}[INFO]${NC} Backing up exports..."
    
    if [ -d "${PROJECT_ROOT}/exports" ]; then
        tar czf "${BACKUP_DIR}/exports.tar.gz" -C "${PROJECT_ROOT}" exports 2>&1
        local size=$(du -h "${BACKUP_DIR}/exports.tar.gz" | cut -f1)
        echo -e "${GREEN}[SUCCESS]${NC} Exports backup created: ${BACKUP_DIR}/exports.tar.gz (${size})"
    else
        echo -e "${BLUE}[INFO]${NC} No exports directory found"
    fi
}

# -----------------------------------------------------------------------------
# Create backup manifest
# -----------------------------------------------------------------------------
create_manifest() {
    local manifest="${BACKUP_DIR}/manifest.txt"
    
    cat > "${manifest}" << MANIFEST
OnSide Backup Manifest
======================
Date: $(date)
Environment: ${ENVIRONMENT}
Backup Type: ${BACKUP_TYPE}
Backup Directory: ${BACKUP_DIR}

Files:
------
$(ls -lh "${BACKUP_DIR}")

Docker Images:
--------------
$(docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" images)

Docker Volumes:
---------------
$(docker volume ls | grep onside)

MANIFEST

    echo -e "${GREEN}[SUCCESS]${NC} Backup manifest created: ${manifest}"
}

# -----------------------------------------------------------------------------
# Cleanup old backups
# -----------------------------------------------------------------------------
cleanup_old_backups() {
    local retention_days=${BACKUP_RETENTION_DAYS:-30}
    
    echo -e "${BLUE}[INFO]${NC} Cleaning up backups older than ${retention_days} days..."
    
    find "${PROJECT_ROOT}/backups" -type d -mtime +${retention_days} -exec rm -rf {} + 2>/dev/null || true
    
    echo -e "${GREEN}[SUCCESS]${NC} Old backups cleaned up"
}

# -----------------------------------------------------------------------------
# Upload to S3 (optional)
# -----------------------------------------------------------------------------
upload_to_s3() {
    if [ -n "${BACKUP_S3_BUCKET:-}" ] && [ -n "${AWS_ACCESS_KEY_ID:-}" ]; then
        echo -e "${BLUE}[INFO]${NC} Uploading backup to S3..."
        
        if command -v aws &> /dev/null; then
            aws s3 sync "${BACKUP_DIR}" "s3://${BACKUP_S3_BUCKET}/backups/$(basename ${BACKUP_DIR})/" \
                --region "${AWS_REGION:-us-east-1}" || {
                echo -e "${RED}[ERROR]${NC} S3 upload failed"
                return 1
            }
            echo -e "${GREEN}[SUCCESS]${NC} Backup uploaded to S3"
        else
            echo -e "${BLUE}[INFO]${NC} AWS CLI not found, skipping S3 upload"
        fi
    fi
}

# -----------------------------------------------------------------------------
# Main backup flow
# -----------------------------------------------------------------------------
main() {
    case "${BACKUP_TYPE}" in
        database)
            backup_database
            ;;
        volumes)
            backup_redis
            backup_minio
            ;;
        full)
            backup_database
            backup_redis
            backup_minio
            backup_logs
            backup_exports
            ;;
        *)
            echo -e "${RED}[ERROR]${NC} Unknown backup type: ${BACKUP_TYPE}"
            echo "Valid types: full, database, volumes"
            exit 1
            ;;
    esac
    
    create_manifest
    cleanup_old_backups
    upload_to_s3
    
    # Calculate total backup size
    local total_size=$(du -sh "${BACKUP_DIR}" | cut -f1)
    
    echo ""
    echo -e "${GREEN}=========================================="
    echo "  Backup Complete!"
    echo "==========================================${NC}"
    echo "Backup location: ${BACKUP_DIR}"
    echo "Total size: ${total_size}"
    echo ""
}

main
