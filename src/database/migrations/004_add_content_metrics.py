"""Add content_metrics column to competitor_content table"""
from sqlalchemy import text
from src.database.config import engine

def migrate():
    """Add content_metrics column to competitor_content table"""
    with engine.connect() as conn:
        # Add content_metrics column if it doesn't exist
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name='competitor_content' AND column_name='content_metrics') THEN
                    ALTER TABLE competitor_content ADD COLUMN content_metrics JSONB;
                END IF;
            END $$;
        """))
        conn.commit()

if __name__ == "__main__":
    migrate()
