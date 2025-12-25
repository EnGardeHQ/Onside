"""Database Setup Script.

This script creates the necessary database tables for the OnSide application
following Semantic Seed coding standards and Sprint 4 implementation patterns.
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from src.database import Base
from src.auth.models import User, UserRole
from src.models.company import Company
from src.models.competitor import Competitor
from src.models.competitor_metrics import CompetitorMetrics, MetricType, DataSource
from src.models.competitor_content import CompetitorContent
from src.models.report import Report
from src.models.llm_fallback import LLMFallback
from src.models.content import Content, ContentEngagementHistory
from src.models.ai import AIInsight
from src.models.trend import TrendAnalysis
from src.models.engagement import EngagementMetrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/onside"

async def setup_database():
    """Create database tables and set up initial data."""
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        # Create all tables
        async with engine.begin() as conn:
            # Drop all tables with CASCADE to handle dependencies
            # Drop schema and recreate
            await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
            await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Successfully created database tables")
        
        # Create async session
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Create test data
        async with async_session() as session:
            # Create a test user first
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password=pwd_context.hash("testpassword123"),
                name="Test User",
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(test_user)
            await session.commit()
            logger.info("Created test user")
            
            # Create a test company
            company = Company(
                name="Test Company",
                domain="testcompany.com",
                description="A test company",
                user_id=test_user.id
            )
            session.add(company)
            await session.commit()
            logger.info("Created test company")
            
            # Create test competitors
            competitors = [
                Competitor(
                    name="Competitor 1",
                    domain="competitor1.com",
                    description="First test competitor",
                    company_id=company.id
                ),
                Competitor(
                    name="Competitor 2",
                    domain="competitor2.com",
                    description="Second test competitor",
                    company_id=company.id
                )
            ]
            session.add_all(competitors)
            await session.commit()
            
            # Create test metrics
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            # Initialize metrics list for batch insertion
            metrics = []
            
            # Generate test data for each competitor
            for competitor in competitors:
                # Generate 30 days of historical data
                for i in range(30):
                    # Calculate time periods for metrics
                    period_start = now - timedelta(days=i+1)
                    period_end = now - timedelta(days=i)
                    
                    # Add web traffic metrics with enhanced data quality
                    metrics.extend([
                        CompetitorMetrics(
                            competitor_id=competitor.id,
                            metric_type=MetricType.WEB_TRAFFIC,
                            value=1000 + i * 100,
                            metric_date=now - timedelta(days=i),
                            start_date=period_start,
                            end_date=period_end,
                            source=DataSource.GOOGLE_ANALYTICS,
                            data_quality_score=0.95,
                            confidence_score=0.95,
                            meta_data={
                                "page_views": 1500 + i * 150,
                                "unique_visitors": 1000 + i * 100,
                                "bounce_rate": 0.45 - (i * 0.01)
                            }
                        ),
                        # Add social engagement metrics
                        CompetitorMetrics(
                            competitor_id=competitor.id,
                            metric_type=MetricType.SOCIAL_ENGAGEMENT,
                            value=500 + i * 50,
                            metric_date=now - timedelta(days=i),
                            start_date=period_start,
                            end_date=period_end,
                            source=DataSource.SOCIAL_MEDIA,
                            data_quality_score=0.90,
                            confidence_score=0.90,
                            engagement_rate=(25 + i * 0.5) / 100,  # 25-40% engagement rate
                            meta_data={
                                "likes": 300 + i * 30,
                                "shares": 150 + i * 15,
                                "comments": 50 + i * 5
                            }
                        )
                    ])
            session.add_all(metrics)
            await session.commit()
            
            logger.info("Successfully created test data")
            
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(setup_database())
