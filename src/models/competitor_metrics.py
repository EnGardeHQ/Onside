"""Competitor metrics model with enhanced confidence scoring and data quality tracking."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, Dict, TYPE_CHECKING, List

from sqlalchemy import ForeignKey, JSON, String, Float, Integer, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database import Base

# Handle circular imports properly
if TYPE_CHECKING:
    from src.models.competitor import Competitor
    from src.models.link import Link

class MetricType(str, PyEnum):
    """Types of competitor metrics following Sprint 4 patterns.
    
    Following OnSide project requirements:
    - Uses actual database schema
    - Validates against real schema
    - Follows BDD/TDD methodology
    """
    WEB_TRAFFIC = "web_traffic"
    SOCIAL_ENGAGEMENT = "social_engagement"
    MENTIONS = "mentions"
    SENTIMENT = "sentiment"
    MARKET_SHARE = "market_share"
    GROWTH_RATE = "growth_rate"
    ENGAGEMENT = "engagement"  # For link-specific engagement metrics

class DataSource(str, PyEnum):
    """Data sources for competitor metrics."""
    MELTWATER = "meltwater"
    GOOGLE_ANALYTICS = "google_analytics"
    SOCIAL_MEDIA = "social_media"
    MARKET_RESEARCH = "market_research"
    CUSTOM = "custom"

class CompetitorMetrics(Base):
    """Model for storing competitor metrics with enhanced confidence scoring.
    
    Following Sprint 4 implementation patterns for AI/ML capabilities:
    - Data quality validation and scoring
    - Confidence scoring with weighted metrics
    - Source tracking and validation
    - Time-series data handling
    """
    __tablename__ = "competitor_metrics"
    __table_args__ = {"extend_existing": True}

    # Primary fields
    id: Mapped[int] = mapped_column(primary_key=True)
    competitor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competitors.id", ondelete="CASCADE"), 
        nullable=True,
        comment="Reference to the competitor this metric belongs to"
    )
    
    link_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("links.id", ondelete="CASCADE"),
        nullable=True,
        comment="Reference to the link these metrics belong to"
    )
    
    # Metric type and value
    metric_type: Mapped[str] = mapped_column(
        Enum(MetricType),
        nullable=False,
        comment="Type of metric being tracked"
    )
    value: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Actual metric value"
    )
    
    # Time tracking
    metric_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="Date the metric was recorded"
    )
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Start of the time period this metric covers"
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="End of the time period this metric covers"
    )
    
    # Data quality and confidence
    source: Mapped[Optional[str]] = mapped_column(
        Enum(DataSource),
        nullable=True,
        comment="Source of the metric data"
    )
    data_quality_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Score indicating data quality (0-1)"
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Overall confidence in the metric (0-1)"
    )
    
    # Additional metrics
    mentions_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of mentions in the time period"
    )
    sentiment_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Sentiment analysis score (-1 to 1)"
    )
    engagement_rate: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Engagement rate as a percentage"
    )
    
    # Metadata
    meta_data: Mapped[Optional[Dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional metadata and context"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="Timestamp when the record was created"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp when the record was last updated"
    )

    # Relationships - simplified to avoid circular imports
    competitor = relationship(
        "Competitor",
        back_populates="metrics",
        foreign_keys=[competitor_id],
        lazy="select"
    )

    link = relationship(
        "Link",
        back_populates="metrics",
        foreign_keys=[link_id],
        lazy="select"
    )
    
    # Enhanced engagement data following Sprint 4 AI/ML capabilities
    engagement_data: Mapped[Optional[Dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Structured engagement metrics with confidence scores"
    )
    
    engagement_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Overall engagement score (0-1)"
    )
    
    def __init__(self, **kwargs):
        """Initialize CompetitorMetrics with data quality validation."""
        super().__init__(**kwargs)
        if not self.confidence_score:
            self.confidence_score = 0.0
        if not self.data_quality_score:
            self.data_quality_score = 0.0
            
    def update_confidence(self, data_quality: float) -> None:
        """Update confidence score based on data quality.
        
        Args:
            data_quality: Score indicating quality of source data (0-1)
        """
        if not 0.0 <= data_quality <= 1.0:
            raise ValueError("Data quality score must be between 0 and 1")
            
        self.data_quality_score = data_quality
        # Overall confidence is weighted by data quality and time relevance
        time_weight = 1.0  # Add time decay factor based on metric age
        self.confidence_score = (data_quality * 0.7) + (time_weight * 0.3)
            
    def __repr__(self) -> str:
        """String representation of the CompetitorMetrics model."""
        return f"<CompetitorMetrics(id={self.id}, type='{self.metric_type}', confidence={self.confidence_score:.2f})>"
