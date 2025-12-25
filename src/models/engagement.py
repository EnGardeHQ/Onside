"""Engagement metrics models module."""
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy import ForeignKey, JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.database import Base

class EngagementMetrics(Base):
    """Engagement metrics model."""
    __tablename__ = "engagement_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("contents.id"), nullable=False)
    metric_type: Mapped[str] = mapped_column(String, nullable=False)
    metric_value: Mapped[int] = mapped_column(Integer, nullable=False)
    metric_metadata: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Define relationships
    content: Mapped["Content"] = relationship("Content", back_populates="engagement_metrics")

    def __repr__(self) -> str:
        """String representation of the EngagementMetrics model."""
        return f"<EngagementMetrics(id={self.id}, content_id={self.content_id}, type={self.metric_type})>"
