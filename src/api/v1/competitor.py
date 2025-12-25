"""
Competitor API endpoints for OnSide application.

This module provides endpoints for managing and analyzing competitors.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.competitor import Competitor
from src.schemas.competitor import CompetitorCreate, CompetitorResponse, CompetitorUpdate
from src.services.competitor_service import CompetitorService

router = APIRouter()

@router.post("/", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
async def create_competitor(
    competitor: CompetitorCreate,
    db: AsyncSession = Depends(get_db)
) -> CompetitorResponse:
    """Create a new competitor.
    
    Args:
        competitor: Competitor data to create
        db: Database session
        
    Returns:
        Created competitor
    """
    service = CompetitorService(db)
    return await service.create_competitor(competitor)

@router.get("/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(
    competitor_id: int,
    db: AsyncSession = Depends(get_db)
) -> CompetitorResponse:
    """Get a competitor by ID.
    
    Args:
        competitor_id: ID of the competitor to retrieve
        db: Database session
        
    Returns:
        Requested competitor
    """
    service = CompetitorService(db)
    competitor = await service.get_competitor(competitor_id)
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor with ID {competitor_id} not found"
        )
    return competitor

@router.get("/", response_model=List[CompetitorResponse])
async def list_competitors(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[CompetitorResponse]:
    """List all competitors with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of competitors
    """
    service = CompetitorService(db)
    return await service.list_competitors(skip=skip, limit=limit)

@router.put("/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(
    competitor_id: int,
    competitor_update: CompetitorUpdate,
    db: AsyncSession = Depends(get_db)
) -> CompetitorResponse:
    """Update a competitor.
    
    Args:
        competitor_id: ID of the competitor to update
        competitor_update: Competitor data to update
        db: Database session
        
    Returns:
        Updated competitor
    """
    service = CompetitorService(db)
    competitor = await service.update_competitor(competitor_id, competitor_update)
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor with ID {competitor_id} not found"
        )
    return competitor

@router.delete("/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_competitor(
    competitor_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a competitor.
    
    Args:
        competitor_id: ID of the competitor to delete
        db: Database session
    """
    service = CompetitorService(db)
    success = await service.delete_competitor(competitor_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor with ID {competitor_id} not found"
        )
