"""Migrate data from SQLite to PostgreSQL"""
import os
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import sys
from datetime import datetime, timezone
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from src.database.migrations.create_market_tables import metadata

# Load environment variables
load_dotenv()

def migrate():
    # Source (SQLite) database
    sqlite_url = "sqlite:///./capilytics.db"
    sqlite_engine = create_engine(sqlite_url)
    
    # Create tables in SQLite first
    metadata.create_all(sqlite_engine)
    
    # Target (PostgreSQL) database
    postgres_url = os.getenv("DATABASE_URL")
    postgres_engine = create_engine(postgres_url)
    
    # Create tables in PostgreSQL
    metadata.create_all(postgres_engine)
    
    # Create sessions
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    postgres_session = PostgresSession()
    
    try:
        # Clean up existing data
        postgres_session.execute(text("TRUNCATE competitors, competitor_content, market_tags, market_segments CASCADE"))
        postgres_session.commit()
        
        sqlite_session.execute(text("DELETE FROM competitors"))
        sqlite_session.execute(text("DELETE FROM competitor_content"))
        sqlite_session.execute(text("DELETE FROM market_tags"))
        sqlite_session.execute(text("DELETE FROM market_segments"))
        sqlite_session.commit()
        
        # Insert sample data into SQLite for testing
        current_time = datetime.now(timezone.utc)
        params = {
            "name": "Test Company",
            "domain": "test.com",
            "description": "Test Description",
            "market_share": 0.5,
            "created_at": current_time,
            "updated_at": current_time,
            "meta_data": json.dumps({})
        }
        
        sqlite_session.execute(
            text("""
                INSERT INTO competitors (name, domain, description, market_share, created_at, updated_at, meta_data)
                VALUES (:name, :domain, :description, :market_share, :created_at, :updated_at, :meta_data)
            """),
            params
        )
        sqlite_session.commit()
        
        # Migrate competitors
        competitors = sqlite_session.execute(text("SELECT * FROM competitors")).fetchall()
        for competitor in competitors:
            postgres_session.execute(
                text("""
                    INSERT INTO competitors (id, name, domain, description, market_share, created_at, updated_at, meta_data)
                    VALUES (:id, :name, :domain, :description, :market_share, :created_at, :updated_at, :meta_data)
                """),
                competitor._asdict()
            )
        
        # Migrate competitor_content
        contents = sqlite_session.execute(text("SELECT * FROM competitor_content")).fetchall()
        for content in contents:
            postgres_session.execute(
                text("""
                    INSERT INTO competitor_content 
                    (id, competitor_id, title, url, content_type, published_date, engagement_metrics, created_at, updated_at)
                    VALUES (:id, :competitor_id, :title, :url, :content_type, :published_date, :engagement_metrics, :created_at, :updated_at)
                """),
                content._asdict()
            )
        
        # Migrate market_tags
        tags = sqlite_session.execute(text("SELECT * FROM market_tags")).fetchall()
        for tag in tags:
            postgres_session.execute(
                text("""
                    INSERT INTO market_tags (id, name, description, created_at)
                    VALUES (:id, :name, :description, :created_at)
                """),
                tag._asdict()
            )
        
        # Migrate market_segments
        segments = sqlite_session.execute(text("SELECT * FROM market_segments")).fetchall()
        for segment in segments:
            postgres_session.execute(
                text("""
                    INSERT INTO market_segments (id, name, description, created_at)
                    VALUES (:id, :name, :description, :created_at)
                """),
                segment._asdict()
            )
        
        postgres_session.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        postgres_session.rollback()
    finally:
        sqlite_session.close()
        postgres_session.close()

if __name__ == "__main__":
    migrate()
