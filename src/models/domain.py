"""Domain model for tracking domains in the OnSide application."""
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.database import Base

# Handle circular imports
if TYPE_CHECKING:
    from .link import Link
    from .company import Company

class Domain(Base):
    """Model representing a domain in the system.
    
    Attributes:
        id: Primary key
        name: Domain name (e.g., 'example.com')
        is_active: Whether the domain is active
        is_primary: Whether this is the primary domain for the company
        company_id: Foreign key to the associated company
        created_at: Timestamp when the domain was created
        updated_at: Timestamp when the domain was last updated
        meta_data: Additional metadata about the domain
        links: Relationship to associated links
        company: Relationship to the associated company
    """
    __tablename__ = 'domains'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True)
    meta_data = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    links: Mapped[List["Link"]] = relationship("Link", back_populates="domain", cascade="all, delete-orphan")
    company: Mapped["Company"] = relationship("Company", back_populates="domains")
    
    def __repr__(self) -> str:
        return f"<Domain(id={self.id}, name='{self.name}', company_id={self.company_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert domain to dictionary.
        
        Returns:
            Dict containing domain attributes
        """
        return {
            "id": self.id,
            "name": self.name,
            "is_active": self.is_active,
            "is_primary": self.is_primary,
            "company_id": self.company_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "meta_data": self.meta_data
        }
        
    @property
    def domain(self) -> str:
        """Alias for name to maintain backward compatibility."""
        return self.name
        
    @domain.setter
    def domain(self, value: str) -> None:
        """Set the domain name."""
        self.name = value
