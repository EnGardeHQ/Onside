"""Test module for LLM provider and fallback manager.

This module tests the Sprint 4 implementation of LLM service management,
including fallback mechanisms, rate limiting, and performance tracking.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import asyncio

from src.services.llm_provider import FallbackManager, ProviderConfig
from src.models.llm_fallback import LLMProvider, FallbackReason
from src.models.report import Report, ReportType, ReportStatus


@pytest.fixture
def fallback_manager():
    """Create a FallbackManager instance for testing."""
    return FallbackManager()


@pytest.fixture
def mock_report():
    """Create a mock report instance."""
    report = MagicMock(spec=Report)
    report.id = 1
    report.type = ReportType.CONTENT
    report.status = ReportStatus.PROCESSING
    report.parameters = {
        "content_id": 123,
        "analysis_depth": 2,
        "with_chain_of_thought": True
    }
    return report


async def test_successful_llm_call(fallback_manager, mock_report):
    """Test successful LLM call with primary provider."""
    prompt = "Test prompt for content analysis"
    result, provider = await fallback_manager.execute_with_fallback(
        prompt=prompt,
        report=mock_report,
        initial_provider=LLMProvider.OPENAI
    )
    
    assert provider == LLMProvider.OPENAI
    assert result["confidence_score"] >= 0.7
    assert "steps" in result["reasoning"]
    assert fallback_manager.metrics[LLMProvider.OPENAI]["success_count"] == 1


async def test_fallback_on_timeout(fallback_manager, mock_report):
    """Test fallback to alternative provider on timeout."""
    with patch.object(
        fallback_manager,
        "_execute_llm_call",
        side_effect=[asyncio.TimeoutError, MagicMock(return_value={
            "text": "Fallback response",
            "confidence_score": 0.8,
            "reasoning": {"steps": []}
        })]
    ):
        result, provider = await fallback_manager.execute_with_fallback(
            prompt="Test prompt",
            report=mock_report,
            initial_provider=LLMProvider.OPENAI
        )
        
        assert provider == LLMProvider.ANTHROPIC
        mock_report.track_llm_fallback.assert_called_once_with(
            original_provider="openai",
            fallback_provider="anthropic",
            reason="timeout",
            prompt="Test prompt"
        )


async def test_fallback_on_low_confidence(fallback_manager, mock_report):
    """Test fallback when confidence score is below threshold."""
    with patch.object(
        fallback_manager,
        "_execute_llm_call",
        side_effect=[
            {"text": "Low confidence", "confidence_score": 0.5, "reasoning": {"steps": []}},
            {"text": "High confidence", "confidence_score": 0.9, "reasoning": {"steps": []}}
        ]
    ):
        result, provider = await fallback_manager.execute_with_fallback(
            prompt="Test prompt",
            report=mock_report,
            confidence_threshold=0.7
        )
        
        assert provider == LLMProvider.ANTHROPIC
        assert result["confidence_score"] >= 0.7
        mock_report.track_llm_fallback.assert_called_once_with(
            original_provider="openai",
            fallback_provider="anthropic",
            reason="low_confidence",
            prompt="Test prompt"
        )


async def test_rate_limit_handling(fallback_manager, mock_report):
    """Test rate limit handling and provider switching."""
    config = fallback_manager.providers[LLMProvider.OPENAI]
    config.rate_limit = 2
    config.current_rate = 2
    
    result, provider = await fallback_manager.execute_with_fallback(
        prompt="Test prompt",
        report=mock_report,
        initial_provider=LLMProvider.OPENAI
    )
    
    assert provider == LLMProvider.ANTHROPIC
    mock_report.track_llm_fallback.assert_called_once()
    assert mock_report.track_llm_fallback.call_args[1]["reason"] == "error"


async def test_multiple_provider_failures(fallback_manager, mock_report):
    """Test handling of multiple provider failures."""
    with patch.object(
        fallback_manager,
        "_execute_llm_call",
        side_effect=[
            asyncio.TimeoutError,
            Exception("API Error"),
            {"text": "Success", "confidence_score": 0.8, "reasoning": {"steps": []}}
        ]
    ):
        result, provider = await fallback_manager.execute_with_fallback(
            prompt="Test prompt",
            report=mock_report
        )
        
        assert provider == LLMProvider.COHERE
        assert mock_report.track_llm_fallback.call_count == 2
        assert result["confidence_score"] >= 0.7


async def test_all_providers_fail(fallback_manager, mock_report):
    """Test handling when all providers fail."""
    with patch.object(
        fallback_manager,
        "_execute_llm_call",
        side_effect=asyncio.TimeoutError
    ):
        with pytest.raises(Exception) as exc_info:
            await fallback_manager.execute_with_fallback(
                prompt="Test prompt",
                report=mock_report
            )
        
        assert "All providers failed" in str(exc_info.value)
        assert mock_report.track_llm_fallback.call_count == len(LLMProvider) - 1


def test_provider_metrics(fallback_manager):
    """Test provider performance metrics tracking."""
    provider = LLMProvider.OPENAI
    
    # Simulate successful calls
    fallback_manager._update_metrics(provider, True, 0.5)
    fallback_manager._update_metrics(provider, True, 0.7)
    
    # Simulate failed call
    fallback_manager._update_metrics(provider, False, 0)
    
    metrics = fallback_manager.get_provider_metrics()[provider.value]
    assert metrics["success_rate"] == 2/3
    assert 0.5 <= metrics["avg_latency"] <= 0.7
    assert metrics["total_requests"] == 3
    assert metrics["failure_count"] == 1


def test_rate_limit_reset(fallback_manager):
    """Test rate limit counter reset after time window."""
    provider = LLMProvider.OPENAI
    config = fallback_manager.providers[provider]
    
    # Set up rate limit scenario
    config.rate_limit = 5
    config.current_rate = 5
    config.last_reset = datetime.utcnow() - timedelta(minutes=2)
    
    # Check rate limit
    assert fallback_manager._check_rate_limit(provider) is True
    assert config.current_rate == 1


async def test_chain_of_thought_logging(fallback_manager, mock_report):
    """Test chain-of-thought reasoning is properly logged."""
    result, provider = await fallback_manager.execute_with_fallback(
        prompt="Test prompt for reasoning",
        report=mock_report,
        initial_provider=LLMProvider.OPENAI
    )
    
    assert "reasoning" in result
    assert "steps" in result["reasoning"]
    assert len(result["reasoning"]["steps"]) > 0
    assert all("description" in step for step in result["reasoning"]["steps"])
