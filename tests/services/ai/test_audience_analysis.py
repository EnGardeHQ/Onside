"""Tests for the Audience Analysis Service.

This module tests the AI-powered audience analysis service with persona generation,
engagement pattern analysis, and LLM fallback support.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any, Optional

from src.services.ai.audience_analysis import AudienceAnalysisService
from src.services.llm_provider import FallbackManager, LLMProvider
from src.services.data.audience_data import AudienceDataService
from src.services.data.engagement_metrics import EngagementMetricsService
from src.models.report import Report


@pytest.fixture
def mock_llm_manager():
    """Create a mock LLM manager."""
    manager = AsyncMock(spec=FallbackManager)
    
    # Mock response from LLM
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "personas": [
            {
                "name": "Tech Enthusiasts",
                "demographics": {
                    "age_range": "25-34",
                    "gender_distribution": {"male": 0.65, "female": 0.32, "other": 0.03},
                    "income_level": "above average",
                    "education": "bachelor's degree or higher"
                },
                "behaviors": [
                    "Early technology adopters",
                    "High social media engagement",
                    "Research-driven purchase decisions"
                ],
                "interests": ["AI", "Gadgets", "Software Development", "Gaming"],
                "pain_points": ["Price sensitivity", "Feature complexity"],
                "engagement_channels": ["Twitter", "Tech blogs", "YouTube"],
                "confidence": 0.89
            },
            {
                "name": "Business Decision Makers",
                "demographics": {
                    "age_range": "35-54",
                    "gender_distribution": {"male": 0.55, "female": 0.44, "other": 0.01},
                    "income_level": "high",
                    "education": "advanced degrees"
                },
                "behaviors": [
                    "ROI-focused",
                    "Value long-term relationships",
                    "Seek expert opinions"
                ],
                "interests": ["Business Strategy", "Productivity", "Industry Trends"],
                "pain_points": ["Implementation complexity", "Team adoption"],
                "engagement_channels": ["LinkedIn", "Industry conferences", "Email"],
                "confidence": 0.86
            }
        ],
        "recommendations": [
            {
                "segment": "Tech Enthusiasts",
                "content_strategy": "Technical deep-dives and feature comparisons",
                "channels": ["Twitter", "YouTube", "Tech blogs"],
                "messaging": "Focus on innovation and technical specifications"
            },
            {
                "segment": "Business Decision Makers",
                "content_strategy": "Case studies and ROI analysis",
                "channels": ["LinkedIn", "Email newsletters", "Webinars"],
                "messaging": "Emphasize business value and implementation support"
            }
        ]
    })
    mock_response.confidence_score = 0.87
    
    manager.execute_with_fallback.return_value = mock_response
    return manager


@pytest.fixture
def mock_audience_data():
    """Create a mock audience data service."""
    service = AsyncMock(spec=AudienceDataService)
    
    # Mock audience data
    mock_data = {
        "segments": [
            {
                "id": 1,
                "name": "Tech Enthusiasts",
                "size": 250000,
                "demographics": {
                    "age_distribution": {"18-24": 0.15, "25-34": 0.45, "35-44": 0.25, "45+": 0.15},
                    "gender_distribution": {"male": 0.65, "female": 0.32, "other": 0.03},
                    "location_distribution": {"North America": 0.6, "Europe": 0.25, "Asia": 0.1, "Other": 0.05},
                    "income_levels": {"low": 0.1, "medium": 0.35, "high": 0.55}
                }
            },
            {
                "id": 2,
                "name": "Business Decision Makers",
                "size": 120000,
                "demographics": {
                    "age_distribution": {"18-24": 0.05, "25-34": 0.2, "35-44": 0.4, "45+": 0.35},
                    "gender_distribution": {"male": 0.55, "female": 0.44, "other": 0.01},
                    "location_distribution": {"North America": 0.5, "Europe": 0.3, "Asia": 0.15, "Other": 0.05},
                    "income_levels": {"low": 0.05, "medium": 0.25, "high": 0.7}
                }
            }
        ],
        "timeframe": "2025-01-01 to 2025-03-01",
        "data_completeness": 0.92
    }
    
    service.get_audience_data.return_value = mock_data
    service.calculate_data_quality = MagicMock(return_value=0.92)
    return service


@pytest.fixture
def mock_engagement_metrics():
    """Create a mock engagement metrics service."""
    service = AsyncMock(spec=EngagementMetricsService)
    
    # Mock engagement metrics
    mock_metrics = {
        "segments": [
            {
                "id": 1,
                "name": "Tech Enthusiasts",
                "engagement": {
                    "channels": {
                        "twitter": 0.75,
                        "youtube": 0.68,
                        "tech_blogs": 0.62,
                        "email": 0.45,
                        "linkedin": 0.38
                    },
                    "content_types": {
                        "technical_articles": 0.72,
                        "product_reviews": 0.68,
                        "tutorials": 0.65,
                        "case_studies": 0.48,
                        "webinars": 0.42
                    },
                    "time_patterns": {
                        "weekday_distribution": {"mon": 0.15, "tue": 0.18, "wed": 0.2, "thu": 0.22, "fri": 0.15, "sat": 0.05, "sun": 0.05},
                        "time_of_day": {"morning": 0.25, "afternoon": 0.35, "evening": 0.3, "night": 0.1}
                    }
                }
            },
            {
                "id": 2,
                "name": "Business Decision Makers",
                "engagement": {
                    "channels": {
                        "linkedin": 0.82,
                        "email": 0.75,
                        "webinars": 0.65,
                        "industry_conferences": 0.58,
                        "twitter": 0.42
                    },
                    "content_types": {
                        "case_studies": 0.78,
                        "whitepapers": 0.72,
                        "industry_reports": 0.68,
                        "webinars": 0.65,
                        "product_reviews": 0.48
                    },
                    "time_patterns": {
                        "weekday_distribution": {"mon": 0.22, "tue": 0.25, "wed": 0.2, "thu": 0.18, "fri": 0.12, "sat": 0.02, "sun": 0.01},
                        "time_of_day": {"morning": 0.4, "afternoon": 0.45, "evening": 0.12, "night": 0.03}
                    }
                }
            }
        ],
        "confidence": 0.88
    }
    
    service.get_engagement_metrics.return_value = mock_metrics
    service.analyze_patterns.return_value = {
        "segment_id": 1,
        "patterns": [
            {
                "type": "channel_preference",
                "description": "Strong preference for Twitter and YouTube",
                "confidence": 0.85
            },
            {
                "type": "content_preference",
                "description": "Technical content performs best",
                "confidence": 0.82
            },
            {
                "type": "timing",
                "description": "Highest engagement on weekdays, afternoons",
                "confidence": 0.78
            }
        ],
        "aggregate_confidence": 0.82
    }
    
    return service


@pytest.fixture
def audience_analysis_service(mock_llm_manager, mock_audience_data, mock_engagement_metrics):
    """Create an audience analysis service with mocked dependencies."""
    return AudienceAnalysisService(
        llm_manager=mock_llm_manager,
        audience_data_service=mock_audience_data,
        engagement_metrics_service=mock_engagement_metrics
    )


class TestAudienceAnalysisService:
    """Test cases for the AudienceAnalysisService."""
    
    @pytest.mark.asyncio
    async def test_analyze_with_chain_of_thought(self, audience_analysis_service):
        """Test audience analysis with chain-of-thought reasoning."""
        # Arrange
        company_id = 1
        segment_id = None  # All segments
        timeframe = "last_quarter"
        demographic_filters = {"age_range": ["25-34", "35-44"]}
        
        # Act
        result = await audience_analysis_service.analyze(
            company_id=company_id,
            segment_id=segment_id,
            timeframe=timeframe,
            demographic_filters=demographic_filters,
            with_chain_of_thought=True
        )
        
        # Assert
        assert "analysis" in result
        assert "confidence_score" in result
        assert "confidence_metrics" in result
        assert "reasoning" in result
        
        assert "personas" in result["analysis"]
        assert "recommendations" in result["analysis"]
        assert len(result["analysis"]["personas"]) == 2
        assert result["confidence_score"] > 0.8
        
        # Verify chain of thought was included
        assert "chain_id" in result["reasoning"]
        assert "steps" in result["reasoning"]
        assert len(result["reasoning"]["steps"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_without_chain_of_thought(self, audience_analysis_service):
        """Test audience analysis without chain-of-thought reasoning."""
        # Arrange
        company_id = 1
        segment_id = None  # All segments
        timeframe = "last_quarter"
        demographic_filters = {"age_range": ["25-34", "35-44"]}
        
        # Act
        result = await audience_analysis_service.analyze(
            company_id=company_id,
            segment_id=segment_id,
            timeframe=timeframe,
            demographic_filters=demographic_filters,
            with_chain_of_thought=False
        )
        
        # Assert
        assert "analysis" in result
        assert "confidence_score" in result
        assert "confidence_metrics" in result
        assert "reasoning" not in result
    
    @pytest.mark.asyncio
    async def test_analyze_specific_segment(self, audience_analysis_service):
        """Test audience analysis for a specific segment."""
        # Arrange
        company_id = 1
        segment_id = 1  # Tech Enthusiasts
        timeframe = "last_quarter"
        demographic_filters = {}
        
        # Act
        result = await audience_analysis_service.analyze(
            company_id=company_id,
            segment_id=segment_id,
            timeframe=timeframe,
            demographic_filters=demographic_filters
        )
        
        # Assert
        assert "analysis" in result
        assert "personas" in result["analysis"]
        # We should only have one persona since we specified a segment
        assert len(result["analysis"]["personas"]) == 1
        assert result["analysis"]["personas"][0]["name"] == "Tech Enthusiasts"
    
    @pytest.mark.asyncio
    async def test_fetch_audience_data(self, audience_analysis_service):
        """Test fetching audience data."""
        # Arrange
        company_id = 1
        segment_id = None
        timeframe = "last_quarter"
        demographic_filters = {"age_range": ["25-34", "35-44"]}
        
        # Act
        data, quality = await audience_analysis_service._fetch_audience_data(
            company_id=company_id,
            segment_id=segment_id,
            timeframe=timeframe,
            demographic_filters=demographic_filters
        )
        
        # Assert
        assert "segments" in data
        assert len(data["segments"]) == 2
        assert quality == 0.92
    
    @pytest.mark.asyncio
    async def test_analyze_engagement_patterns(self, audience_analysis_service):
        """Test analyzing engagement patterns."""
        # Arrange
        segment_id = 1
        
        # Act
        patterns, confidence = await audience_analysis_service._analyze_engagement_patterns(segment_id)
        
        # Assert
        assert "patterns" in patterns
        assert len(patterns["patterns"]) == 3
        assert confidence == 0.82
    
    @pytest.mark.asyncio
    async def test_generate_personas(self, audience_analysis_service):
        """Test generating audience personas."""
        # Arrange
        audience_data = {
            "segments": [
                {
                    "id": 1,
                    "name": "Tech Enthusiasts",
                    "demographics": {
                        "age_distribution": {"25-34": 0.45},
                        "gender_distribution": {"male": 0.65}
                    }
                }
            ]
        }
        engagement_patterns = {
            "segment_id": 1,
            "patterns": [
                {
                    "type": "channel_preference",
                    "description": "Strong preference for Twitter"
                }
            ]
        }
        report = Report(
            type="audience_analysis",
            parameters={"company_id": 1}
        )
        
        # Act
        personas, recommendations, confidence = await audience_analysis_service._generate_personas(
            audience_data=audience_data,
            engagement_patterns=engagement_patterns,
            report=report
        )
        
        # Assert
        assert len(personas) == 2
        assert personas[0]["name"] == "Tech Enthusiasts"
        assert len(recommendations) == 2
        assert confidence == 0.87
    
    def test_prepare_persona_prompt(self, audience_analysis_service):
        """Test preparing persona prompt."""
        # Arrange
        audience_data = {
            "segments": [
                {
                    "id": 1,
                    "name": "Tech Enthusiasts",
                    "demographics": {
                        "age_distribution": {"25-34": 0.45},
                        "gender_distribution": {"male": 0.65}
                    }
                }
            ]
        }
        engagement_patterns = {
            "segment_id": 1,
            "patterns": [
                {
                    "type": "channel_preference",
                    "description": "Strong preference for Twitter"
                }
            ]
        }
        
        # Act
        prompt = audience_analysis_service._prepare_persona_prompt(
            audience_data=audience_data,
            engagement_patterns=engagement_patterns
        )
        
        # Assert
        prompt_data = json.loads(prompt)
        assert prompt_data["task"] == "audience_persona_generation"
        assert "data" in prompt_data
        assert "audience_segments" in prompt_data["data"]
        assert "engagement_patterns" in prompt_data["data"]
        assert "requirements" in prompt_data
        assert "format" in prompt_data["requirements"]
    
    def test_parse_llm_response(self, audience_analysis_service):
        """Test parsing LLM response."""
        # Arrange
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "personas": [
                {
                    "name": "Tech Enthusiasts",
                    "demographics": {"age_range": "25-34"},
                    "behaviors": ["Early technology adopters"],
                    "confidence": 0.89
                }
            ],
            "recommendations": [
                {
                    "segment": "Tech Enthusiasts",
                    "content_strategy": "Technical deep-dives"
                }
            ]
        })
        
        # Act
        personas, recommendations = audience_analysis_service._parse_llm_response(mock_response)
        
        # Assert
        assert len(personas) == 1
        assert personas[0]["name"] == "Tech Enthusiasts"
        assert len(recommendations) == 1
        assert recommendations[0]["segment"] == "Tech Enthusiasts"
    
    def test_parse_llm_response_invalid_json(self, audience_analysis_service):
        """Test parsing invalid LLM response."""
        # Arrange
        mock_response = MagicMock()
        mock_response.content = "Invalid JSON"
        
        # Act
        personas, recommendations = audience_analysis_service._parse_llm_response(mock_response)
        
        # Assert
        assert len(personas) == 0
        assert len(recommendations) == 0
