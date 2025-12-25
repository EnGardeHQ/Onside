"""
Company model for the OnSide application.
"""
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from src.database import Base

# Handle circular imports
if TYPE_CHECKING:
    from .domain import Domain
    from .competitor import Competitor
    from .report import Report


class Company(Base):
    """
    Company model representing a business entity in the system.
    """
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    meta_data = mapped_column(JSON, default=dict, nullable=False)
    
    # Relationships
    domains: Mapped[List["Domain"]] = relationship(
        "Domain", 
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    competitors: Mapped[List["Competitor"]] = relationship(
        "Competitor", 
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    email_recipients = relationship(
        "EmailRecipient",
        back_populates="company",
        lazy="select"
    )

    search_history = relationship(
        "SearchHistory",
        back_populates="company",
        lazy="select"
    )

    report_schedules = relationship(
        "ReportSchedule",
        back_populates="company",
        lazy="select"
    )

    scraped_content = relationship(
        "ScrapedContent",
        back_populates="company",
        lazy="select"
    )

    scraping_schedules = relationship(
        "ScrapingSchedule",
        back_populates="company",
        lazy="select"
    )

    @property
    def primary_domain(self) -> Optional["Domain"]:
        """Get the primary domain for this company if set."""
        for domain in self.domains:
            if domain.is_primary:
                return domain
        return None

    def __repr__(self) -> str:
        return f"<Company {self.name} ({self.domain})>"
