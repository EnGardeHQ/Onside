"""Report models module."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, Optional, List
from sqlalchemy import ForeignKey, JSON, DateTime, String, Enum, Float, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.database import Base
from src.models.user import User


class ReportStatus(PyEnum):
    """Report status enumeration."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportType(PyEnum):
    """Report type enumeration."""
    CONTENT = "content"
    SENTIMENT = "sentiment"
    COMPETITOR = "competitor"
    MARKET = "market"
    AUDIENCE = "audience"
    TEMPORAL = "temporal"
    SEO = "seo"


class Report(Base):
    """Report model for tracking report generation jobs.
    
    This model supports various report types including content analysis, sentiment analysis,
    competitor intelligence, market analysis, audience insights, temporal analysis, and SEO metrics.
    It includes support for AI/ML enhancements with chain-of-thought reasoning and confidence scoring.
    
    Attributes:
        id (int): Primary key for the report
        user_id (int): Foreign key to the user who created the report
        type (ReportType): Type of report (content, sentiment, competitor, etc.)
        status (ReportStatus): Current status of the report generation
        parameters (Dict): Input parameters for the report generation
        result (Optional[Dict]): Generated report results
        error_message (Optional[str]): Error message if report generation failed
        chain_of_thought (Optional[Dict]): AI reasoning steps and decision process
        confidence_score (Optional[float]): AI confidence in the report results (0-1)
        processing_time (Optional[float]): Time taken to generate the report in seconds
        created_at (datetime): Timestamp when the report was created
        updated_at (datetime): Timestamp when the report was last updated
    """
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), default=ReportStatus.QUEUED)
    parameters: Mapped[Dict] = mapped_column(JSON, nullable=True)
    result: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    chain_of_thought: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    processing_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Define relationships with fully qualified module paths
    user = relationship(
        "src.models.user.User",
        back_populates="reports",
        lazy="select"
    )
    company = relationship(
        "src.models.company.Company",
        back_populates="reports",
        lazy="select"
    )
    llm_fallbacks = relationship("LLMFallback", back_populates="report")
    progress_tracker = relationship("src.models.progress.ProgressTracker", back_populates="report", uselist=False)
    email_deliveries = relationship(
        "EmailDelivery",
        back_populates="report",
        lazy="select"
    )
    schedule_executions = relationship(
        "ScheduleExecution",
        back_populates="report",
        lazy="select"
    )

    # Fallback tracking
    fallback_count: Mapped[int] = mapped_column(Integer, default=0)
    last_fallback_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def validate_parameters(self) -> bool:
        """Validate report parameters based on report type.
        
        Returns:
            bool: True if parameters are valid, False otherwise
        """
        required_params = {
            ReportType.CONTENT: ["content_id", "analysis_depth"],
            ReportType.SENTIMENT: ["content_id", "with_reasoning"],
            ReportType.COMPETITOR: ["competitor_id", "timeframe"],
            ReportType.MARKET: ["company_id", "timeframe"],
            ReportType.AUDIENCE: ["company_id", "segment_id"],
            ReportType.TEMPORAL: ["content_id", "timeframe"],
            ReportType.SEO: ["content_id", "enhanced"]
        }
        
        if not self.parameters:
            return False
            
        return all(param in self.parameters for param in required_params.get(self.type, []))
    
    def record_chain_of_thought(self, reasoning: Dict) -> None:
        """Record AI chain-of-thought reasoning process.
        
        Args:
            reasoning (Dict): Dictionary containing AI reasoning steps and decision process
        """
        self.chain_of_thought = {
            "timestamp": datetime.utcnow().isoformat(),
            "steps": reasoning.get("steps", []),
            "decisions": reasoning.get("decisions", []),
            "fallback_attempts": reasoning.get("fallback_attempts", 0),
            "final_conclusion": reasoning.get("conclusion")
        }
    
    def update_confidence(self, score: float, metrics: Optional[Dict] = None) -> None:
        """Update AI confidence score and related metrics.
        
        Args:
            score (float): Confidence score between 0 and 1
            metrics (Optional[Dict]): Additional confidence-related metrics
        """
        if not 0 <= score <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
            
        self.confidence_score = score
        if metrics:
            if not self.result:
                self.result = {}
            self.result["confidence_metrics"] = metrics
    
    def complete_with_time(self, processing_time_seconds: float) -> None:
        """Mark report as complete and record processing time.
        
        Args:
            processing_time_seconds (float): Time taken to generate the report in seconds
        """
        self.status = ReportStatus.COMPLETED
        self.processing_time = processing_time_seconds
        self.updated_at = datetime.utcnow()
        
    def track_llm_fallback(self, original_provider: str, fallback_provider: str,
                          reason: str, prompt: str) -> None:
        """Track an LLM fallback attempt.
        
        This method supports the Sprint 4 requirement for tracking LLM fallbacks
        and maintaining traceability of AI operations.
        
        Args:
            original_provider (str): The LLM provider that failed
            fallback_provider (str): The provider used as fallback
            reason (str): Reason for the fallback
            prompt (str): Original prompt that triggered the fallback
        """
        from src.models.llm_fallback import LLMFallback, LLMProvider, FallbackReason
        
        self.fallback_count += 1
        self.last_fallback_at = datetime.utcnow()
        
        fallback = LLMFallback(
            report_id=self.id,
            attempt_number=self.fallback_count,
            original_provider=LLMProvider(original_provider),
            fallback_provider=LLMProvider(fallback_provider),
            reason=FallbackReason(reason),
            original_prompt=prompt
        )
        
        self.llm_fallbacks.append(fallback)
        
    def get_fallback_summary(self) -> Dict:
        """Get a summary of LLM fallbacks for this report.
        
        Returns:
            Dict: Summary of fallback attempts and their outcomes
        """
        if not self.llm_fallbacks:
            return {
                "total_fallbacks": 0,
                "success_rate": None,
                "avg_latency": None
            }
            
        successful = sum(1 for f in self.llm_fallbacks if f.success)
        total = len(self.llm_fallbacks)
        
        latencies = [f.latency_ms for f in self.llm_fallbacks if f.latency_ms is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else None
        
        return {
            "total_fallbacks": total,
            "success_rate": successful / total if total > 0 else 0,
            "avg_latency": avg_latency,
            "providers_used": list(set(f.fallback_provider.value for f in self.llm_fallbacks)),
            "common_reasons": self._get_common_fallback_reasons()
        }
        
    def _get_common_fallback_reasons(self) -> List[Dict]:
        """Get the most common reasons for fallbacks.
        
        Returns:
            List[Dict]: List of reasons and their frequencies
        """
        if not self.llm_fallbacks:
            return []
            
        reason_counts = {}
        for fallback in self.llm_fallbacks:
            reason = fallback.reason.value
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            
        return [
            {"reason": reason, "count": count}
            for reason, count in sorted(
                reason_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ]
    
    def __repr__(self) -> str:
        """String representation of the Report model.
        
        Returns:
            str: String representation of the report
        """
        return f"<Report(id={self.id}, type={self.type}, status={self.status}, confidence={self.confidence_score:.2f} if self.confidence_score else None)>"
