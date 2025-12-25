"""
JLL Analysis Report Generator using Sprint 4 AI/ML capabilities.

This script implements the complete workflow for JLL competitor analysis:
1. Campaign creation with primary company (JLL)
2. Competitor identification based on relevance
3. Data collection through web scraping, link search, and engagement extraction
4. AI-powered analysis with chain-of-thought reasoning and confidence scoring
5. Professional PDF report generation with enhanced formatting

Features:
- Complete integration of all Sprint 4 services
- GPT-4 for enhanced insights with Anthropic Claude as fallback
- Comprehensive error handling and logging
- BDD/TDD compliant implementation
"""
import asyncio
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Core services
from src.services.report_generator import ReportGeneratorService
from src.services.pdf_export import PDFExportService
from src.services.llm_provider import LLMProvider, FallbackManager, ProviderConfig

# AI/ML services
from src.services.ai.competitor_analysis import CompetitorAnalysisService
from src.services.ai.market_analysis import MarketAnalysisService
from src.services.ai.audience_analysis import AudienceAnalysisService

# Data services
from src.services.data.competitor_data import CompetitorDataService
from src.services.data.metrics import MetricsService
from src.services.campaign.campaign_service import CampaignService

# Web scraping & engagement services
from src.services.web_scraper.web_scraper import WebScraperService
from src.services.link_search.link_search import LinkSearchService
from src.services.engagement_extraction.engagement_extraction import EngagementExtractionService
from src.workflow.scraping_workflow import scrape_company_data, scrape_competitors_data

# Repositories
from src.repositories.competitor_repository import CompetitorRepository
from src.repositories.competitor_metrics_repository import CompetitorMetricsRepository

# Models
from src.models.report import Report, ReportType, ReportStatus
from src.models.competitor_metrics import MetricType

# Load environment variables
load_dotenv()

async def create_db_session() -> AsyncSession:
    """Create and return a database session following Semantic Seed standards."""
    try:
        # Get database credentials
        user = os.getenv('DB_USER', 'tobymorning')
        password = os.getenv('DB_PASSWORD', '')
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'onside')
        
        # Construct database URL with asyncpg driver
        database_url = f'postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}'
        
        # Create async engine with proper configuration
        engine = create_async_engine(
            database_url,
            echo=True,  # SQL query logging
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800
        )
        
        # Create session factory
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        
        # Test connection
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: None)
            logger.info('Successfully connected to database')
        
        return async_session()
        
    except Exception as e:
        logger.error(f'Failed to create database session: {str(e)}')
        raise

async def generate_jll_report():
    """Generate enhanced JLL analysis report with AI/ML capabilities.
    
    Following Sprint 4 implementation patterns:
    - Chain-of-thought reasoning for competitor insights
    - Data quality and confidence scoring
    - LLM fallback support with OpenAI as primary provider
    - Structured insights for trends, opportunities, threats
    """
    # Initialize database session variable
    db = None
    
    try:
        logger.info("Starting JLL analysis report generation workflow")
        # Create database session
        db = await create_db_session()
        
        # Step 1: Create campaign for JLL
        logger.info("Creating campaign for JLL analysis")
        campaign_service = CampaignService(db)
        jll_company_id = 1  # Assuming JLL is ID 1, adjust as needed
        campaign_result = await campaign_service.create_campaign(
            name="JLL Competitive Analysis", 
            primary_company_id=jll_company_id,
            description="Analysis of JLL's competitive positioning in the real estate services market"
        )
        
        if not campaign_result["success"]:
            logger.error(f"Failed to create campaign: {campaign_result.get('error')}")
            return {"success": False, "error": campaign_result.get('error')}
        
        campaign = campaign_result["campaign"]
        logger.info(f"Created campaign: {campaign['name']} (ID: {campaign['id']})")
        
        # Step 2: Identify relevant competitors
        logger.info("Identifying relevant competitors for JLL")
        competitors = await campaign_service.identify_competitors(
            campaign_id=campaign["id"],
            max_competitors=5
        )
        
        if not competitors:
            logger.warning("No competitors identified for JLL")
        else:
            logger.info(f"Identified {len(competitors)} competitors for JLL")
            for i, comp in enumerate(competitors, 1):
                logger.info(f"  {i}. {comp['name']} (relevance: {comp['relevance_score']:.2f})")
        
        # Step 3: Set up web scraping services
        web_scraper_service = WebScraperService(db)
        link_search_service = LinkSearchService(db)
        engagement_service = EngagementExtractionService(db)
        
        # Step 4: Scrape JLL data
        logger.info("Starting web scraping for JLL")
        jll_scrape_result = await scrape_company_data(
            web_scraper_service,
            link_search_service,
            engagement_service,
            jll_company_id
        )
        
        if not jll_scrape_result["success"]:
            logger.error(f"Failed to scrape JLL data: {jll_scrape_result.get('error')}")
        else:
            logger.info(f"Successfully scraped {jll_scrape_result.get('links_scraped', 0)} JLL links")
        
        # Step 5: Scrape competitor data
        if competitors:
            logger.info("Starting web scraping for competitors")
            competitor_scrape_result = await scrape_competitors_data(
                web_scraper_service,
                link_search_service,
                engagement_service,
                competitors
            )
            
            logger.info(f"Scraped data for {competitor_scrape_result.get('successful_scrapes', 0)} of {len(competitors)} competitors")
        
        # Initialize LLM manager with Sprint 4 configuration
        llm_manager = FallbackManager()
        
        # Configure OpenAI as primary provider with GPT-4
        openai_config = ProviderConfig(
            name="openai",
            timeout=15.0,
            max_retries=3,
            confidence_threshold=0.85,
            rate_limit=100
        )
        llm_manager.providers[LLMProvider.OPENAI] = openai_config
        
        # Configure Anthropic as fallback
        anthropic_config = ProviderConfig(
            name="anthropic",
            timeout=20.0,
            max_retries=2,
            confidence_threshold=0.80,
            rate_limit=50
        )
        llm_manager.providers[LLMProvider.ANTHROPIC] = anthropic_config
        
        # Set up fallback chain
        llm_manager.fallback_chain = [LLMProvider.OPENAI, LLMProvider.ANTHROPIC]
        
        # Initialize repositories
        competitor_repository = CompetitorRepository(db)
        competitor_metrics_repository = CompetitorMetricsRepository(db)
        
        # Initialize data services
        competitor_data_service = CompetitorDataService(
            competitor_repository=competitor_repository,
            metrics_repository=competitor_metrics_repository
        )
        metrics_service = MetricsService()
        
        # Initialize analysis services with enhanced AI capabilities
        competitor_analysis = CompetitorAnalysisService(
            llm_manager=llm_manager,
            competitor_data_service=competitor_data_service,
            metrics_service=metrics_service
        )
        
        market_analysis = MarketAnalysisService(
            llm_manager=llm_manager,
            market_data_service=None,  # Will use default implementation
            predictive_model_service=None  # Will use default implementation
        )
        
        audience_analysis = AudienceAnalysisService(
            llm_manager=llm_manager,
            audience_data_service=None,  # Will use default implementation
            engagement_metrics_service=None  # Will use default implementation
        )
        
        # Initialize report generator with AI services
        report_generator = ReportGeneratorService(
            db=db,
            llm_manager=llm_manager,
            competitor_analysis_service=competitor_analysis,
            market_analysis_service=market_analysis,
            audience_analysis_service=audience_analysis
        )
        
        pdf_export = PDFExportService(export_dir="exports")
        
        print("\n=== Generating Enhanced JLL Analysis Report ===")
        print("Using GPT-4 for AI/ML insights and chain-of-thought reasoning")
        
        # Create report configuration following Sprint 4 implementation
        report = Report(
            type=ReportType.COMPETITOR,
            status=ReportStatus.QUEUED,
            fallback_count=0,  # Initialize fallback tracking
            chain_of_thought={},  # Initialize chain of thought tracking
            confidence_score=None,  # Will be updated during analysis
            parameters={
                "competitor_ids": [1],  # JLL ID
                "metrics": [
                    MetricType.MARKET_SHARE,
                    MetricType.GROWTH_RATE,
                    MetricType.WEB_TRAFFIC,
                    MetricType.SOCIAL_ENGAGEMENT,
                    MetricType.MENTIONS,
                    MetricType.SENTIMENT
                ],
                "timeframe": "last_year",  # Using string timeframe as per Sprint 4
                "sectors": [
                    "commercial_real_estate",
                    "property_management",
                    "investment_management",
                    "facilities_management",
                    "project_development",
                    "proptech",
                    "smart_buildings",
                    "sustainable_development"
                ],
                "with_chain_of_thought": True,
                "include_predictions": True,
                "confidence_threshold": 0.85,  # Higher threshold for more reliable insights
                "analysis_depth": "comprehensive",
                "include_market_context": True,
                "sentiment_analysis": True,
                "trend_analysis": {
                    "timeframes": ["short_term", "medium_term", "long_term"],
                    "factors": ["market_conditions", "tech_adoption", "sustainability"]
                },
                "competitive_analysis": {
                    "focus_areas": ["ai_integration", "digital_transformation", "sustainability"],
                    "comparison_metrics": ["innovation", "market_share", "growth"]
                }
            }
        )
        
        # Generate competitor report
        result = await report_generator._generate_competitor_report(report)
        
        # Export to PDF with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = await pdf_export.export_report(
            result,
            "competitor",
            filename=f"jll_analysis_{timestamp}.pdf"
        )
        
        # Print analysis summary
        print("\nReport Generation Summary:")
        print(f"- Confidence Score: {result['metadata']['confidence_score']:.2f}")
        
        # Handle processing_time as dictionary with detailed timing metrics
        processing_time = result['metadata']['processing_time']
        if isinstance(processing_time, dict):
            print(f"- Total Processing Time: {processing_time.get('total', 0.0):.2f}s")
            print("  Timing Breakdown:")
            for key, value in processing_time.items():
                if key != 'total':
                    print(f"  - {key.replace('_', ' ').title()}: {value:.2f}s")
        else:
            # Fallback for backward compatibility
            print(f"- Processing Time: {float(processing_time):.2f}s")
            
        print(f"- Model: {result['metadata']['model']}")
        
        # Handle different data quality structures
        if 'data_coverage' in result['metadata']:
            if isinstance(result['metadata']['data_coverage'], dict) and 'quality_score' in result['metadata']['data_coverage']:
                print(f"- Data Quality: {result['metadata']['data_coverage']['quality_score']:.2f}")
            else:
                print(f"- Data Coverage: {result['metadata']['data_coverage']}")
        elif 'confidence_metrics' in result and 'data_quality' in result['confidence_metrics']:
            print(f"- Data Quality: {result['confidence_metrics']['data_quality']:.2f}")
        elif 'data_quality' in result['metadata']:
            print(f"- Data Quality: {result['metadata']['data_quality']:.2f}")
        
        print("\nKey Insights (High Confidence):")
        for rec in result["analysis"]["recommendations"]:
            if rec["confidence"] >= 0.85:
                print(f"- {rec['action']} (Confidence: {rec['confidence']:.2f})")
                print(f"  Impact: {rec['impact']}")
                print(f"  Reasoning: {rec['reasoning']}\n")
        
        print(f"\nPDF Report exported to: {pdf_path}")
        print("\nChain of Thought Process:")
        print(result["metadata"]["chain_of_thought"])
        
        return pdf_path
        
    except Exception as e:
        print(f"Error generating JLL report: {str(e)}")
        logger.error(f"Failed to run JLL analysis: {str(e)}")
        raise
        
    finally:
        # Ensure database connection is properly closed
        if db:
            await db.close()
            logger.info("Database session closed successfully")

if __name__ == "__main__":
    try:
        # Load environment variables
        load_dotenv()
        
        # Validate OpenAI API key
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError('OPENAI_API_KEY environment variable not set')
            
        # Validate Anthropic API key for fallback capability
        if not os.getenv('ANTHROPIC_API_KEY'):
            logger.warning('ANTHROPIC_API_KEY environment variable not set - fallback to Anthropic disabled')
        
        # Ensure exports directory exists
        Path("exports").mkdir(exist_ok=True)
        
        # Run report generation
        asyncio.run(generate_jll_report())
        
    except Exception as e:
        logger.error(f'Failed to run JLL analysis: {str(e)}')
        raise
