from datetime import datetime
from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict
from src.database import Base

class CompetitorContent(Base):
    """Model for storing competitor content"""
    __tablename__ = "competitor_content"

    id: Mapped[int] = mapped_column(primary_key=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(nullable=False, unique=True)
    title: Mapped[Optional[str]] = mapped_column(nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(nullable=True)  # e.g., blog, news, social
    publish_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    discovered_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_updated: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    engagement_metrics: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)  # likes, shares, comments
    content_metrics: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)  # readability, sentiment, etc.
    meta_data: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    competitor: Mapped["Competitor"] = relationship("Competitor", back_populates="content")
