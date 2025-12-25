"""Pydantic schemas for Report Schedule API endpoints."""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


class ReportScheduleBase(BaseModel):
    """Base schema for report schedule."""
    name: str = Field(..., min_length=1, max_length=255, description="Schedule name")
    description: Optional[str] = Field(None, description="Schedule description")
    report_type: str = Field(..., description="Type of report to generate")
    cron_expression: str = Field(..., description="Cron expression for scheduling")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Report parameters")
    email_recipients: Optional[List[str]] = Field(None, description="Email recipients for report")
    notify_on_completion: bool = Field(True, description="Send notification on completion")

    @validator('report_type')
    def validate_report_type(cls, v):
        """Validate report type."""
        valid_types = ['content', 'sentiment', 'competitor', 'market', 'audience', 'temporal', 'seo']
        if v.lower() not in valid_types:
            raise ValueError(f"Report type must be one of: {', '.join(valid_types)}")
        return v.lower()


class ReportScheduleCreate(ReportScheduleBase):
    """Schema for creating a report schedule."""
    company_id: int = Field(..., description="Company ID")


class ReportScheduleUpdate(BaseModel):
    """Schema for updating a report schedule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    report_type: Optional[str] = None
    cron_expression: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    email_recipients: Optional[List[str]] = None
    notify_on_completion: Optional[bool] = None


class ReportScheduleResponse(ReportScheduleBase):
    """Schema for report schedule response."""
    id: int
    user_id: int
    company_id: int
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        orm_mode = True


class ReportScheduleListResponse(BaseModel):
    """Schema for list of report schedules."""
    schedules: List[ReportScheduleResponse]
    total: int
    page: int
    page_size: int


class ScheduleExecutionResponse(BaseModel):
    """Schema for schedule execution response."""
    id: int
    schedule_id: int
    report_id: Optional[int]
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    execution_time_seconds: Optional[float]
    created_at: datetime

    class Config:
        """Pydantic config."""
        orm_mode = True


class ScheduleExecutionListResponse(BaseModel):
    """Schema for list of schedule executions."""
    executions: List[ScheduleExecutionResponse]
    total: int
    page: int
    page_size: int


class ScheduleStatsResponse(BaseModel):
    """Schema for schedule statistics."""
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    avg_execution_time: float
