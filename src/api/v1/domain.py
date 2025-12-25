"""
Domain API endpoints for OnSide application.

This module provides endpoints for managing domains.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.domain import (
    DomainCreate, 
    DomainUpdate, 
    DomainResponse,
    DomainListResponse
)
from src.services.domain_service import DomainService
from src.exceptions import DomainValidationError

router = APIRouter()

@router.post(
    "/", 
    response_model=DomainResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new domain",
    response_description="The created domain"
)
async def create_domain(
    domain: DomainCreate,
    db: AsyncSession = Depends(get_db)
) -> DomainResponse:
    """Create a new domain.
    
    - **domain**: Domain data to create
    
    Returns the created domain with its ID and timestamps.
    """
    service = DomainService(db)
    try:
        return await service.create_domain(domain)
    except DomainValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/{domain_id}", 
    response_model=DomainResponse,
    summary="Get a domain by ID",
    response_description="The requested domain"
)
async def get_domain(
    domain_id: int,
    db: AsyncSession = Depends(get_db)
) -> DomainResponse:
    """Get a domain by its ID.
    
    - **domain_id**: ID of the domain to retrieve
    
    Returns the domain details if found, otherwise returns 404.
    """
    service = DomainService(db)
    domain = await service.get_domain(domain_id)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain with ID {domain_id} not found"
        )
    return domain

@router.get(
    "/lookup/{domain_name}", 
    response_model=DomainResponse,
    summary="Get a domain by name",
    response_description="The requested domain"
)
async def get_domain_by_name(
    domain_name: str,
    db: AsyncSession = Depends(get_db)
) -> DomainResponse:
    """Get a domain by its name.
    
    - **domain_name**: Name of the domain to retrieve (e.g., example.com)
    
    Returns the domain details if found, otherwise returns 404.
    """
    service = DomainService(db)
    domain = await service.get_domain_by_name(domain_name)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{domain_name}' not found"
        )
    return domain

@router.get(
    "/", 
    response_model=DomainListResponse,
    summary="List domains",
    response_description="List of domains with pagination"
)
async def list_domains(
    company_id: Optional[int] = Query(
        None, 
        description="Filter by company ID"
    ),
    is_active: Optional[bool] = Query(
        None, 
        description="Filter by active status"
    ),
    skip: int = Query(
        0, 
        ge=0, 
        description="Number of records to skip"
    ),
    limit: int = Query(
        100, 
        ge=1, 
        le=1000,
        description="Maximum number of records to return"
    ),
    db: AsyncSession = Depends(get_db)
) -> DomainListResponse:
    """List domains with optional filtering and pagination.
    
    - **company_id**: Filter by company ID
    - **is_active**: Filter by active status
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (max 1000)
    
    Returns a paginated list of domains.
    """
    service = DomainService(db)
    domains = await service.list_domains(
        company_id=company_id,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    
    # Get total count for pagination
    total = len(domains)  # This is a simplified version; in a real app, you'd get the total count from the DB
    
    return DomainListResponse(
        items=domains,
        total=total,
        skip=skip,
        limit=limit
    )

@router.put(
    "/{domain_id}", 
    response_model=DomainResponse,
    summary="Update a domain",
    response_description="The updated domain"
)
async def update_domain(
    domain_id: int,
    domain_update: DomainUpdate,
    db: AsyncSession = Depends(get_db)
) -> DomainResponse:
    """Update a domain.
    
    - **domain_id**: ID of the domain to update
    - **domain_update**: Domain data to update
    
    Returns the updated domain if found, otherwise returns 404.
    """
    service = DomainService(db)
    try:
        updated_domain = await service.update_domain(domain_id, domain_update)
        if not updated_domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain with ID {domain_id} not found"
            )
        return updated_domain
    except DomainValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete(
    "/{domain_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a domain",
    response_description="Domain deleted"
)
async def delete_domain(
    domain_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a domain.
    
    - **domain_id**: ID of the domain to delete
    
    Returns 204 No Content if successful, 404 if domain not found.
    """
    service = DomainService(db)
    success = await service.delete_domain(domain_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain with ID {domain_id} not found"
        )

@router.post(
    "/{domain_id}/set-primary",
    response_model=DomainResponse,
    summary="Set a domain as primary",
    response_description="The updated domain"
)
async def set_primary_domain(
    domain_id: int,
    company_id: int = Query(..., description="ID of the company"),
    db: AsyncSession = Depends(get_db)
) -> DomainResponse:
    """Set a domain as primary for a company.
    
    - **domain_id**: ID of the domain to set as primary
    - **company_id**: ID of the company
    
    Returns the updated domain if successful, otherwise returns 404.
    """
    service = DomainService(db)
    success = await service.set_primary_domain(company_id, domain_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to set domain {domain_id} as primary for company {company_id}"
        )
    
    # Return the updated domain
    domain = await service.get_domain(domain_id)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain with ID {domain_id} not found"
        )
    return domain
