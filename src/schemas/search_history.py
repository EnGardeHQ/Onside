"""Pydantic schemas for Search History API endpoints."""
from datetime import datetime
from typing import Dict, Optional, Any, List
from pydantic import BaseModel, Field


class SearchHistoryBase(BaseModel):
    """Base schema for search history."""
    query: str = Field(..., min_length=1, description="Search query")
    search_type: str = Field(..., description="Type of search performed")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters applied")
    results_count: Optional[int] = Field(None, ge=0, description="Number of results returned")
    execution_time_ms: Optional[float] = Field(None, ge=0, description="Query execution time in milliseconds")
    language: Optional[str] = Field(None, max_length=5, description="Search language")


class SearchHistoryCreate(SearchHistoryBase):
    """Schema for creating search history record."""
    company_id: Optional[int] = Field(None, description="Company ID")
    ip_address: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")


class SearchHistoryResponse(SearchHistoryBase):
    """Schema for search history response."""
    id: int
    user_id: int
    company_id: Optional[int]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    class Config:
        """Pydantic config."""
        orm_mode = True


class SearchHistoryListResponse(BaseModel):
    """Schema for list of search history records."""
    searches: List[SearchHistoryResponse]
    total: int
    page: int
    page_size: int


class SearchAnalyticsResponse(BaseModel):
    """Schema for search analytics."""
    total_searches: int
    unique_queries: int
    avg_execution_time_ms: float
    top_queries: List[Dict[str, Any]]
    search_types_distribution: Dict[str, int]
    searches_by_hour: Dict[int, int]
    searches_by_day: Dict[str, int]
    avg_results_count: float


class CleanupResponse(BaseModel):
    """Schema for cleanup operation response."""
    deleted_count: int
    message: str
