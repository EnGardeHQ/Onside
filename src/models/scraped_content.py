"""Models for web scraping and content tracking."""
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy import ForeignKey, JSON, DateTime, String, Integer, Float, Text, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
import hashlib

from src.database import Base


class ScrapedContent(Base):
    """Model for storing scraped web content with versioning.

    This model stores HTML content, screenshots, and metadata from web scraping
    operations, supporting version tracking and change detection.
    """
    __tablename__ = "scraped_content"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    domain: Mapped[str] = mapped_column(String(500), nullable=False)
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"), nullable=True)
    competitor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("competitors.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    html_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    screenshot_url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scrape_duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    content_metadata: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()")

    # Relationships
    company = relationship("Company", back_populates="scraped_content")
    competitor = relationship("Competitor", back_populates="scraped_content")
    old_version_changes = relationship(
        "ContentChange",
        foreign_keys="ContentChange.old_version_id",
        back_populates="old_version"
    )
    new_version_changes = relationship(
        "ContentChange",
        foreign_keys="ContentChange.new_version_id",
        back_populates="new_version"
    )

    def calculate_content_hash(self) -> str:
        """Calculate SHA-256 hash of the content.

        Returns:
            str: Hexadecimal hash string
        """
        content = self.text_content or self.html_content or ""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def update_hash(self) -> None:
        """Update the content_hash field."""
        self.content_hash = self.calculate_content_hash()

    def has_changed(self, other: 'ScrapedContent') -> bool:
        """Check if content has changed compared to another version.

        Args:
            other: Another ScrapedContent instance to compare

        Returns:
            bool: True if content has changed
        """
        return self.content_hash != other.content_hash

    def __repr__(self) -> str:
        """String representation."""
        return f"<ScrapedContent(id={self.id}, url='{self.url}', version={self.version})>"


class ScrapingSchedule(Base):
    """Model for scheduling automated web scraping tasks.

    This model supports cron-style scheduling for web scraping with
    configurable options for screenshots and custom scraping behavior.
    """
    __tablename__ = "scraping_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"), nullable=True)
    competitor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("competitors.id"), nullable=True)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    capture_screenshot: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    scraping_config: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()", onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="scraping_schedules")
    competitor = relationship("Competitor", back_populates="scraping_schedules")

    def __repr__(self) -> str:
        """String representation."""
        return f"<ScrapingSchedule(id={self.id}, name='{self.name}', url='{self.url}')>"


class ContentChange(Base):
    """Model for tracking changes between versions of scraped content.

    This model stores diff information when content changes are detected,
    enabling change tracking and alerting functionality.
    """
    __tablename__ = "content_changes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    old_version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scraped_content.id"), nullable=True)
    new_version_id: Mapped[int] = mapped_column(ForeignKey("scraped_content.id"), nullable=False)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    diff_data: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    change_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()")

    # Relationships
    old_version = relationship(
        "ScrapedContent",
        foreign_keys=[old_version_id],
        back_populates="old_version_changes"
    )
    new_version = relationship(
        "ScrapedContent",
        foreign_keys=[new_version_id],
        back_populates="new_version_changes"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<ContentChange(id={self.id}, type='{self.change_type}', change={self.change_percentage}%)>"
