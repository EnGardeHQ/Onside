"""Integration tests for LLM services with real APIs.

This module tests the OnSide LLM services with real OpenAI and Anthropic APIs
while mocking other external services like SemRush and Meltwater.
"""

# Test module uses fixtures from conftest.py
import pytest
import asyncio
import os
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

# Import models
from src.models.report import Report, ReportType, ReportStatus
from src.models.company import Company
from src.models.llm_fallback import LLMProvider, FallbackReason

# Import services
from src.services.llm_provider.fallback_manager import FallbackManager
from src.services.ai.llm_with_chain_of_thought import LLMWithChainOfThought
from src.services.ai.competitor_analysis import CompetitorAnalysisService
from src.services.ai.market_analysis import MarketAnalysisService
from src.services.data.competitor_data import CompetitorDataService
from src.services.data.market_data import MarketDataService
from src.services.data.metrics import MetricsService
from src.services.ai.predictive_model import PredictiveModelService

# Environment setup is handled in conftest.py


# DB fixture is imported from conftest.py


class TestLLMIntegration:
    """Integration tests for LLM services with real APIs."""
    
    async def create_test_report(self, db: AsyncSession):
        """Create a test report for integration testing."""
        # First create or get a company
        from sqlalchemy import select
        company_query = select(Company).where(Company.name == "Test Company").limit(1)
        result = await db.execute(company_query)
        company = result.scalar_one_or_none()
        
        if not company:
            company = Company(
                name="Test Company",
                domain="testcompany.com",
                industry="Technology"
            )
            db.add(company)
            await db.flush()
            await db.refresh(company)
        
        # Create a new report
        report = Report(
            company_id=company.id,
            type=ReportType.COMPETITOR,
            status=ReportStatus.PROCESSING,
            data={
                "competitors": [
                    {"name": "Competitor A", "domain": "competitora.com"},
                    {"name": "Competitor B", "domain": "competitorb.com"}
                ]
            },
            created_at=datetime.utcnow()
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)
        
        return report

    @pytest.mark.asyncio
    async def test_llm_with_chain_of_thought(self, db: AsyncSession):
        """Test LLM with chain-of-thought reasoning using real OpenAI API."""
        # Create a test report
        report = await self.create_test_report(db)
        
        # Initialize the fallback manager with real APIs
        fallback_manager = FallbackManager()
        
        # Create LLMWithChainOfThought instance
        llm_service = LLMWithChainOfThought(fallback_manager)
        
        # Simple prompt for testing
        prompt = (
            "Analyze the following company: Test Company\n"
            "Industry: Technology\n"
            "Provide a brief competitive analysis identifying key strengths and weaknesses."
        )
        
        # Execute LLM call with reasoning
        result, confidence = await llm_service._execute_llm_with_reasoning(
            prompt=prompt,
            report=report,
            with_chain_of_thought=True,
        )
        
        # Validate result
        assert result is not None
        assert isinstance(result, dict)
        assert confidence > 0.5
        
        # Verify chain of thought was captured
        assert len(llm_service.chain_of_thought_steps) > 0
        
        # Update the report with the result
        report.result = result
        report.status = ReportStatus.COMPLETED
        db.add(report)
        await db.commit()
        
        # Fetch the updated report to verify
        updated_report = await db.get(Report, report.id)
        assert updated_report.status == ReportStatus.COMPLETED
        assert updated_report.result == result

    @pytest.mark.asyncio
    async def test_competitor_analysis_service(self, db: AsyncSession):
        """Test CompetitorAnalysisService with real OpenAI API."""
        # Create a test report
        report = await self.create_test_report(db)
        
        # Initialize the fallback manager
        fallback_manager = FallbackManager()
        
        # Create mock services
        competitor_data_service = AsyncMock(spec=CompetitorDataService)
        metrics_service = AsyncMock(spec=MetricsService)
        
        # Create the competitor analysis service with mocked semrush service
        with patch('src.services.seo.semrush_service.SemrushService'):
            # Create competitor analysis service
            competitor_service = CompetitorAnalysisService(
                llm_manager=fallback_manager,
                competitor_data_service=competitor_data_service,
                metrics_service=metrics_service
            )
            
            # Mock the _fetch_competitor_data method to avoid needing actual data
            with patch.object(
                competitor_service, '_fetch_competitor_data', 
                new_callable=AsyncMock,
                return_value=({
                    "competitors": [
                        {
                            "name": "Competitor A",
                            "domain": "competitora.com",
                            "metrics": {
                                "traffic": 10000,
                                "keywords": 500,
                                "backlinks": 1000
                            },
                            "content": {
                                "blog_posts": 30,
                                "product_pages": 10
                            }
                        },
                        {
                            "name": "Competitor B",
                            "domain": "competitorb.com",
                            "metrics": {
                                "traffic": 8000,
                                "keywords": 400,
                                "backlinks": 800
                            },
                            "content": {
                                "blog_posts": 25,
                                "product_pages": 8
                            }
                        }
                    ]
                }, 0.85)):
                # Generate competitor analysis
                result = await competitor_service.analyze(
                    competitor_ids=[1, 2],
                    metrics=["traffic", "keywords", "backlinks"],
                    timeframe="last_30_days"
                )
                
                # Validate result
                assert result is not None
                assert isinstance(result, dict)
                assert "insights" in result
                assert len(result["insights"]) > 0
                
                # Check for chain of thought
                assert len(competitor_service.chain_of_thought_steps) > 0

    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, db: AsyncSession):
        """Test fallback mechanism from OpenAI to Anthropic."""
        # Create a test report
        report = await self.create_test_report(db)
        
        # Initialize the fallback manager
        fallback_manager = FallbackManager()
        
        # Force the first provider to fail to test fallback
        original_execute = fallback_manager._execute_llm_call
        
        # Counter to track calls to each provider
        provider_calls = {"openai": 0, "anthropic": 0}
        
        # Mock the execute method to fail for OpenAI
        async def mock_execute_llm_call(provider, prompt, timeout, **kwargs):
            if provider == LLMProvider.OPENAI:
                provider_calls["openai"] += 1
                # Simulate a failure for OpenAI
                raise Exception("Simulated OpenAI failure")
            elif provider == LLMProvider.ANTHROPIC:
                provider_calls["anthropic"] += 1
                # Use the real Anthropic API
                return await original_execute(provider, prompt, timeout, **kwargs)
        
        # Apply the mock
        with patch.object(fallback_manager, '_execute_llm_call', side_effect=mock_execute_llm_call):
            # Create LLMWithChainOfThought instance
            llm_service = LLMWithChainOfThought(fallback_manager)
            
            # Simple prompt for testing
            prompt = (
                "Analyze the following company: Test Company\n"
                "Industry: Technology\n"
                "Provide a brief competitive analysis identifying key strengths and weaknesses."
            )
            
            # Execute LLM call with reasoning
            result, confidence = await llm_service._execute_llm_with_reasoning(
                prompt=prompt,
                report=report,
                with_chain_of_thought=True,
            )
            
            # Verify the fallback occurred
            assert provider_calls["openai"] > 0
            assert provider_calls["anthropic"] > 0
            
            # Validate result from fallback
            assert result is not None
            assert isinstance(result, dict)
            assert confidence > 0.5
            
            # Verify chain of thought was captured
            assert len(llm_service.chain_of_thought_steps) > 0

    @pytest.mark.asyncio
    async def test_market_analysis_service(self, db: AsyncSession):
        """Test MarketAnalysisService with real OpenAI API and mocked data services."""
        # Create a test report
        report = await self.create_test_report(db)
        
        # Initialize the fallback manager
        fallback_manager = FallbackManager()
        
        # Create mock services
        market_data_service = AsyncMock(spec=MarketDataService)
        predictive_model_service = AsyncMock(spec=PredictiveModelService)
        
        # Create the market analysis service with mocked external services
        with patch('src.services.seo.semrush_service.SemrushService'), \
             patch('src.services.market_data.meltwater_service.MeltwaterService', MagicMock()):
            
            # Create market analysis service
            market_service = MarketAnalysisService(
                llm_manager=fallback_manager,
                market_data_service=market_data_service,
                predictive_model_service=predictive_model_service
            )
            
            # Mock the _fetch_market_data method to avoid needing actual data
            with patch.object(
                market_service, '_fetch_market_data', 
                new_callable=AsyncMock,
                return_value=({
                    "industry": "Technology",
                    "segment": "SaaS",
                    "market_size": 5000000000,
                    "growth_rate": 15.5,
                    "trends": [
                        {"name": "Cloud Migration", "strength": 0.85},
                        {"name": "AI Integration", "strength": 0.92},
                        {"name": "Remote Work", "strength": 0.78}
                    ],
                    "competitors": [
                        {"name": "Competitor A", "market_share": 0.15},
                        {"name": "Competitor B", "market_share": 0.12},
                        {"name": "Competitor C", "market_share": 0.09}
                    ]
                }, 0.9)):
                # Generate market analysis
                result = await market_service.analyze(
                    company_id=report.company_id,
                    sectors=["Technology", "SaaS"],
                    timeframe="last_90_days"
                )
                
                # Validate result
                assert result is not None
                assert isinstance(result, dict)
                assert "analysis" in result
                
                # Check for chain of thought
                try:
                    assert len(market_service.chain_of_thought_steps) > 0
                except AttributeError:
                    # If reset_reasoning is implemented instead of reset_chain_of_thought
                    assert market_service.get_reasoning() is not None

                # Reset reasoning chain
                if hasattr(market_service, 'reset_chain_of_thought'):
                    market_service.reset_chain_of_thought()
                else:
                    market_service.reset_reasoning()

                # Add reasoning to result if with_chain_of_thought
                if hasattr(market_service, 'get_reasoning_chain'):
                    result["reasoning"] = market_service.get_reasoning_chain()
                elif hasattr(market_service, 'get_reasoning'):
                    result["reasoning"] = market_service.get_reasoning()

if __name__ == "__main__":
    # For direct execution
    import asyncio
    import pytest
    import sys
    
    # Run the tests with pytest
    sys.exit(pytest.main(['-xvs', __file__]))

