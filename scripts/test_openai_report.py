"""Test script for OpenAI competitor report generation.

This script tests the actual OpenAI API integration in our report generation
service, following Semantic Seed coding standards and BDD principles from Sprint 4.
"""
import asyncio
import logging
from datetime import datetime, timedelta, UTC
from typing import Dict, Any

from src.services.report_generator import ReportGeneratorService
from src.services.ai.llm_service import LLMService, LLMProvider
from src.services.ai.competitor_analysis import CompetitorAnalysisService
from src.services.data.competitor_data import CompetitorDataService
from src.services.data.metrics import MetricsService
from src.repositories.competitor_repository import CompetitorRepository
from src.repositories.competitor_metrics_repository import CompetitorMetricsRepository
from src.models.report import Report, ReportType, ReportStatus
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Configure logging per Semantic Seed standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_competitor_report():
    """
    Generate a competitor report using actual OpenAI API with chain-of-thought reasoning.
    
    Following Sprint 4 implementation:
    - Uses GPT-4 for enhanced analysis
    - Implements chain-of-thought reasoning
    - Includes confidence scoring
    - Provides structured insights
    - Handles fallbacks gracefully
    """
    # Create async DB session
    engine = create_async_engine('postgresql+asyncpg://localhost/onside')
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # Initialize services with OpenAI as primary provider
        llm_service = LLMService()
        
        # Initialize repositories
        competitor_repository = CompetitorRepository(db=session)
        competitor_metrics_repository = CompetitorMetricsRepository(db=session)
        
        # Initialize metrics service
        metrics_service = MetricsService()
        
        # Initialize competitor data service with repositories
        competitor_data = CompetitorDataService(
            competitor_repository=competitor_repository,
            metrics_repository=competitor_metrics_repository
        )
        
        # Initialize competitor analysis with chain-of-thought
        competitor_analysis = CompetitorAnalysisService(
            llm_manager=llm_service,
            competitor_data_service=competitor_data,
            metrics_service=metrics_service
        )
        
        # Initialize report generator with AI services
        report_gen = ReportGeneratorService(
            db=session,
            competitor_analysis_service=competitor_analysis,
            llm_manager=llm_service
        )
        
        # Create test report with comprehensive parameters
        report = Report(
            user_id=1,
            type=ReportType.COMPETITOR,
            status=ReportStatus.QUEUED,
            parameters={
                'competitor_ids': [1, 2],
                'metrics': [
                    'revenue',
                    'market_share',
                    'growth_rate',
                    'customer_satisfaction',
                    'product_innovation'
                ],
                'timeframe': {
                    'start': (datetime.now(UTC) - timedelta(days=90)).isoformat(),
                    'end': datetime.now(UTC).isoformat()
                },
                'with_chain_of_thought': True,
                'confidence_threshold': 0.8,
                'analysis_depth': 'comprehensive',
                'include_predictions': True
            },
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        try:
            # Generate report using OpenAI
            logger.info("Generating competitor report using OpenAI GPT-4...")
            result = await report_gen._generate_competitor_report(report)
            
            # Log comprehensive results
            logger.info("\nReport Generation Results:")
            logger.info("\nAnalysis Results:")
            for metric, analysis in result['analysis'].items():
                logger.info(f"\n{metric.upper()}:")
                logger.info(f"Trend: {analysis.get('trend')}")
                logger.info(f"Confidence: {analysis.get('confidence'):.2f}")
            
            logger.info("\nKey Insights:")
            for insight in result['insights']:
                logger.info(f"\n- Type: {insight['type']}")
                logger.info(f"  Title: {insight['title']}")
                logger.info(f"  Description: {insight['description']}")
                logger.info(f"  Confidence: {insight.get('confidence', 0.0):.2f}")
            
            logger.info("\nRecommendations:")
            for rec in result['recommendations']:
                logger.info(f"\n- {rec['title']}")
                logger.info(f"  Action Items: {', '.join(rec.get('action_items', []))}")
                logger.info(f"  Priority: {rec.get('priority', 'medium')}")
            
            logger.info("\nChain of Thought:")
            for step in report.chain_of_thought:
                logger.info(f"\n{step['step']}: {step['description']}")
            
            logger.info("\nConfidence Metrics:")
            logger.info(f"Overall Score: {report.confidence_score:.2f}")
            for metric, score in report.confidence_metrics.items():
                logger.info(f"{metric}: {score:.2f}")
            
            logger.info("\nMetadata:")
            logger.info(f"Provider: {result['metadata']['provider']}")
            logger.info(f"Model: {result['metadata']['model']}")
            logger.info(f"Processing Time: {result['metadata']['processing_time']:.2f}s")
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            logger.error("Chain of thought at failure:")
            if hasattr(report, 'chain_of_thought'):
                for step in report.chain_of_thought:
                    logger.error(f"{step['step']}: {step['description']}")
            raise

if __name__ == "__main__":
    asyncio.run(test_competitor_report())
