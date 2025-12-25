"""Company Repository Module.

This module provides database operations for company entities.
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.company import Company


class CompanyRepository:
    """Repository for company-related database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize the repository with a database session.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def get_by_id(self, company_id: int) -> Optional[Company]:
        """Get a company by ID.
        
        Args:
            company_id: ID of the company to retrieve
            
        Returns:
            Company if found, None otherwise
        """
        result = await self.db.execute(
            select(Company).where(Company.id == company_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_domain(self, domain: str) -> Optional[Company]:
        """Get a company by domain.
        
        Args:
            domain: Domain of the company
            
        Returns:
            Company if found, None otherwise
        """
        result = await self.db.execute(
            select(Company).where(Company.domain == domain)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self) -> List[Company]:
        """Get all companies.
        
        Returns:
            List of all companies
        """
        result = await self.db.execute(select(Company))
        return result.scalars().all()
    
    async def create(self, company: Company) -> Company:
        """Create a new company.
        
        Args:
            company: Company to create
            
        Returns:
            Created company
        """
        self.db.add(company)
        await self.db.commit()
        await self.db.refresh(company)
        return company
    
    async def update(self, company: Company) -> Company:
        """Update an existing company.
        
        Args:
            company: Company to update
            
        Returns:
            Updated company
        """
        await self.db.commit()
        await self.db.refresh(company)
        return company
    
    async def delete(self, company: Company) -> None:
        """Delete a company.
        
        Args:
            company: Company to delete
        """
        await self.db.delete(company)
        await self.db.commit()
