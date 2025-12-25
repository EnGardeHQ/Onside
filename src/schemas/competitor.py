"""
Pydantic models for competitor-related requests and responses.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl

class CompetitorBase(BaseModel):
    """Base model for competitor data."""
    name: str = Field(..., description="Name of the competitor")
    domain: str = Field(..., description="Competitor's domain name")
    description: Optional[str] = Field(None, description="Description of the competitor")
    market_share: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=100.0,
        description="Market share percentage (0-100)"
    )
    website: Optional[HttpUrl] = Field(None, description="Competitor's website URL")
    logo_url: Optional[HttpUrl] = Field(None, description="URL to the competitor's logo")
    industry: Optional[str] = Field(None, description="Industry the competitor operates in")
    location: Optional[str] = Field(None, description="Geographic location")
    founded_year: Optional[int] = Field(None, description="Year the company was founded")
    employee_count: Optional[int] = Field(None, description="Number of employees")
    revenue: Optional[float] = Field(None, description="Annual revenue in USD")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata about the competitor"
    )

class CompetitorCreate(CompetitorBase):
    """Model for creating a new competitor."""
    pass

class CompetitorUpdate(BaseModel):
    """Model for updating an existing competitor."""
    name: Optional[str] = Field(None, description="Name of the competitor")
    domain: Optional[str] = Field(None, description="Competitor's domain name")
    description: Optional[str] = Field(None, description="Description of the competitor")
    market_share: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=100.0,
        description="Market share percentage (0-100)"
    )
    website: Optional[HttpUrl] = Field(None, description="Competitor's website URL")
    logo_url: Optional[HttpUrl] = Field(None, description="URL to the competitor's logo")
    industry: Optional[str] = Field(None, description="Industry the competitor operates in")
    location: Optional[str] = Field(None, description="Geographic location")
    founded_year: Optional[int] = Field(None, description="Year the company was founded")
    employee_count: Optional[int] = Field(None, description="Number of employees")
    revenue: Optional[float] = Field(None, description="Annual revenue in USD")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata about the competitor"
    )

class CompetitorResponse(CompetitorBase):
    """Model for competitor response."""
    id: int = Field(..., description="Unique identifier for the competitor")
    created_at: datetime = Field(..., description="When the competitor was created")
    updated_at: datetime = Field(..., description="When the competitor was last updated")

    class Config:
        """Pydantic config."""
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Example Competitor",
                "domain": "example.com",
                "description": "A leading competitor in the example industry",
                "market_share": 15.5,
                "website": "https://example.com",
                "logo_url": "https://example.com/logo.png",
                "industry": "Technology",
                "location": "San Francisco, CA",
                "founded_year": 2010,
                "employee_count": 250,
                "revenue": 50000000.0,
                "metadata": {
                    "key": "value"
                },
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
