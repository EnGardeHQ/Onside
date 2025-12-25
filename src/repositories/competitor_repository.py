"""Competitor Repository Module.

This module provides database operations for competitor entities.
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.competitor import Competitor


class CompetitorRepository:
    """Repository for competitor-related database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize the repository with a database session.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def get_by_id(self, competitor_id: int) -> Optional[Competitor]:
        """Get a competitor by ID.
        
        Args:
            competitor_id: ID of the competitor to retrieve
            
        Returns:
            Competitor if found, None otherwise
        """
        result = await self.db.execute(
            select(Competitor).where(Competitor.id == competitor_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_id(self, company_id: int) -> List[Competitor]:
        """Get all competitors for a company.
        
        Args:
            company_id: ID of the company
            
        Returns:
            List of competitors
        """
        result = await self.db.execute(
            select(Competitor).where(Competitor.company_id == company_id)
        )
        return result.scalars().all()
    
    async def get_by_domain(self, domain: str) -> Optional[Competitor]:
        """Get a competitor by domain.
        
        Args:
            domain: Domain of the competitor
            
        Returns:
            Competitor if found, None otherwise
        """
        result = await self.db.execute(
            select(Competitor).where(Competitor.domain == domain)
        )
        return result.scalar_one_or_none()
    
    async def create(self, competitor: Competitor) -> Competitor:
        """Create a new competitor.
        
        Args:
            competitor: Competitor to create
            
        Returns:
            Created competitor
        """
        self.db.add(competitor)
        await self.db.commit()
        await self.db.refresh(competitor)
        return competitor
    
    async def update(self, competitor: Competitor) -> Competitor:
        """Update an existing competitor.
        
        Args:
            competitor: Competitor to update
            
        Returns:
            Updated competitor
        """
        await self.db.commit()
        await self.db.refresh(competitor)
        return competitor
    
    async def delete(self, competitor: Competitor) -> None:
        """Delete a competitor.
        
        Args:
            competitor: Competitor to delete
        """
        await self.db.delete(competitor)
        await self.db.commit()
