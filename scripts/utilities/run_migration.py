"""Run the migration to fix created_at column in competitor_content table"""
from src.database.migrations.fix_competitor_content_created_at import migrate
from src.database.config import engine

if __name__ == "__main__":
    with engine.connect() as conn:
        conn.execute(migrate())
        conn.commit()
