"""LLM fallback tracking model module.

This module provides models for tracking LLM fallback attempts and chain-of-thought reasoning
logs as part of the Sprint 4 AI/ML enhancements.
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, Optional, List
from sqlalchemy import ForeignKey, JSON, DateTime, String, Enum, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.database import Base


class FallbackReason(PyEnum):
    """Enumeration of reasons for LLM fallback."""
    TIMEOUT = "timeout"
    ERROR = "error"
    LOW_CONFIDENCE = "low_confidence"
    INVALID_RESPONSE = "invalid_response"
    RATE_LIMIT = "rate_limit"


class LLMProvider(PyEnum):
    """Enumeration of LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    FALLBACK = "fallback"


class LLMFallback(Base):
    """Model for tracking LLM fallback attempts and chain-of-thought reasoning.
    
    This model supports the Sprint 4 requirement for fallback mechanisms in LLM calls
    and logging of chain-of-thought outputs for traceability.
    
    Attributes:
        id (int): Primary key for the fallback record
        report_id (int): Foreign key to the associated report
        attempt_number (int): Sequential number of the fallback attempt
        original_provider (LLMProvider): Original LLM provider that failed
        fallback_provider (LLMProvider): Provider used for fallback
        reason (FallbackReason): Reason for falling back to alternative provider
        original_prompt (str): Original prompt sent to the LLM
        chain_of_thought (Dict): Logged reasoning steps and decision process
        success (bool): Whether the fallback attempt was successful
        latency_ms (int): Response time in milliseconds
        created_at (datetime): Timestamp of the fallback attempt
    """
    __tablename__ = "llm_fallbacks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    original_provider: Mapped[LLMProvider] = mapped_column(Enum(LLMProvider), nullable=False)
    fallback_provider: Mapped[LLMProvider] = mapped_column(Enum(LLMProvider), nullable=False)
    reason: Mapped[FallbackReason] = mapped_column(Enum(FallbackReason), nullable=False)
    original_prompt: Mapped[str] = mapped_column(String, nullable=False)
    chain_of_thought: Mapped[Dict] = mapped_column(JSON, nullable=True)
    success: Mapped[bool] = mapped_column(nullable=False, default=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Define relationships
    report = relationship("Report", back_populates="llm_fallbacks")

    def record_chain_of_thought(self, steps: List[Dict]) -> None:
        """Record the chain-of-thought reasoning steps.
        
        Args:
            steps (List[Dict]): List of reasoning steps, each containing the step description
                              and any relevant metadata
        """
        self.chain_of_thought = {
            "timestamp": datetime.utcnow().isoformat(),
            "steps": steps,
            "attempt_number": self.attempt_number,
            "provider": self.fallback_provider.value
        }

    def complete_with_metrics(self, success: bool, latency_ms: int) -> None:
        """Record completion metrics for the fallback attempt.
        
        Args:
            success (bool): Whether the fallback attempt was successful
            latency_ms (int): Response time in milliseconds
        """
        self.success = success
        self.latency_ms = latency_ms

    def __repr__(self) -> str:
        """String representation of the LLMFallback model.
        
        Returns:
            str: String representation of the fallback record
        """
        return (
            f"<LLMFallback(id={self.id}, report_id={self.report_id}, "
            f"from={self.original_provider.value}, to={self.fallback_provider.value}, "
            f"success={self.success})>"
        )
