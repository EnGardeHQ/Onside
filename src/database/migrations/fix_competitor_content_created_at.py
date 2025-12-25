"""Add default value for created_at in competitor_content table"""
from sqlalchemy import text

def migrate():
    """Add default value for created_at in competitor_content table"""
    query = text("""
        ALTER TABLE competitor_content
        ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP,
        ALTER COLUMN created_at SET NOT NULL;
    """)
    return query
