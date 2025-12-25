"""Pydantic schemas for Web Scraping API endpoints."""
from datetime import datetime
from typing import Dict, Optional, Any, List
from pydantic import BaseModel, Field, HttpUrl, validator


class ScrapeRequest(BaseModel):
    """Schema for scraping request."""
    url: str = Field(..., description="URL to scrape")
    company_id: Optional[int] = Field(None, description="Company ID")
    competitor_id: Optional[int] = Field(None, description="Competitor ID")
    capture_screenshot: bool = Field(True, description="Capture screenshot")
    wait_for_selector: Optional[str] = Field(None, description="CSS selector to wait for")
    timeout: int = Field(30000, ge=1000, le=120000, description="Timeout in milliseconds")

    @validator('url')
    def validate_url(cls, v):
        """Validate URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v


class ScrapedContentResponse(BaseModel):
    """Schema for scraped content response."""
    id: int
    url: str
    domain: str
    company_id: Optional[int]
    competitor_id: Optional[int]
    version: int
    title: Optional[str]
    meta_description: Optional[str]
    meta_keywords: Optional[str]
    screenshot_url: Optional[str]
    screenshot_path: Optional[str]
    content_hash: Optional[str]
    status_code: Optional[int]
    error_message: Optional[str]
    scrape_duration_ms: Optional[float]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        """Pydantic config."""
        orm_mode = True


class ScrapedContentDetailResponse(ScrapedContentResponse):
    """Schema for scraped content with text content."""
    text_content: Optional[str]
    html_content: Optional[str]


class ScrapedContentListResponse(BaseModel):
    """Schema for list of scraped content."""
    content: List[ScrapedContentResponse]
    total: int
    page: int
    page_size: int


class ContentVersionResponse(BaseModel):
    """Schema for content version response."""
    id: int
    version: int
    content_hash: str
    created_at: datetime
    has_changes: bool

    class Config:
        """Pydantic config."""
        orm_mode = True


class ContentDiffResponse(BaseModel):
    """Schema for content diff comparison."""
    url: str
    old_version: int
    new_version: int
    has_changed: bool
    change_percentage: Optional[float]
    diff_summary: Optional[str]
    diff_data: Optional[Dict[str, Any]]


class ScrapingScheduleBase(BaseModel):
    """Base schema for scraping schedule."""
    name: str = Field(..., min_length=1, max_length=255, description="Schedule name")
    url: str = Field(..., description="URL to scrape")
    cron_expression: str = Field(..., description="Cron expression for scheduling")
    capture_screenshot: bool = Field(True, description="Capture screenshots")
    scraping_config: Optional[Dict[str, Any]] = Field(None, description="Scraping configuration")

    @validator('url')
    def validate_url(cls, v):
        """Validate URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v


class ScrapingScheduleCreate(ScrapingScheduleBase):
    """Schema for creating scraping schedule."""
    company_id: Optional[int] = Field(None, description="Company ID")
    competitor_id: Optional[int] = Field(None, description="Competitor ID")


class ScrapingScheduleUpdate(BaseModel):
    """Schema for updating scraping schedule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = None
    cron_expression: Optional[str] = None
    capture_screenshot: Optional[bool] = None
    scraping_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ScrapingScheduleResponse(ScrapingScheduleBase):
    """Schema for scraping schedule response."""
    id: int
    company_id: Optional[int]
    competitor_id: Optional[int]
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        orm_mode = True


class ScrapingScheduleListResponse(BaseModel):
    """Schema for list of scraping schedules."""
    schedules: List[ScrapingScheduleResponse]
    total: int
    page: int
    page_size: int
