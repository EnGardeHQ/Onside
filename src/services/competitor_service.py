"""
Competitor Service for OnSide application.

This module provides business logic for managing and analyzing competitors.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from src.models.competitor import Competitor
from src.schemas.competitor import CompetitorCreate, CompetitorResponse, CompetitorUpdate
from src.repositories.competitor_repository import CompetitorRepository

class CompetitorService:
    """Service for handling competitor-related operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the service with a database session.
        
        Args:
            db: Database session
        """
        self.db = db
        self.repository = CompetitorRepository(db)
    
    async def create_competitor(self, competitor: CompetitorCreate) -> CompetitorResponse:
        """Create a new competitor.
        
        Args:
            competitor: Competitor data to create
            
        Returns:
            Created competitor
        """
        db_competitor = Competitor(**competitor.dict())
        self.db.add(db_competitor)
        await self.db.commit()
        await self.db.refresh(db_competitor)
        return CompetitorResponse.from_orm(db_competitor)
    
    async def get_competitor(self, competitor_id: int) -> Optional[CompetitorResponse]:
        """Get a competitor by ID.
        
        Args:
            competitor_id: ID of the competitor to retrieve
            
        Returns:
            Competitor if found, None otherwise
        """
        competitor = await self.repository.get_by_id(competitor_id)
        if competitor:
            return CompetitorResponse.from_orm(competitor)
        return None
    
    async def list_competitors(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[CompetitorResponse]:
        """List all competitors with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of competitors
        """
        result = await self.db.execute(
            select(Competitor).offset(skip).limit(limit)
        )
        competitors = result.scalars().all()
        return [CompetitorResponse.from_orm(comp) for comp in competitors]
    
    async def update_competitor(
        self, 
        competitor_id: int, 
        competitor_update: CompetitorUpdate
    ) -> Optional[CompetitorResponse]:
        """Update a competitor.
        
        Args:
            competitor_id: ID of the competitor to update
            competitor_update: Competitor data to update
            
        Returns:
            Updated competitor if found, None otherwise
        """
        result = await self.db.execute(
            select(Competitor).where(Competitor.id == competitor_id)
        )
        db_competitor = result.scalar_one_or_none()
        
        if not db_competitor:
            return None
            
        update_data = competitor_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_competitor, field, value)
            
        await self.db.commit()
        await self.db.refresh(db_competitor)
        return CompetitorResponse.from_orm(db_competitor)
    
    async def delete_competitor(self, competitor_id: int) -> bool:
        """Delete a competitor.
        
        Args:
            competitor_id: ID of the competitor to delete
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            delete(Competitor).where(Competitor.id == competitor_id)
        )
        await self.db.commit()
        return result.rowcount > 0
