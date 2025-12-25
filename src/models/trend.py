"""Trend analysis model module."""
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Optional, List
from src.database import Base

class TrendAnalysis(Base):
    """Model for storing trend analysis results"""
    __tablename__ = "trend_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    trend_type: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    trend_data: Mapped[Dict] = mapped_column(JSON)
    trend_score: Mapped[float] = mapped_column(Float, nullable=False)
    trend_metadata: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Many-to-many relationship with Content
    contents = relationship(
        "Content",
        secondary="content_trends",
        back_populates="trends"
    )

    def __repr__(self):
        return f"<TrendAnalysis(id={self.id}, trend_type='{self.trend_type}')>"
