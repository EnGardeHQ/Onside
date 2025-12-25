"""Tests for the Market Analysis Service.

This module tests the AI-powered market analysis service with predictive
insights, chain-of-thought reasoning, and LLM fallback support.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.services.ai.market_analysis import MarketAnalysisService
from src.services.llm_provider import FallbackManager, LLMProvider
from src.services.data.market_data import MarketDataService
from src.services.data.predictive_models import PredictiveModelService
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
                "sector": "technology",
                "analysis": "Growing at 12% annually with increased demand for AI solutions",
                "recommendations": ["Invest in AI capabilities", "Partner with tech startups"]
            },
            {
                "sector": "healthcare",
                "analysis": "Stable growth with regulatory changes impacting market dynamics",
                "recommendations": ["Focus on compliance solutions", "Expand telehealth offerings"]
            }
        ]
    })
    mock_response.confidence_score = 0.86
    
    manager.execute_with_fallback.return_value = mock_response
    return manager


@pytest.fixture
def mock_market_data():
    """Create a mock market data service."""
    service = AsyncMock(spec=MarketDataService)
    
    # Mock market data
    mock_data = {
        "sectors": {
            "technology": {
                "growth_rate": 0.12,
                "market_size": 2.5,  # trillion
                "trends": ["AI adoption", "Cloud migration"]
            },
            "healthcare": {
                "growth_rate": 0.08,
                "market_size": 1.8,  # trillion
                "trends": ["Telehealth", "Personalized medicine"]
            }
        },
        "timeframe": "2025-01-01 to 2025-03-01"
    }
    
    service.get_sector_data.return_value = mock_data
    service.calculate_completeness = MagicMock(return_value=0.90)
    
    # Mock sector trend analysis
    service.analyze_sector_trends.return_value = {
        "trends": [
            {"name": "AI adoption", "strength": 0.85, "direction": "increasing"},
            {"name": "Cloud migration", "strength": 0.78, "direction": "stable"}
        ],
        "opportunities": ["Enterprise AI solutions", "Edge computing"],
        "threats": ["Talent shortage", "Regulatory changes"],
        "confidence": 0.88
    }
    
    return service


@pytest.fixture
def mock_predictive_models():
    """Create a mock predictive model service."""
    service = AsyncMock(spec=PredictiveModelService)
    
    # Mock predictions
    service.generate_predictions.return_value = {
        "predictions": [
            {
                "sector": "technology",
                "growth_forecast": 0.14,
                "confidence": 0.82,
                "timeframe": "next_quarter"
            },
            {
                "sector": "healthcare",
                "growth_forecast": 0.09,
                "confidence": 0.79,
                "timeframe": "next_quarter"
            }
        ],
        "aggregate_confidence": 0.80
    }
    
    return service


@pytest.fixture
def market_analysis_service(mock_llm_manager, mock_market_data, mock_predictive_models):
    """Create a market analysis service with mocked dependencies."""
    return MarketAnalysisService(
        llm_manager=mock_llm_manager,
        market_data_service=mock_market_data,
        predictive_model_service=mock_predictive_models
    )


class TestMarketAnalysisService:
    """Test cases for the MarketAnalysisService."""
    
    @pytest.mark.asyncio
    async def test_analyze_with_chain_of_thought(self, market_analysis_service):
        """Test market analysis with chain-of-thought reasoning."""
        # Arrange
        company_id = 1
        sectors = ["technology", "healthcare"]
        timeframe = "last_quarter"
        
        # Act
        result = await market_analysis_service.analyze(
            company_id=company_id,
            sectors=sectors,
            timeframe=timeframe,
            with_chain_of_thought=True,
            include_predictions=True
        )
        
        # Assert
        assert "analysis" in result
        assert "confidence_score" in result
        assert "confidence_metrics" in result
        assert "reasoning" in result
        
        assert result["analysis"]["company_id"] == company_id
        assert len(result["analysis"]["sectors_analyzed"]) == 2
        assert result["analysis"]["timeframe"] == timeframe
        assert "market_trends" in result["analysis"]
        assert "predictions" in result["analysis"]
        
        # Verify chain of thought was included
        assert "chain_id" in result["reasoning"]
        assert "steps" in result["reasoning"]
        assert len(result["reasoning"]["steps"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_without_chain_of_thought(self, market_analysis_service):
        """Test market analysis without chain-of-thought reasoning."""
        # Arrange
        company_id = 1
        sectors = ["technology", "healthcare"]
        timeframe = "last_quarter"
        
        # Act
        result = await market_analysis_service.analyze(
            company_id=company_id,
            sectors=sectors,
            timeframe=timeframe,
            with_chain_of_thought=False,
            include_predictions=True
        )
        
        # Assert
        assert "analysis" in result
        assert "confidence_score" in result
        assert "confidence_metrics" in result
        assert "reasoning" not in result
    
    @pytest.mark.asyncio
    async def test_analyze_without_predictions(self, market_analysis_service):
        """Test market analysis without predictions."""
        # Arrange
        company_id = 1
        sectors = ["technology", "healthcare"]
        timeframe = "last_quarter"
        
        # Act
        result = await market_analysis_service.analyze(
            company_id=company_id,
            sectors=sectors,
            timeframe=timeframe,
            include_predictions=False
        )
        
        # Assert
        assert "analysis" in result
        assert result["analysis"]["predictions"] is None
        assert "prediction_confidence" not in result["confidence_metrics"]
    
    @pytest.mark.asyncio
    async def test_fetch_market_data(self, market_analysis_service):
        """Test fetching market data."""
        # Arrange
        company_id = 1
        sectors = ["technology", "healthcare"]
        timeframe = "last_quarter"
        
        # Act
        data, completeness = await market_analysis_service._fetch_market_data(
            company_id=company_id,
            sectors=sectors,
            timeframe=timeframe
        )
        
        # Assert
        assert "sectors" in data
        assert "technology" in data["sectors"]
        assert "healthcare" in data["sectors"]
        assert completeness == 0.90
    
    @pytest.mark.asyncio
    async def test_analyze_trends(self, market_analysis_service):
        """Test analyzing market trends."""
        # Arrange
        data = {
            "sectors": {
                "technology": {
                    "growth_rate": 0.12,
                    "market_size": 2.5
                },
                "healthcare": {
                    "growth_rate": 0.08,
                    "market_size": 1.8
                }
            }
        }
        sectors = ["technology", "healthcare"]
        
        # Act
        trend_analysis, confidence = await market_analysis_service._analyze_trends(
            data=data,
            sectors=sectors
        )
        
        # Assert
        assert "technology" in trend_analysis
        assert "healthcare" in trend_analysis
        assert "trends" in trend_analysis["technology"]
        assert "opportunities" in trend_analysis["technology"]
        assert confidence == 0.88
    
    @pytest.mark.asyncio
    async def test_generate_predictions(self, market_analysis_service):
        """Test generating market predictions."""
        # Arrange
        trend_analysis = {
            "technology": {
                "trends": [{"name": "AI adoption", "strength": 0.85}],
                "confidence": 0.88
            },
            "healthcare": {
                "trends": [{"name": "Telehealth", "strength": 0.80}],
                "confidence": 0.85
            }
        }
        report = Report(
            type="market_analysis",
            parameters={"company_id": 1, "sectors": ["technology", "healthcare"]}
        )
        
        # Act
        predictions, confidence = await market_analysis_service._generate_predictions(
            trend_analysis=trend_analysis,
            report=report
        )
        
        # Assert
        assert len(predictions) == 2
        assert predictions[0]["sector"] == "technology"
        assert "qualitative_analysis" in predictions[0]
        assert "recommendations" in predictions[0]
        assert confidence == 0.86
    
    def test_prepare_prediction_prompt(self, market_analysis_service):
        """Test preparing prediction prompt."""
        # Arrange
        trend_analysis = {
            "technology": {
                "trends": [{"name": "AI adoption", "strength": 0.85}],
                "confidence": 0.88
            }
        }
        ml_predictions = {
            "predictions": [
                {
                    "sector": "technology",
                    "growth_forecast": 0.14,
                    "confidence": 0.82
                }
            ]
        }
        
        # Act
        prompt = market_analysis_service._prepare_prediction_prompt(
            trend_analysis=trend_analysis,
            ml_predictions=ml_predictions
        )
        
        # Assert
        prompt_data = json.loads(prompt)
        assert prompt_data["task"] == "market_prediction_enhancement"
        assert "data" in prompt_data
        assert "trends" in prompt_data["data"]
        assert "ml_predictions" in prompt_data["data"]
        assert "requirements" in prompt_data
        assert "focus_areas" in prompt_data["requirements"]
    
    def test_combine_predictions(self, market_analysis_service):
        """Test combining ML predictions with LLM insights."""
        # Arrange
        ml_predictions = {
            "predictions": [
                {
                    "sector": "technology",
                    "growth_forecast": 0.14,
                    "confidence": 0.82
                },
                {
                    "sector": "healthcare",
                    "growth_forecast": 0.09,
                    "confidence": 0.79
                }
            ]
        }
        
        llm_response = MagicMock()
        llm_response.content = json.dumps({
            "insights": [
                {
                    "sector": "technology",
                    "analysis": "Growing AI adoption",
                    "recommendations": ["Invest in AI"]
                },
                {
                    "sector": "healthcare",
                    "analysis": "Telehealth expansion",
                    "recommendations": ["Expand digital health"]
                }
            ]
        })
        
        # Act
        enhanced_predictions = market_analysis_service._combine_predictions(
            ml_predictions=ml_predictions,
            llm_response=llm_response
        )
        
        # Assert
        assert len(enhanced_predictions) == 2
        assert enhanced_predictions[0]["sector"] == "technology"
        assert "qualitative_analysis" in enhanced_predictions[0]
        assert "recommendations" in enhanced_predictions[0]
        assert enhanced_predictions[0]["qualitative_analysis"] == "Growing AI adoption"
    
    def test_combine_predictions_invalid_json(self, market_analysis_service):
        """Test combining predictions with invalid LLM response."""
        # Arrange
        ml_predictions = {
            "predictions": [
                {
                    "sector": "technology",
                    "growth_forecast": 0.14,
                    "confidence": 0.82
                }
            ]
        }
        
        llm_response = MagicMock()
        llm_response.content = "Invalid JSON"
        
        # Act
        predictions = market_analysis_service._combine_predictions(
            ml_predictions=ml_predictions,
            llm_response=llm_response
        )
        
        # Assert
        assert len(predictions) == 1
        assert predictions[0]["sector"] == "technology"
        assert "qualitative_analysis" not in predictions[0]
