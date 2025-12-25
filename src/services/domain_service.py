"""
Domain Service for OnSide application.

This module provides business logic for managing domains.
"""
import re
import tldextract
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain import Domain
from src.schemas.domain import DomainCreate, DomainUpdate, DomainResponse
from src.repositories.domain_repository import DomainRepository
from src.exceptions import DomainValidationError

class DomainService:
    """Service for handling domain-related operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the service with a database session.
        
        Args:
            db: Database session
        """
        self.db = db
        self.repository = DomainRepository(db)
    
    @staticmethod
    def normalize_domain(domain: str) -> str:
        """Normalize a domain name.
        
        Args:
            domain: Domain name to normalize
            
        Returns:
            Normalized domain name
            
        Raises:
            DomainValidationError: If the domain is invalid
        """
        if not domain:
            raise DomainValidationError("Domain cannot be empty")
        
        # Extract domain and suffix using tldextract
        extracted = tldextract.extract(domain.lower().strip())
        
        if not extracted.domain or not extracted.suffix:
            raise DomainValidationError(f"Invalid domain format: {domain}")
        
        # Rebuild the domain from parts to ensure consistency
        normalized_domain = f"{extracted.domain}.{extracted.suffix}"
        
        # Basic validation of the normalized domain
        if not re.match(r"^[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,}$", normalized_domain):
            raise DomainValidationError(f"Invalid domain format: {normalized_domain}")
        
        return normalized_domain
    
    async def create_domain(self, domain_data: DomainCreate) -> DomainResponse:
        """Create a new domain.
        
        Args:
            domain_data: Domain data to create
            
        Returns:
            Created domain
            
        Raises:
            DomainValidationError: If domain validation fails
        """
        # Normalize the domain
        normalized_domain = self.normalize_domain(domain_data.domain)
        
        # Check if domain already exists
        existing_domain = await self.repository.get_by_domain(normalized_domain)
        if existing_domain:
            raise DomainValidationError(f"Domain already exists: {normalized_domain}")
        
        # Create new domain
        db_domain = Domain(
            domain=normalized_domain,
            is_active=domain_data.is_active,
            is_primary=domain_data.is_primary,
            company_id=domain_data.company_id,
            metadata_=domain_data.metadata
        )
        
        # If this is set as primary, ensure no other primary exists for this company
        if domain_data.is_primary and domain_data.company_id:
            await self.repository.set_primary_domain(
                company_id=domain_data.company_id,
                domain_id=0  # Will be updated after creation
            )
        
        created_domain = await self.repository.create(db_domain)
        
        # If this is set as primary, update the domain ID
        if domain_data.is_primary and domain_data.company_id:
            await self.repository.set_primary_domain(
                company_id=domain_data.company_id,
                domain_id=created_domain.id
            )
            # Refresh to get the updated domain
            created_domain = await self.repository.get_by_id(created_domain.id)
        
        return DomainResponse.from_orm(created_domain)
    
    async def get_domain(self, domain_id: int) -> Optional[DomainResponse]:
        """Get a domain by ID.
        
        Args:
            domain_id: ID of the domain to retrieve
            
        Returns:
            Domain if found, None otherwise
        """
        domain = await self.repository.get_by_id(domain_id)
        if domain:
            return DomainResponse.from_orm(domain)
        return None
    
    async def get_domain_by_name(self, domain_name: str) -> Optional[DomainResponse]:
        """Get a domain by its name.
        
        Args:
            domain_name: Name of the domain to retrieve
            
        Returns:
            Domain if found, None otherwise
        """
        normalized_domain = self.normalize_domain(domain_name)
        domain = await self.repository.get_by_domain(normalized_domain)
        if domain:
            return DomainResponse.from_orm(domain)
        return None
    
    async def list_domains(
        self, 
        company_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[DomainResponse]:
        """List domains with optional filtering.
        
        Args:
            company_id: Filter by company ID
            is_active: Filter by active status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of domains
        """
        query = select(Domain)
        
        if company_id is not None:
            query = query.where(Domain.company_id == company_id)
        
        if is_active is not None:
            query = query.where(Domain.is_active == is_active)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        domains = result.scalars().all()
        return [DomainResponse.from_orm(domain) for domain in domains]
    
    async def update_domain(
        self, 
        domain_id: int, 
        domain_update: DomainUpdate
    ) -> Optional[DomainResponse]:
        """Update a domain.
        
        Args:
            domain_id: ID of the domain to update
            domain_update: Domain data to update
            
        Returns:
            Updated domain if found, None otherwise
        """
        update_data = domain_update.dict(exclude_unset=True)
        
        # If updating the domain name, normalize it
        if 'domain' in update_data:
            update_data['domain'] = self.normalize_domain(update_data['domain'])
        
        # If setting as primary, update primary domain
        if update_data.get('is_primary', False):
            domain = await self.repository.get_by_id(domain_id)
            if domain and domain.company_id:
                await self.repository.set_primary_domain(
                    company_id=domain.company_id,
                    domain_id=domain_id
                )
                # Remove from update data as it's already handled
                update_data.pop('is_primary', None)
        
        if update_data:  # Only update if there are fields to update
            updated_domain = await self.repository.update(domain_id, update_data)
        else:
            updated_domain = await self.repository.get_by_id(domain_id)
        
        if updated_domain:
            return DomainResponse.from_orm(updated_domain)
        return None
    
    async def delete_domain(self, domain_id: int) -> bool:
        """Delete a domain.
        
        Args:
            domain_id: ID of the domain to delete
            
        Returns:
            True if deleted, False if not found
        """
        return await self.repository.delete(domain_id)
    
    async def set_primary_domain(self, company_id: int, domain_id: int) -> bool:
        """Set a domain as primary for a company.
        
        Args:
            company_id: ID of the company
            domain_id: ID of the domain to set as primary
            
        Returns:
            True if successful, False otherwise
        """
        return await self.repository.set_primary_domain(company_id, domain_id)
