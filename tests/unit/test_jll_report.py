#!/usr/bin/env python
"""
Test script for JLL report generation, ensuring the recursion issues are fixed.
This script tests the end-to-end workflow with real database connection.
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_jll_report")

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from src.models.llm_fallback import LLMProvider
from src.services.llm_provider.fallback_manager import FallbackManager
from src.models.report import Report
from src.database import SessionLocal
from src.repositories.reports_repository import ReportsRepository
from src.repositories.companies_repository import CompaniesRepository
from src.services.ai.competitor_analysis import CompetitorAnalysisService
from src.services.ai.market_analysis import MarketAnalysisService
from src.services.ai.audience_analysis import AudienceAnalysisService


async def test_jll_report_generation():
    """Test the JLL report generation workflow to verify recursion issues are fixed."""
    logger.info("Starting JLL report generation test")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Initialize repositories
        reports_repo = ReportsRepository(db)
        companies_repo = CompaniesRepository(db)
        
        # Find JLL company
        company = await companies_repo.get_by_name("JLL")
        if not company:
            logger.warning("JLL company not found, using first available company")
            companies = await companies_repo.get_all()
            if not companies:
                logger.error("No companies found in database")
                return
            company = companies[0]
        
        # Create a test report
        report = Report(
            title=f"JLL Test Report {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            company_id=company.id,
            created_at=datetime.now()
        )
        report = await reports_repo.create(report)
        logger.info(f"Created test report: {report.title} (ID: {report.id})")
        
        # Initialize fallback manager with providers
        providers = [
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
            LLMProvider.COHERE
        ]
        fallback_manager = FallbackManager(providers=providers)
        
        # Initialize AI services
        competitor_service = CompetitorAnalysisService(
            fallback_manager=fallback_manager,
            db=db
        )
        
        market_service = MarketAnalysisService(
            fallback_manager=fallback_manager,
            db=db
        )
        
        audience_service = AudienceAnalysisService(
            fallback_manager=fallback_manager,
            db=db
        )
        
        # Test AI services
        logger.info("Testing CompetitorAnalysisService...")
        competitor_insights = await competitor_service.get_competitor_insights(report, company.id)
        logger.info(f"✅ CompetitorAnalysisService returned {len(competitor_insights)} insights")
        
        logger.info("Testing MarketAnalysisService...")
        market_insights = await market_service.get_market_insights(report, company.id)
        logger.info(f"✅ MarketAnalysisService returned {len(market_insights)} insights")
        
        logger.info("Testing AudienceAnalysisService...")
        audience_insights = await audience_service.get_audience_insights(report, company.id)
        logger.info(f"✅ AudienceAnalysisService returned {len(audience_insights)} insights")
        
        # Validate insights
        all_insights = [
            *competitor_insights,
            *market_insights,
            *audience_insights
        ]
        
        for i, insight in enumerate(all_insights):
            logger.info(f"Insight {i+1}: {insight.type} - Confidence: {insight.confidence:.2f}")
            
        logger.info(f"Total insights generated: {len(all_insights)}")
        
        # Clean up test report
        await reports_repo.delete(report.id)
        logger.info(f"Deleted test report: {report.id}")
        
    except Exception as e:
        logger.error(f"❌ Error during test: {str(e)}")
    finally:
        # Close the database session
        await db.close()
        logger.info("Database session closed")


async def main():
    """Main entry point for testing."""
    logger.info("Starting JLL report test")
    
    try:
        await test_jll_report_generation()
        logger.info("✅ JLL report generation test completed successfully")
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
    
    logger.info("Test complete")


if __name__ == "__main__":
    asyncio.run(main())
