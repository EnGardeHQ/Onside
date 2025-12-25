"""Pydantic schemas for Link Deduplication API endpoints."""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator


class DetectDuplicatesRequest(BaseModel):
    """Schema for detect duplicates request."""
    company_id: Optional[int] = Field(None, description="Company ID to scope search")
    similarity_threshold: float = Field(0.85, ge=0.0, le=1.0, description="Similarity threshold (0-1)")
    include_inactive: bool = Field(False, description="Include inactive links")

    @validator('similarity_threshold')
    def validate_threshold(cls, v):
        """Validate similarity threshold."""
        if v < 0.0 or v > 1.0:
            raise ValueError("Similarity threshold must be between 0 and 1")
        return v


class DuplicateLinkGroup(BaseModel):
    """Schema for a group of duplicate links."""
    normalized_url: str
    similarity_score: float
    link_ids: List[int]
    urls: List[str]
    titles: List[Optional[str]]


class DetectDuplicatesResponse(BaseModel):
    """Schema for detect duplicates response."""
    total_links_analyzed: int
    duplicate_groups_found: int
    duplicate_groups: List[DuplicateLinkGroup]


class MergeDuplicatesRequest(BaseModel):
    """Schema for merge duplicates request."""
    primary_link_id: int = Field(..., description="ID of link to keep")
    duplicate_link_ids: List[int] = Field(..., min_items=1, description="IDs of links to merge")
    merge_metadata: bool = Field(True, description="Merge metadata from duplicates")
    merge_tags: bool = Field(True, description="Merge tags from duplicates")

    @validator('duplicate_link_ids')
    def validate_duplicates(cls, v, values):
        """Validate duplicate link IDs."""
        if 'primary_link_id' in values and values['primary_link_id'] in v:
            raise ValueError("Primary link ID cannot be in duplicate list")
        return v


class MergeDuplicatesResponse(BaseModel):
    """Schema for merge duplicates response."""
    message: str
    primary_link_id: int
    merged_count: int
    deleted_link_ids: List[int]


class DuplicateReportResponse(BaseModel):
    """Schema for duplicate report response."""
    generated_at: str
    total_links: int
    unique_links: int
    duplicate_links: int
    duplication_rate: float
    duplicate_groups: List[DuplicateLinkGroup]
    recommendations: List[str]


class LinkNormalizationResponse(BaseModel):
    """Schema for link normalization response."""
    original_url: str
    normalized_url: str
    changes_made: List[str]
