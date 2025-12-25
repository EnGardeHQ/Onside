from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import sys
from datetime import datetime, timedelta, timezone

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.content import Base, Content
from src.models.engagement import EngagementMetrics
from src.auth.models import User, UserRole

SQLALCHEMY_DATABASE_URL = "sqlite:///capilytics.db"

def init_db():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # Create an admin user if it doesn't exist
    admin_user = session.query(User).filter_by(email="admin@example.com").first()
    if not admin_user:
        admin_user = User(
            email="admin@example.com",
            name="Admin User",
            role=UserRole.ADMIN
        )
        admin_user.set_password("admin123")
        session.add(admin_user)
        session.commit()
    
    # Create a test user if it doesn't exist
    test_user = session.query(User).filter_by(email="test@example.com").first()
    if not test_user:
        test_user = User(
            email="test@example.com",
            name="Test User",
            role=UserRole.USER
        )
        test_user.set_password("test123")
        session.add(test_user)
        session.commit()

    # Create test content and metrics
    platforms = ["twitter", "linkedin"]
    metric_types = ["engagement", "reach"]
    
    # Create content for each platform
    for platform in platforms:
        content = Content(
            user_id=admin_user.id,
            title=f"Test {platform.capitalize()} Post",
            content_text=f"This is a test post for {platform}",
            content_type="post",
            content_metadata={"platform": platform},
            created_at=datetime.now(timezone.utc) - timedelta(days=7)
        )
        session.add(content)
        session.commit()

        # Create metrics for the content
        for metric_type in metric_types:
            # Create metrics for the past 7 days
            for day in range(7):
                metric = EngagementMetrics(
                    content_id=content.id,
                    metric_type=metric_type,
                    metric_value=100 + day * 10,  # Increasing values
                    created_at=datetime.now(timezone.utc) - timedelta(days=day)
                )
                session.add(metric)

    session.commit()
    return session

if __name__ == "__main__":
    init_db()
