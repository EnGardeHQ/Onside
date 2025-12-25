"""Search History model for tracking search queries and analytics."""
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy import ForeignKey, JSON, DateTime, String, Integer, Float, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.database import Base


class SearchHistory(Base):
    """Model for tracking user search queries and analytics.

    This model stores all search activity to enable search analytics,
    trending queries, and user behavior insights.
    """
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"), nullable=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    search_type: Mapped[str] = mapped_column(String(50), nullable=False)
    filters: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    results_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    execution_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()")

    # Relationships
    user = relationship("User", back_populates="search_history")
    company = relationship("Company", back_populates="search_history")

    def __repr__(self) -> str:
        """String representation."""
        return f"<SearchHistory(id={self.id}, query='{self.query[:50]}...', type='{self.search_type}')>"
