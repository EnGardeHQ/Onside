"""Test database connection and operations"""
import sys
import os
from datetime import datetime, timezone
import json

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.config import SessionLocal, engine
from src.models.market import Competitor, CompetitorContent, MarketTag
from sqlalchemy import text

def reset_sequences():
    """Reset all sequences in the database"""
    with engine.connect() as conn:
        conn.execute(text("""
            SELECT setval(pg_get_serial_sequence('competitors', 'id'), 
                         COALESCE((SELECT MAX(id) + 1 FROM competitors), 1), false);
            SELECT setval(pg_get_serial_sequence('competitor_content', 'id'), 
                         COALESCE((SELECT MAX(id) + 1 FROM competitor_content), 1), false);
            SELECT setval(pg_get_serial_sequence('market_tags', 'id'), 
                         COALESCE((SELECT MAX(id) + 1 FROM market_tags), 1), false);
        """))
        conn.commit()

def test_database_operations():
    """Test basic database operations"""
    session = SessionLocal()
    try:
        # Reset sequences before testing
        reset_sequences()
        
        # Test 1: Create a competitor
        print("Testing competitor creation...")
        competitor = Competitor(
            name="Test Corp",
            domain="testcorp.com",
            description="A test company",
            market_share=0.15,
            meta_data={"industry": "technology"}
        )
        session.add(competitor)
        session.commit()
        print(f"Created competitor: {competitor.name} (ID: {competitor.id})")

        # Test 2: Read competitor
        print("\nTesting competitor retrieval...")
        retrieved_competitor = session.query(Competitor).filter_by(domain="testcorp.com").first()
        print(f"Retrieved competitor: {retrieved_competitor.name}")
        
        # Test 3: Create competitor content
        print("\nTesting content creation...")
        content = CompetitorContent(
            competitor_id=competitor.id,
            title="Test Article",
            url="https://testcorp.com/article1",
            content_type="blog",
            publish_date=datetime.now(timezone.utc),
            engagement_metrics={"views": 100, "shares": 10}
        )
        session.add(content)
        session.commit()
        print(f"Created content: {content.title} for competitor {competitor.name}")

        # Test 4: Create and associate market tags
        print("\nTesting market tag creation...")
        tag = MarketTag(
            name="AI",
            description="Artificial Intelligence"
        )
        session.add(tag)
        session.commit()
        print(f"Created market tag: {tag.name}")

        # Test 5: Query with joins
        print("\nTesting complex query...")
        result = (
            session.query(Competitor, CompetitorContent)
            .join(CompetitorContent)
            .filter(Competitor.domain == "testcorp.com")
            .first()
        )
        if result:
            comp, cont = result
            print(f"Found content '{cont.title}' for competitor '{comp.name}'")

        print("\nAll tests completed successfully!")

    except Exception as e:
        print(f"Error during testing: {e}")
        session.rollback()
        raise
    finally:
        # Clean up test data
        print("\nCleaning up test data...")
        session.query(CompetitorContent).filter_by(competitor_id=competitor.id).delete()
        session.query(Competitor).filter_by(domain="testcorp.com").delete()
        session.query(MarketTag).filter_by(name="AI").delete()
        session.commit()
        session.close()

if __name__ == "__main__":
    test_database_operations()
