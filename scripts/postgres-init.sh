#!/bin/bash
set -e

# =============================================================================
# PostgreSQL Initialization Script
# =============================================================================
# This script runs on first database initialization
# =============================================================================

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable required extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
    CREATE EXTENSION IF NOT EXISTS "btree_gin";
    CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
    
    -- Create read-only user for reporting
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'onside_readonly') THEN
            CREATE ROLE onside_readonly WITH LOGIN PASSWORD 'readonly_password_change_me';
        END IF;
    END
    \$\$;
    
    -- Grant permissions
    GRANT CONNECT ON DATABASE $POSTGRES_DB TO onside_readonly;
    GRANT USAGE ON SCHEMA public TO onside_readonly;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO onside_readonly;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO onside_readonly;
    
    -- Create performance indexes (will be supplemented by Alembic migrations)
    -- These are general purpose indexes that improve common queries
    
    EOSQL

echo "PostgreSQL initialization completed successfully"
