"""Engagement schemas module."""
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel

class EngagementMetricBase(BaseModel):
    """Base schema for engagement metrics."""
    metric_type: str
    metric_value: int
    metric_metadata: Optional[Dict] = None

class EngagementMetricCreate(EngagementMetricBase):
    """Schema for creating engagement metrics."""
    pass

class EngagementMetricResponse(EngagementMetricBase):
    """Schema for engagement metrics response."""
    id: int
    content_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True
