"""Integration tests for OpenAI API in report generation.

This module tests the actual OpenAI API integration with our report generation
service, following BDD principles and Semantic Seed coding standards.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from src.services.report_generator import ReportGeneratorService
from src.services.ai.llm_service import LLMService, LLMProvider
from src.models.report import Report, ReportType, ReportStatus
from src.services.ai.competitor_analysis import CompetitorAnalysisService
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

@pytest.mark.integration
class TestOpenAIIntegration:
    """Integration tests for OpenAI API with chain-of-thought reasoning."""
    
    @pytest.fixture
    async def db_session(self):
        """Create a test database session."""
        engine = create_async_engine('postgresql+asyncpg://localhost/onside_test')
        async_session = sessionmaker(engine, class_=AsyncSession)
        async with async_session() as session:
            yield session
            
    @pytest.fixture
    def llm_service(self):
        """Create LLM service with OpenAI as primary provider."""
        return LLMService(
            primary_provider=LLMProvider.OPENAI,
            fallback_providers=[LLMProvider.ANTHROPIC]
        )
        
    @pytest.fixture
    def competitor_analysis(self, llm_service):
        """Create competitor analysis service with real LLM."""
        return CompetitorAnalysisService(llm_manager=llm_service)
        
    @pytest.fixture
    def report_generator(self, db_session, competitor_analysis):
        """Create report generator with real services."""
        return ReportGeneratorService(
            db=db_session,
            competitor_analysis_service=competitor_analysis
        )
    
    @pytest.mark.asyncio
    async def test_openai_competitor_report_generation(self, report_generator):
        """
        Should generate a competitor report using actual OpenAI API.
        
        Given: A report generator service with OpenAI integration
        When: We request a competitor analysis report
        Then: It should generate insights using GPT-4
        And: Include chain-of-thought reasoning
        And: Provide confidence scores
        """
        # Arrange
        report = Report(
            user_id=1,
            type=ReportType.COMPETITOR,
            status=ReportStatus.QUEUED,
            parameters={
                'competitor_ids': [1, 2],  # Test competitor IDs
                'metrics': ['revenue', 'market_share', 'growth_rate'],
                'timeframe': {
                    'start': (datetime.now() - timedelta(days=90)).isoformat(),
                    'end': datetime.now().isoformat()
                },
                'with_chain_of_thought': True,
                'confidence_threshold': 0.8
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Act
        result = await report_generator._generate_competitor_report(report)
        
        # Assert
        assert isinstance(result, dict)
        assert 'analysis' in result
        assert 'insights' in result
        assert 'recommendations' in result
        assert 'metadata' in result
        
        # Verify OpenAI specific metadata
        assert result['metadata']['provider'] == 'openai'
        assert result['metadata']['model'] == 'gpt-4'
        
        # Verify chain of thought
        assert report.chain_of_thought is not None
        assert len(report.chain_of_thought) > 0
        
        # Verify confidence metrics
        assert report.confidence_score >= 0.0
        assert report.confidence_score <= 1.0
        
        # Print results for manual verification
        print("\nOpenAI Integration Test Results:")
        print(f"Analysis: {result['analysis']}")
        print(f"Chain of Thought: {report.chain_of_thought}")
        print(f"Confidence Score: {report.confidence_score}")
