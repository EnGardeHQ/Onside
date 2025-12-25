"""
Pydantic models for domain-related requests and responses.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, HttpUrl, validator


class DomainBase(BaseModel):
    """Base model for domain data."""
    domain: str = Field(..., description="Domain name (e.g., example.com)", max_length=255)
    is_active: bool = Field(True, description="Whether the domain is active")
    is_primary: bool = Field(False, description="Whether this is the primary domain for the company")
    company_id: Optional[int] = Field(None, description="ID of the company this domain belongs to")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata about the domain"
    )


class DomainCreate(DomainBase):
    """Model for creating a new domain."""
    pass


class DomainUpdate(BaseModel):
    """Model for updating an existing domain."""
    domain: Optional[str] = Field(None, description="Domain name (e.g., example.com)", max_length=255)
    is_active: Optional[bool] = Field(None, description="Whether the domain is active")
    is_primary: Optional[bool] = Field(None, description="Whether this is the primary domain for the company")
    company_id: Optional[int] = Field(None, description="ID of the company this domain belongs to")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata about the domain"
    )


class DomainResponse(DomainBase):
    """Model for domain response."""
    id: int = Field(..., description="Unique identifier for the domain")
    created_at: datetime = Field(..., description="When the domain was created")
    updated_at: datetime = Field(..., description="When the domain was last updated")

    class Config:
        """Pydantic config."""
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "domain": "example.com",
                "is_active": True,
                "is_primary": True,
                "company_id": 1,
                "metadata": {"registrar": "GoDaddy", "expires_at": "2024-01-01"},
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }


class DomainListResponse(BaseModel):
    """Model for a list of domains response."""
    items: List[DomainResponse] = Field(..., description="List of domains")
    total: int = Field(..., description="Total number of domains")
    skip: int = Field(..., description="Number of domains skipped")
    limit: int = Field(..., description="Maximum number of domains returned")

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "domain": "example.com",
                        "is_active": True,
                        "is_primary": True,
                        "company_id": 1,
                        "metadata": {"registrar": "GoDaddy"},
                        "created_at": "2023-01-01T00:00:00",
                        "updated_at": "2023-01-01T00:00:00"
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 10
            }
        }
