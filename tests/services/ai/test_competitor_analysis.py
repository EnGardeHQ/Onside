"""Tests for the Competitor Analysis Service.

This module tests the AI-powered competitor analysis service with
chain-of-thought reasoning and LLM fallback support.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.services.ai.competitor_analysis import CompetitorAnalysisService
from src.services.llm_provider import FallbackManager, LLMProvider
from src.services.data.competitor_data import CompetitorDataService
from src.services.data.metrics import MetricsService
from src.models.report import Report


@pytest.fixture
def mock_llm_manager():
    """Create a mock LLM manager."""
    manager = AsyncMock(spec=FallbackManager)
    
    # Mock response from LLM
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "insights": [
            {
                "category": "trend",
                "title": "Market Share Growth",
                "description": "Competitor A has shown 15% market share growth",
                "confidence": 0.9
            },
            {
                "category": "threat",
                "title": "New Product Launch",
                "description": "Competitor B is launching a competing product",
                "confidence": 0.85
            }
        ]
    })
    mock_response.confidence_score = 0.88
    
    manager.execute_with_fallback.return_value = mock_response
    return manager


@pytest.fixture
def mock_competitor_data():
    """Create a mock competitor data service."""
    service = AsyncMock(spec=CompetitorDataService)
    
    # Mock competitor data
    mock_data = {
        "competitors": [
            {"id": 1, "name": "Competitor A", "metrics": {"market_share": 0.3}},
            {"id": 2, "name": "Competitor B", "metrics": {"market_share": 0.2}}
        ],
        "timeframe": "2025-01-01 to 2025-03-01"
    }
    
    service.get_bulk_data.return_value = mock_data
    service.calculate_data_quality = MagicMock(return_value=0.92)
    return service


@pytest.fixture
def mock_metrics_service():
    """Create a mock metrics service."""
    service = MagicMock(spec=MetricsService)
    
    # Mock metric analysis
    service.analyze_metric.return_value = {
        "trend": "increasing",
        "value": 0.15,
        "confidence": 0.9
    }
    
    service.calculate_data_quality = MagicMock(return_value=0.92)
    return service


@pytest.fixture
def competitor_analysis_service(mock_llm_manager, mock_competitor_data, mock_metrics_service):
    """Create a competitor analysis service with mocked dependencies."""
    return CompetitorAnalysisService(
        llm_manager=mock_llm_manager,
        competitor_data_service=mock_competitor_data,
        metrics_service=mock_metrics_service
    )


class TestCompetitorAnalysisService:
    """Test cases for the CompetitorAnalysisService."""
    
    @pytest.mark.asyncio
    async def test_analyze_with_chain_of_thought(self, competitor_analysis_service):
        """Test competitor analysis with chain-of-thought reasoning."""
        # Arrange
        competitor_ids = [1, 2]
        metrics = ["market_share", "growth_rate"]
        timeframe = "last_quarter"
        
        # Act
        result = await competitor_analysis_service.analyze(
            competitor_ids=competitor_ids,
            metrics=metrics,
            timeframe=timeframe,
            with_chain_of_thought=True
        )
        
        # Assert
        assert "analysis" in result
        assert "confidence_score" in result
        assert "confidence_metrics" in result
        assert "reasoning" in result
        
        assert len(result["analysis"]["insights"]) == 2
        assert result["confidence_score"] > 0.8
        assert "data_quality" in result["confidence_metrics"]
        assert "metric_confidence" in result["confidence_metrics"]
        assert "insight_confidence" in result["confidence_metrics"]
        
        # Verify chain of thought was included
        assert "chain_id" in result["reasoning"]
        assert "steps" in result["reasoning"]
        assert len(result["reasoning"]["steps"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_without_chain_of_thought(self, competitor_analysis_service):
        """Test competitor analysis without chain-of-thought reasoning."""
        # Arrange
        competitor_ids = [1, 2]
        metrics = ["market_share", "growth_rate"]
        timeframe = "last_quarter"
        
        # Act
        result = await competitor_analysis_service.analyze(
            competitor_ids=competitor_ids,
            metrics=metrics,
            timeframe=timeframe,
            with_chain_of_thought=False
        )
        
        # Assert
        assert "analysis" in result
        assert "confidence_score" in result
        assert "confidence_metrics" in result
        assert "reasoning" not in result
    
    @pytest.mark.asyncio
    async def test_analyze_with_confidence_threshold(self, competitor_analysis_service):
        """Test competitor analysis with confidence threshold."""
        # Arrange
        competitor_ids = [1, 2]
        metrics = ["market_share", "growth_rate"]
        timeframe = "last_quarter"
        
        # Act
        result = await competitor_analysis_service.analyze(
            competitor_ids=competitor_ids,
            metrics=metrics,
            timeframe=timeframe,
            confidence_threshold=0.9  # Set high threshold
        )
        
        # Assert
        assert "analysis" in result
        assert "confidence_score" in result
        assert result["confidence_score"] < 0.9  # Our mock setup ensures this
    
    @pytest.mark.asyncio
    async def test_fetch_competitor_data(self, competitor_analysis_service):
        """Test fetching competitor data."""
        # Arrange
        competitor_ids = [1, 2]
        metrics = ["market_share", "growth_rate"]
        timeframe = "last_quarter"
        
        # Act
        data, quality = await competitor_analysis_service._fetch_competitor_data(
            competitor_ids=competitor_ids,
            metrics=metrics,
            timeframe=timeframe
        )
        
        # Assert
        assert "competitors" in data
        assert len(data["competitors"]) == 2
        assert quality == 0.92
    
    @pytest.mark.asyncio
    async def test_analyze_metrics(self, competitor_analysis_service):
        """Test analyzing metrics."""
        # Arrange
        data = {
            "competitors": [
                {"id": 1, "name": "Competitor A", "metrics": {"market_share": 0.3}},
                {"id": 2, "name": "Competitor B", "metrics": {"market_share": 0.2}}
            ]
        }
        metrics = ["market_share", "growth_rate"]
        
        # Act
        analysis, confidence = await competitor_analysis_service._analyze_metrics(
            data=data,
            metrics=metrics
        )
        
        # Assert
        assert "market_share" in analysis
        assert "growth_rate" in analysis
        assert confidence == 0.9
    
    @pytest.mark.asyncio
    async def test_generate_insights(self, competitor_analysis_service):
        """Test generating insights."""
        # Arrange
        analysis_results = {
            "market_share": {"trend": "increasing", "value": 0.15, "confidence": 0.9},
            "growth_rate": {"trend": "stable", "value": 0.05, "confidence": 0.85}
        }
        report = Report(
            type="competitor_analysis",
            parameters={"competitor_ids": [1, 2]}
        )
        
        # Act
        insights, confidence = await competitor_analysis_service._generate_insights(
            analysis_results=analysis_results,
            report=report
        )
        
        # Assert
        assert len(insights) == 2
        assert insights[0]["category"] == "trend"
        assert insights[1]["category"] == "threat"
        assert confidence == 0.88
    
    def test_prepare_insight_prompt(self, competitor_analysis_service):
        """Test preparing insight prompt."""
        # Arrange
        analysis_results = {
            "market_share": {"trend": "increasing", "value": 0.15, "confidence": 0.9},
            "growth_rate": {"trend": "stable", "value": 0.05, "confidence": 0.85}
        }
        
        # Act
        prompt = competitor_analysis_service._prepare_insight_prompt(analysis_results)
        
        # Assert
        prompt_data = json.loads(prompt)
        assert prompt_data["task"] == "competitor_analysis"
        assert "data" in prompt_data
        assert "requirements" in prompt_data
        assert "format" in prompt_data["requirements"]
        assert "focus_areas" in prompt_data["requirements"]
    
    def test_parse_llm_response(self, competitor_analysis_service):
        """Test parsing LLM response."""
        # Arrange
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "insights": [
                {
                    "category": "trend",
                    "title": "Market Share Growth",
                    "description": "Competitor A has shown 15% market share growth",
                    "confidence": 0.9
                }
            ]
        })
        
        # Act
        insights = competitor_analysis_service._parse_llm_response(mock_response)
        
        # Assert
        assert len(insights) == 1
        assert insights[0]["category"] == "trend"
        assert insights[0]["title"] == "Market Share Growth"
    
    def test_parse_llm_response_invalid_json(self, competitor_analysis_service):
        """Test parsing invalid LLM response."""
        # Arrange
        mock_response = MagicMock()
        mock_response.content = "Invalid JSON"
        
        # Act
        insights = competitor_analysis_service._parse_llm_response(mock_response)
        
        # Assert
        assert len(insights) == 0
