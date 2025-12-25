"""Report schema module for report API validation and serialization."""
from enum import Enum
from typing import Dict, Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ReportStatusEnum(str, Enum):
    """Report status enumeration for API schemas."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportTypeEnum(str, Enum):
    """Report type enumeration for API schemas."""
    CONTENT = "content"
    SENTIMENT = "sentiment"


class ReportBase(BaseModel):
    """Base schema for report objects."""
    type: ReportTypeEnum
    parameters: Dict[str, Any]


class ReportCreate(ReportBase):
    """Schema for creating a new report."""
    pass


class ReportResponse(ReportBase):
    """Schema for report response."""
    id: int
    user_id: str
    status: ReportStatusEnum
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic model configuration."""
        orm_mode = True


class ReportListResponse(BaseModel):
    """Schema for list of reports response."""
    reports: List[ReportResponse]
    total: int
    page: int
    page_size: int
