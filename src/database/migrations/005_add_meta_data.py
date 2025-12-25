"""Add meta_data column to competitor_content table"""
from sqlalchemy import text
from src.database.config import engine

def migrate():
    """Add meta_data column to competitor_content table"""
    with engine.connect() as conn:
        # Add meta_data column if it doesn't exist
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name='competitor_content' AND column_name='meta_data') THEN
                    ALTER TABLE competitor_content ADD COLUMN meta_data JSONB;
                END IF;
            END $$;
        """))
        conn.commit()

if __name__ == "__main__":
    migrate()
