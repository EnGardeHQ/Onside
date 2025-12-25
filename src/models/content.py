from datetime import datetime
from typing import Optional, List, Dict
import enum

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum, Float, JSON, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from src.database import Base
from src.models.user import User
from src.models.ai import AIInsight
from src.models.trend import TrendAnalysis
from src.models.engagement import EngagementMetrics

class InsightType(str, enum.Enum):
    """Enum for insight types."""
    SENTIMENT = "sentiment"
    TOPIC = "topic"
    ENGAGEMENT = "engagement"
    TREND = "trend"

class Content(Base):
    """Content model class."""
    __tablename__ = "contents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, index=True)
    content_text: Mapped[str] = mapped_column(String)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    content_metadata: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    decay_score: Mapped[float] = mapped_column(Float, default=1.0)
    last_engagement_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    trend_score: Mapped[float] = mapped_column(Float, default=0.0)
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    topic_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Relationships
    user = relationship("src.models.user.User", back_populates="contents")
    engagement_history = relationship("src.models.content.ContentEngagementHistory", back_populates="content")
    insights = relationship("src.models.ai.AIInsight", back_populates="content")
    trends = relationship(
        "src.models.trend.TrendAnalysis",
        secondary="content_trends",
        back_populates="contents"
    )
    engagement_metrics = relationship("src.models.engagement.EngagementMetrics", back_populates="content")

    def __init__(self, **kwargs):
        """Initialize Content model."""
        for key, value in kwargs.items():
            if key == 'text':  # Handle 'text' parameter as 'content_text'
                setattr(self, 'content_text', value)
            else:
                setattr(self, key, value)

    def __repr__(self) -> str:
        """String representation of the Content model."""
        return f"<Content(id={self.id}, title='{self.title}')>"

class ContentEngagementHistory(Base):
    """Content engagement history model class."""
    __tablename__ = "content_engagement_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("contents.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Relationships with fully qualified paths
    content = relationship("src.models.content.Content", back_populates="engagement_history")

content_trends = Table('content_trends', Base.metadata,
    Column('content_id', ForeignKey('contents.id'), primary_key=True),
    Column('trend_id', ForeignKey('trend_analyses.id'), primary_key=True)
)
