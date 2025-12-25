"""
Models for link search and web scraping functionality
"""
from datetime import datetime
from typing import Dict, Optional, List, TYPE_CHECKING, Any
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from src.database import Base

# Handle circular imports properly
if TYPE_CHECKING:
    from .domain import Domain
    from .competitor_metrics import CompetitorMetrics
    from .link_snapshot import LinkSnapshot

class Link(Base):
    """Model for storing links discovered during domain seeding and link search.
    
    Attributes:
        id: Primary key
        url: The full URL of the link
        domain_id: Foreign key to the associated domain
        title: Title of the linked page
        description: Description of the linked page
        discovered_at: When the link was first discovered
        last_checked: When the link was last checked
        status_code: HTTP status code from the last check
        is_active: Whether the link is currently active
        meta_data: Additional metadata about the link
    """
    __tablename__ = 'links'

    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False, unique=True, index=True)
    domain_id = Column(Integer, ForeignKey('domains.id', ondelete='CASCADE'), nullable=False)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_checked = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    status_code = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    meta_data = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    snapshots: Mapped[List["LinkSnapshot"]] = relationship(
        "LinkSnapshot", 
        back_populates="link", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    domain: Mapped["Domain"] = relationship(
        "Domain", 
        back_populates="links",
        lazy="selectin"
    )
    
    metrics: Mapped[List["CompetitorMetrics"]] = relationship(
        "CompetitorMetrics", 
        back_populates="link", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Link(id={self.id}, url='{self.url}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert link to dictionary."""
        return {
            "id": self.id,
            "url": self.url,
            "domain_id": self.domain_id,
            "title": self.title,
            "description": self.description,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "status_code": self.status_code,
            "is_active": self.is_active,
            "meta_data": self.meta_data
        }

class LinkSnapshot(Base):
    """Model for storing snapshots of link content over time.
    
    Attributes:
        id: Primary key
        link_id: Foreign key to the associated link
        captured_at: When the snapshot was taken
        content_html: Raw HTML content of the page
        content_text: Extracted text content of the page
        meta_data: Additional metadata about the snapshot
        http_headers: HTTP headers from the response
        screenshot_path: Path to the screenshot file (if any)
    """
    __tablename__ = 'link_snapshots'

    id = Column(Integer, primary_key=True)
    link_id = Column(Integer, ForeignKey('links.id', ondelete='CASCADE'), nullable=False)
    captured_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    content_html = Column(Text, nullable=True)
    content_text = Column(Text, nullable=True)
    http_headers = Column(JSON, nullable=True)
    screenshot_path = Column(String, nullable=True)
    meta_data = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    link: Mapped["Link"] = relationship(
        "Link", 
        back_populates="snapshots",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<LinkSnapshot(id={self.id}, link_id={self.link_id}, captured_at={self.captured_at})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            "id": self.id,
            "link_id": self.link_id,
            "captured_at": self.captured_at.isoformat() if self.captured_at else None,
            "content_length": len(self.content_html) if self.content_html else 0,
            "text_length": len(self.content_text) if self.content_text else 0,
            "has_screenshot": bool(self.screenshot_path),
            "meta_data": self.meta_data
        }

# Domain and Company models have been moved to their own files:
# - src/models/domain.py
# - src/models/company.py
