"""Test module for report models.

This module contains tests for the Report and LLMFallback models, focusing on
Sprint 4 requirements for AI/ML enhancements and chain-of-thought reasoning.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.models.report import Report, ReportType, ReportStatus
from src.models.llm_fallback import LLMFallback, LLMProvider, FallbackReason


@pytest.fixture
def sample_report(db_session: Session) -> Report:
    """Create a sample report for testing.
    
    Args:
        db_session (Session): SQLAlchemy database session
        
    Returns:
        Report: Sample report instance
    """
    report = Report(
        user_id=1,
        type=ReportType.SENTIMENT,
        parameters={
            "content_id": 123,
            "with_reasoning": True
        }
    )
    db_session.add(report)
    db_session.commit()
    return report


@pytest.fixture
def sample_fallback(db_session: Session, sample_report: Report) -> LLMFallback:
    """Create a sample LLM fallback record for testing.
    
    Args:
        db_session (Session): SQLAlchemy database session
        sample_report (Report): Sample report to associate with
        
    Returns:
        LLMFallback: Sample fallback instance
    """
    fallback = LLMFallback(
        report_id=sample_report.id,
        attempt_number=1,
        original_provider=LLMProvider.OPENAI,
        fallback_provider=LLMProvider.ANTHROPIC,
        reason=FallbackReason.TIMEOUT,
        original_prompt="Test prompt"
    )
    db_session.add(fallback)
    db_session.commit()
    return fallback


def test_report_parameter_validation(sample_report: Report):
    """Test report parameter validation logic."""
    # Valid parameters
    assert sample_report.validate_parameters() is True
    
    # Missing required parameter
    sample_report.parameters = {"content_id": 123}
    assert sample_report.validate_parameters() is False
    
    # No parameters
    sample_report.parameters = None
    assert sample_report.validate_parameters() is False


def test_report_chain_of_thought(sample_report: Report):
    """Test recording of chain-of-thought reasoning."""
    reasoning = {
        "steps": [
            {"step": 1, "description": "Analyze sentiment", "confidence": 0.9},
            {"step": 2, "description": "Extract key phrases", "confidence": 0.85}
        ],
        "decisions": ["positive sentiment", "business context"],
        "fallback_attempts": 0,
        "conclusion": "Overall positive sentiment with business focus"
    }
    
    sample_report.record_chain_of_thought(reasoning)
    assert sample_report.chain_of_thought["steps"] == reasoning["steps"]
    assert sample_report.chain_of_thought["final_conclusion"] == reasoning["conclusion"]
    assert "timestamp" in sample_report.chain_of_thought


def test_report_confidence_update(sample_report: Report):
    """Test confidence score updates with validation."""
    metrics = {
        "sentiment_confidence": 0.85,
        "entity_confidence": 0.9,
        "overall_quality": "high"
    }
    
    sample_report.update_confidence(0.875, metrics)
    assert sample_report.confidence_score == 0.875
    assert sample_report.result["confidence_metrics"] == metrics
    
    with pytest.raises(ValueError):
        sample_report.update_confidence(1.5)


def test_report_completion_tracking(sample_report: Report):
    """Test report completion with processing time."""
    processing_time = 2.5
    sample_report.complete_with_time(processing_time)
    
    assert sample_report.status == ReportStatus.COMPLETED
    assert sample_report.processing_time == processing_time
    assert (datetime.utcnow() - sample_report.updated_at) < timedelta(seconds=1)


def test_llm_fallback_tracking(sample_report: Report, db_session: Session):
    """Test LLM fallback tracking and metrics."""
    # Track first fallback
    sample_report.track_llm_fallback(
        original_provider="openai",
        fallback_provider="anthropic",
        reason="timeout",
        prompt="Test prompt 1"
    )
    
    assert sample_report.fallback_count == 1
    assert len(sample_report.llm_fallbacks) == 1
    
    # Add another fallback
    sample_report.track_llm_fallback(
        original_provider="anthropic",
        fallback_provider="cohere",
        reason="low_confidence",
        prompt="Test prompt 2"
    )
    
    assert sample_report.fallback_count == 2
    assert len(sample_report.llm_fallbacks) == 2
    
    # Update fallback metrics
    latest_fallback = sample_report.llm_fallbacks[-1]
    latest_fallback.complete_with_metrics(success=True, latency_ms=250)
    db_session.commit()
    
    # Check fallback summary
    summary = sample_report.get_fallback_summary()
    assert summary["total_fallbacks"] == 2
    assert "cohere" in summary["providers_used"]
    assert len(summary["common_reasons"]) > 0


def test_llm_fallback_chain_of_thought(sample_fallback: LLMFallback):
    """Test chain-of-thought logging in fallback attempts."""
    steps = [
        {
            "step": 1,
            "action": "Attempt primary LLM",
            "result": "Timeout after 5s",
            "next_action": "Switch to fallback"
        },
        {
            "step": 2,
            "action": "Initialize fallback LLM",
            "result": "Successfully initialized",
            "next_action": "Process original prompt"
        }
    ]
    
    sample_fallback.record_chain_of_thought(steps)
    assert sample_fallback.chain_of_thought["steps"] == steps
    assert sample_fallback.chain_of_thought["attempt_number"] == sample_fallback.attempt_number
    assert sample_fallback.chain_of_thought["provider"] == sample_fallback.fallback_provider.value
