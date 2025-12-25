"""Tests for the Report Generator Service.

This module tests the report generator service that integrates with
various AI analysis services to produce comprehensive reports.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.services.report_generator import ReportGeneratorService
from src.services.ai.competitor_analysis import CompetitorAnalysisService
from src.services.ai.market_analysis import MarketAnalysisService
from src.services.ai.audience_analysis import AudienceAnalysisService
from src.services.ai.temporal_analysis import TemporalAnalysisService
from src.services.ai.seo_analysis import SEOAnalysisService
from src.models.report import Report, ReportStatus
from src.repositories.report_repository import ReportRepository


@pytest.fixture
def mock_competitor_analysis():
    """Create a mock competitor analysis service."""
    service = AsyncMock(spec=CompetitorAnalysisService)
    
    # Mock analysis result
    service.analyze.return_value = {
        "analysis": {
            "insights": [
                {
                    "category": "trend",
                    "title": "Market Share Growth",
                    "description": "Competitor A has shown 15% market share growth",
                    "confidence": 0.9
                }
            ]
        },
        "confidence_score": 0.88,
        "confidence_metrics": {
            "data_quality": 0.92,
            "metric_confidence": 0.9,
            "insight_confidence": 0.85
        },
        "reasoning": {
            "chain_id": "comp-123",
            "steps": [
                {
                    "description": "Fetched competitor data",
                    "input": {"competitor_ids": [1, 2]},
                    "output": {"data_quality": 0.92}
                }
            ]
        }
    }
    
    return service


@pytest.fixture
def mock_market_analysis():
    """Create a mock market analysis service."""
    service = AsyncMock(spec=MarketAnalysisService)
    
    # Mock analysis result
    service.analyze.return_value = {
        "analysis": {
            "company_id": 1,
            "sectors_analyzed": ["technology", "healthcare"],
            "timeframe": "last_quarter",
            "market_trends": {
                "technology": {
                    "trends": [{"name": "AI adoption", "strength": 0.85}],
                    "opportunities": ["Enterprise AI solutions"],
                    "threats": ["Talent shortage"]
                }
            },
            "predictions": [
                {
                    "sector": "technology",
                    "growth_forecast": 0.14,
                    "qualitative_analysis": "Growing AI adoption",
                    "recommendations": ["Invest in AI"]
                }
            ]
        },
        "confidence_score": 0.86,
        "confidence_metrics": {
            "data_completeness": 0.90,
            "trend_confidence": 0.88,
            "prediction_confidence": 0.82
        },
        "reasoning": {
            "chain_id": "market-123",
            "steps": [
                {
                    "description": "Fetched market data",
                    "input": {"sectors": ["technology", "healthcare"]},
                    "output": {"completeness": 0.90}
                }
            ]
        }
    }
    
    return service


@pytest.fixture
def mock_audience_analysis():
    """Create a mock audience analysis service."""
    service = AsyncMock(spec=AudienceAnalysisService)
    
    # Mock analysis result
    service.analyze.return_value = {
        "analysis": {
            "personas": [
                {
                    "name": "Tech Enthusiasts",
                    "demographics": {
                        "age_range": "25-34",
                        "gender_distribution": {"male": 0.65, "female": 0.32, "other": 0.03}
                    },
                    "behaviors": ["Early technology adopters"],
                    "interests": ["AI", "Gadgets"],
                    "confidence": 0.89
                }
            ],
            "recommendations": [
                {
                    "segment": "Tech Enthusiasts",
                    "content_strategy": "Technical deep-dives",
                    "channels": ["Twitter", "YouTube"]
                }
            ]
        },
        "confidence_score": 0.87,
        "confidence_metrics": {
            "data_quality": 0.92,
            "engagement_confidence": 0.82,
            "persona_confidence": 0.87
        },
        "reasoning": {
            "chain_id": "audience-123",
            "steps": [
                {
                    "description": "Fetched audience data",
                    "input": {"company_id": 1},
                    "output": {"data_quality": 0.92}
                }
            ]
        }
    }
    
    return service


@pytest.fixture
def mock_temporal_analysis():
    """Create a mock temporal analysis service."""
    service = AsyncMock(spec=TemporalAnalysisService)
    
    # Mock analysis result
    service.analyze.return_value = {
        "analysis": {
            "trends": [
                {
                    "metric": "engagement",
                    "pattern": "seasonal",
                    "description": "Higher engagement during Q4",
                    "confidence": 0.85
                }
            ],
            "forecasts": [
                {
                    "metric": "engagement",
                    "forecast": "increasing",
                    "value": 0.12,
                    "confidence": 0.82
                }
            ]
        },
        "confidence_score": 0.84,
        "confidence_metrics": {
            "data_quality": 0.90,
            "trend_confidence": 0.85,
            "forecast_confidence": 0.82
        },
        "reasoning": {
            "chain_id": "temporal-123",
            "steps": [
                {
                    "description": "Analyzed time series data",
                    "input": {"metrics": ["engagement"]},
                    "output": {"patterns": ["seasonal"]}
                }
            ]
        }
    }
    
    return service


@pytest.fixture
def mock_seo_analysis():
    """Create a mock SEO analysis service."""
    service = AsyncMock(spec=SEOAnalysisService)
    
    # Mock analysis result
    service.analyze.return_value = {
        "analysis": {
            "keywords": [
                {
                    "keyword": "AI solutions",
                    "volume": 5000,
                    "difficulty": 0.65,
                    "relevance": 0.85
                }
            ],
            "content_gaps": [
                {
                    "topic": "Machine Learning Applications",
                    "opportunity": "high",
                    "competition": "medium"
                }
            ],
            "recommendations": [
                {
                    "type": "content",
                    "description": "Create in-depth guides on ML applications",
                    "priority": "high"
                }
            ]
        },
        "confidence_score": 0.85,
        "confidence_metrics": {
            "data_quality": 0.88,
            "keyword_confidence": 0.85,
            "recommendation_confidence": 0.82
        },
        "reasoning": {
            "chain_id": "seo-123",
            "steps": [
                {
                    "description": "Analyzed keyword data",
                    "input": {"domain": "example.com"},
                    "output": {"keyword_count": 150}
                }
            ]
        }
    }
    
    return service


@pytest.fixture
def mock_report_repository():
    """Create a mock report repository."""
    repo = AsyncMock(spec=ReportRepository)
    
    # Mock save method
    repo.save.return_value = 1  # Report ID
    
    # Mock get method
    repo.get.return_value = Report(
        id=1,
        type="comprehensive",
        status=ReportStatus.PENDING,
        parameters={"company_id": 1},
        created_at=datetime.now()
    )
    
    # Mock update method
    repo.update.return_value = True
    
    return repo


@pytest.fixture
def report_generator_service(
    mock_competitor_analysis,
    mock_market_analysis,
    mock_audience_analysis,
    mock_temporal_analysis,
    mock_seo_analysis,
    mock_report_repository
):
    """Create a report generator service with mocked dependencies."""
    return ReportGeneratorService(
        competitor_analysis=mock_competitor_analysis,
        market_analysis=mock_market_analysis,
        audience_analysis=mock_audience_analysis,
        temporal_analysis=mock_temporal_analysis,
        seo_analysis=mock_seo_analysis,
        report_repository=mock_report_repository
    )


class TestReportGeneratorService:
    """Test cases for the ReportGeneratorService."""
    
    @pytest.mark.asyncio
    async def test_generate_competitor_report(self, report_generator_service):
        """Test generating a competitor analysis report."""
        # Arrange
        report_params = {
            "company_id": 1,
            "competitor_ids": [2, 3],
            "metrics": ["market_share", "growth_rate"],
            "timeframe": "last_quarter",
            "with_chain_of_thought": True
        }
        
        # Act
        report_id = await report_generator_service.generate_competitor_report(**report_params)
        
        # Assert
        assert report_id == 1
        report_generator_service.report_repository.save.assert_called_once()
        report_generator_service.competitor_analysis.analyze.assert_called_once_with(
            competitor_ids=[2, 3],
            metrics=["market_share", "growth_rate"],
            timeframe="last_quarter",
            with_chain_of_thought=True
        )
    
    @pytest.mark.asyncio
    async def test_generate_market_report(self, report_generator_service):
        """Test generating a market analysis report."""
        # Arrange
        report_params = {
            "company_id": 1,
            "sectors": ["technology", "healthcare"],
            "timeframe": "last_quarter",
            "with_chain_of_thought": True,
            "include_predictions": True
        }
        
        # Act
        report_id = await report_generator_service.generate_market_report(**report_params)
        
        # Assert
        assert report_id == 1
        report_generator_service.report_repository.save.assert_called_once()
        report_generator_service.market_analysis.analyze.assert_called_once_with(
            company_id=1,
            sectors=["technology", "healthcare"],
            timeframe="last_quarter",
            with_chain_of_thought=True,
            include_predictions=True
        )
    
    @pytest.mark.asyncio
    async def test_generate_audience_report(self, report_generator_service):
        """Test generating an audience analysis report."""
        # Arrange
        report_params = {
            "company_id": 1,
            "segment_id": None,
            "timeframe": "last_quarter",
            "demographic_filters": {"age_range": ["25-34", "35-44"]},
            "with_chain_of_thought": True
        }
        
        # Act
        report_id = await report_generator_service.generate_audience_report(**report_params)
        
        # Assert
        assert report_id == 1
        report_generator_service.report_repository.save.assert_called_once()
        report_generator_service.audience_analysis.analyze.assert_called_once_with(
            company_id=1,
            segment_id=None,
            timeframe="last_quarter",
            demographic_filters={"age_range": ["25-34", "35-44"]},
            with_chain_of_thought=True
        )
    
    @pytest.mark.asyncio
    async def test_generate_temporal_report(self, report_generator_service):
        """Test generating a temporal analysis report."""
        # Arrange
        report_params = {
            "company_id": 1,
            "metrics": ["engagement", "conversion"],
            "timeframe": "last_year",
            "granularity": "monthly",
            "with_chain_of_thought": True
        }
        
        # Act
        report_id = await report_generator_service.generate_temporal_report(**report_params)
        
        # Assert
        assert report_id == 1
        report_generator_service.report_repository.save.assert_called_once()
        report_generator_service.temporal_analysis.analyze.assert_called_once_with(
            company_id=1,
            metrics=["engagement", "conversion"],
            timeframe="last_year",
            granularity="monthly",
            with_chain_of_thought=True
        )
    
    @pytest.mark.asyncio
    async def test_generate_seo_report(self, report_generator_service):
        """Test generating an SEO analysis report."""
        # Arrange
        report_params = {
            "company_id": 1,
            "domain": "example.com",
            "competitors": ["competitor1.com", "competitor2.com"],
            "with_chain_of_thought": True
        }
        
        # Act
        report_id = await report_generator_service.generate_seo_report(**report_params)
        
        # Assert
        assert report_id == 1
        report_generator_service.report_repository.save.assert_called_once()
        report_generator_service.seo_analysis.analyze.assert_called_once_with(
            company_id=1,
            domain="example.com",
            competitors=["competitor1.com", "competitor2.com"],
            with_chain_of_thought=True
        )
    
    @pytest.mark.asyncio
    async def test_generate_comprehensive_report(self, report_generator_service):
        """Test generating a comprehensive report."""
        # Arrange
        report_params = {
            "company_id": 1,
            "competitor_ids": [2, 3],
            "sectors": ["technology"],
            "timeframe": "last_quarter",
            "with_chain_of_thought": True
        }
        
        # Act
        report_id = await report_generator_service.generate_comprehensive_report(**report_params)
        
        # Assert
        assert report_id == 1
        report_generator_service.report_repository.save.assert_called_once()
        
        # Verify all analysis services were called
        report_generator_service.competitor_analysis.analyze.assert_called_once()
        report_generator_service.market_analysis.analyze.assert_called_once()
        report_generator_service.audience_analysis.analyze.assert_called_once()
        
        # Optional analyses may be called depending on implementation
        # These assertions would depend on the specific implementation
    
    @pytest.mark.asyncio
    async def test_get_report_status(self, report_generator_service):
        """Test getting report status."""
        # Arrange
        report_id = 1
        
        # Act
        report = await report_generator_service.get_report_status(report_id)
        
        # Assert
        assert report.id == 1
        assert report.status == ReportStatus.PENDING
        report_generator_service.report_repository.get.assert_called_once_with(report_id)
    
    @pytest.mark.asyncio
    async def test_get_report_result(self, report_generator_service):
        """Test getting report result."""
        # Arrange
        report_id = 1
        
        # Mock report with completed status
        mock_report = Report(
            id=1,
            type="competitor_analysis",
            status=ReportStatus.COMPLETED,
            parameters={"competitor_ids": [2, 3]},
            result={
                "analysis": {
                    "insights": [
                        {
                            "category": "trend",
                            "title": "Market Share Growth",
                            "description": "Competitor A has shown 15% market share growth",
                            "confidence": 0.9
                        }
                    ]
                },
                "confidence_score": 0.88
            },
            created_at=datetime.now(),
            completed_at=datetime.now()
        )
        report_generator_service.report_repository.get.return_value = mock_report
        
        # Act
        result = await report_generator_service.get_report_result(report_id)
        
        # Assert
        assert result == mock_report.result
        report_generator_service.report_repository.get.assert_called_once_with(report_id)
    
    @pytest.mark.asyncio
    async def test_get_report_result_not_completed(self, report_generator_service):
        """Test getting report result for a report that is not completed."""
        # Arrange
        report_id = 1
        
        # Mock report with pending status
        mock_report = Report(
            id=1,
            type="competitor_analysis",
            status=ReportStatus.PENDING,
            parameters={"competitor_ids": [2, 3]},
            created_at=datetime.now()
        )
        report_generator_service.report_repository.get.return_value = mock_report
        
        # Act/Assert
        with pytest.raises(ValueError, match="Report is not completed"):
            await report_generator_service.get_report_result(report_id)
        
        report_generator_service.report_repository.get.assert_called_once_with(report_id)
