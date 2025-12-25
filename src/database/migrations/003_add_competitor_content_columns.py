"""Add missing columns to competitor_content table"""
from sqlalchemy import text
from src.database.config import engine

def migrate():
    """Add missing columns to competitor_content table"""
    with engine.connect() as conn:
        # Add missing columns if they don't exist
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name='competitor_content' AND column_name='publish_date') THEN
                    ALTER TABLE competitor_content ADD COLUMN publish_date TIMESTAMP WITH TIME ZONE;
                END IF;

                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name='competitor_content' AND column_name='discovered_date') THEN
                    ALTER TABLE competitor_content ADD COLUMN discovered_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
                END IF;

                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name='competitor_content' AND column_name='last_updated') THEN
                    ALTER TABLE competitor_content ADD COLUMN last_updated TIMESTAMP WITH TIME ZONE;
                END IF;
            END $$;
        """))
        conn.commit()

if __name__ == "__main__":
    migrate()
