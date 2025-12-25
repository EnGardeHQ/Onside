"""AI models module."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, Optional
from sqlalchemy import ForeignKey, JSON, DateTime, Float, String, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.database import Base
from src.models.user import User

class InsightType(PyEnum):
    """Insight type enumeration."""
    TOPIC = "topic"
    SENTIMENT = "sentiment"
    AUDIENCE = "audience"
    ENGAGEMENT = "engagement"

class AIInsight(Base):
    """AI insight model."""
    __tablename__ = "ai_insights"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("contents.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[InsightType] = mapped_column(Enum(InsightType), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    insight_metadata: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Define relationships
    content: Mapped["Content"] = relationship("Content", back_populates="insights")
    user: Mapped["User"] = relationship("User", back_populates="insights")

    def __repr__(self) -> str:
        """String representation of the AIInsight model."""
        return f"<AIInsight(id={self.id}, type={self.type}, score={self.score})>"
