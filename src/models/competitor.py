from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional, Dict, TYPE_CHECKING
from src.database import Base

# Handle circular imports properly
if TYPE_CHECKING:
    from src.models.company import Company
    from src.models.competitor_metrics import CompetitorMetrics
    from src.models.competitor_content import CompetitorContent

class Competitor(Base):
    """Model for tracking competitors"""
    __tablename__ = "competitors"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    market_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow, nullable=True)
    meta_data: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)

    # Foreign keys
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    
    # Relationships - using string literals for forward references
    company = relationship(
        "Company", 
        back_populates="competitors", 
        foreign_keys=[company_id],
        lazy="select"
    )
    metrics = relationship(
        "CompetitorMetrics", 
        back_populates="competitor", 
        cascade="all, delete-orphan",
        lazy="select"
    )
    content = relationship(
        "CompetitorContent",
        back_populates="competitor",
        cascade="all, delete-orphan",
        lazy="select"
    )
    scraped_content = relationship(
        "ScrapedContent",
        back_populates="competitor",
        lazy="select"
    )
    scraping_schedules = relationship(
        "ScrapingSchedule",
        back_populates="competitor",
        lazy="select"
    )
