"""Add reports table for report generation tracking"""
from sqlalchemy import text
from src.database.config import engine

def migrate():
    """Create reports table for tracking report generation jobs"""
    with engine.connect() as conn:
        # Create reports table if it doesn't exist
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                type VARCHAR(20) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'queued',
                parameters JSONB,
                result JSONB,
                error_message TEXT,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Create index on user_id for faster lookups
            CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
            
            -- Create index on type for filtering
            CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(type);
            
            -- Create index on status for filtering
            CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
        """))
        conn.commit()

if __name__ == "__main__":
    migrate()
