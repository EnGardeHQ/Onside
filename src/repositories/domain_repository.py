"""
Domain Repository Module.

This module provides database operations for domain entities.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain import Domain


class DomainRepository:
    """Repository for domain-related database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize the repository with a database session.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def get_by_id(self, domain_id: int) -> Optional[Domain]:
        """Get a domain by ID.
        
        Args:
            domain_id: ID of the domain to retrieve
            
        Returns:
            Domain if found, None otherwise
        """
        result = await self.db.execute(
            select(Domain).where(Domain.id == domain_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_domain(self, domain: str) -> Optional[Domain]:
        """Get a domain by its name.
        
        Args:
            domain: Domain name to search for
            
        Returns:
            Domain if found, None otherwise
        """
        result = await self.db.execute(
            select(Domain).where(Domain.domain == domain)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company(self, company_id: int) -> List[Domain]:
        """Get all domains for a company.
        
        Args:
            company_id: ID of the company
            
        Returns:
            List of domains
        """
        result = await self.db.execute(
            select(Domain)
            .where(Domain.company_id == company_id)
            .order_by(Domain.is_primary.desc(), Domain.domain)
        )
        return result.scalars().all()
    
    async def create(self, domain: Domain) -> Domain:
        """Create a new domain.
        
        Args:
            domain: Domain to create
            
        Returns:
            Created domain
        """
        self.db.add(domain)
        await self.db.commit()
        await self.db.refresh(domain)
        return domain
    
    async def update(self, domain_id: int, update_data: Dict[str, Any]) -> Optional[Domain]:
        """Update a domain.
        
        Args:
            domain_id: ID of the domain to update
            update_data: Dictionary of fields to update
            
        Returns:
            Updated domain if found, None otherwise
        """
        result = await self.db.execute(
            update(Domain)
            .where(Domain.id == domain_id)
            .values(**update_data)
            .returning(Domain)
        )
        await self.db.commit()
        return result.scalar_one_or_none()
    
    async def delete(self, domain_id: int) -> bool:
        """Delete a domain.
        
        Args:
            domain_id: ID of the domain to delete
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            delete(Domain).where(Domain.id == domain_id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def set_primary_domain(self, company_id: int, domain_id: int) -> bool:
        """Set a domain as primary for a company.
        
        Args:
            company_id: ID of the company
            domain_id: ID of the domain to set as primary
            
        Returns:
            True if successful, False otherwise
        """
        # First, set all domains for this company as non-primary
        await self.db.execute(
            update(Domain)
            .where(Domain.company_id == company_id)
            .values(is_primary=False)
        )
        
        # Then set the specified domain as primary
        result = await self.db.execute(
            update(Domain)
            .where(and_(
                Domain.id == domain_id,
                Domain.company_id == company_id
            ))
            .values(is_primary=True)
            .returning(Domain)
        )
        
        await self.db.commit()
        return result.scalar_one_or_none() is not None
