"""AI Insight model for storing LLM-generated insights with confidence scoring and chain-of-thought reasoning."""
from datetime import datetime
from typing import Optional, Dict
from enum import Enum

from sqlalchemy import String, DateTime, Float, JSON, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database import Base

class InsightType(str, Enum):
    """Types of AI insights following Sprint 4 patterns."""
    COMPETITOR = "competitor"  # Competitor analysis insights
    MARKET = "market"         # Market analysis insights
    AUDIENCE = "audience"     # Audience analysis insights
    TREND = "trend"          # Trend analysis insights

class AIInsight(Base):
    """AI Insight model for storing LLM-generated insights with enhanced confidence scoring.
    
    Following Sprint 4 implementation patterns for AI/ML capabilities:
    - Chain-of-thought reasoning for competitor insights
    - Data quality and confidence scoring
    - Structured insights for trends and recommendations
    - Fallback mechanisms for robust operation
    """
    __tablename__ = "ai_insights"
    __table_args__ = {'extend_existing': True}

    # Primary fields
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    content_id: Mapped[int] = mapped_column(ForeignKey("contents.id"), nullable=False)
    insight_type: Mapped[str] = mapped_column(SQLEnum(InsightType), nullable=False)
    
    # AI/ML specific fields
    insight_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    reasoning_chain: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True, 
        comment="Chain-of-thought reasoning steps for insight generation")
    data_quality_score: Mapped[float] = mapped_column(Float, default=0.0,
        comment="Input data quality score (0-1)")
    prediction_confidence: Mapped[float] = mapped_column(Float, default=0.0,
        comment="ML prediction confidence (0-1)")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0,
        comment="Overall weighted confidence score (0-1)")
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False,
        comment="Whether fallback mechanism was used")
    insight_metadata: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True,
        comment="Additional insight metadata and context")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("src.auth.models.User", back_populates="insights")
    content = relationship("src.models.content.Content", back_populates="insights")

    def __init__(self, **kwargs):
        """Initialize AIInsight model with enhanced confidence scoring."""
        super().__init__(**kwargs)
        # Initialize confidence scores
        if not self.confidence_score:
            self.confidence_score = 0.0
        if not self.data_quality_score:
            self.data_quality_score = 0.0
        if not self.prediction_confidence:
            self.prediction_confidence = 0.0
            
    def update_confidence(self, data_quality: float, prediction_confidence: float) -> None:
        """Update confidence scores with validation.
        
        Args:
            data_quality: Score for input data quality (0-1)
            prediction_confidence: Score for ML prediction confidence (0-1)
        """
        if not (0.0 <= data_quality <= 1.0 and 0.0 <= prediction_confidence <= 1.0):
            raise ValueError("Scores must be between 0 and 1")
            
        self.data_quality_score = data_quality
        self.prediction_confidence = prediction_confidence
        # Overall confidence is weighted average of data quality and prediction confidence
        self.confidence_score = (data_quality * 0.4) + (prediction_confidence * 0.6)
            
    def __repr__(self) -> str:
        """String representation of the AI Insight model."""
        return f"<AIInsight(id={self.id}, type='{self.insight_type}', confidence={self.confidence_score:.2f})>"
