"""Pydantic schemas for Email Delivery API endpoints."""
from datetime import datetime
from typing import Dict, Optional, Any, List
from pydantic import BaseModel, Field, EmailStr


class EmailRecipientBase(BaseModel):
    """Base schema for email recipient."""
    email: EmailStr = Field(..., description="Recipient email address")
    name: Optional[str] = Field(None, max_length=255, description="Recipient name")


class EmailRecipientCreate(EmailRecipientBase):
    """Schema for creating email recipient."""
    company_id: int = Field(..., description="Company ID")


class EmailRecipientUpdate(BaseModel):
    """Schema for updating email recipient."""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class EmailRecipientResponse(EmailRecipientBase):
    """Schema for email recipient response."""
    id: int
    company_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        orm_mode = True


class EmailRecipientListResponse(BaseModel):
    """Schema for list of email recipients."""
    recipients: List[EmailRecipientResponse]
    total: int
    page: int
    page_size: int


class EmailDeliveryBase(BaseModel):
    """Base schema for email delivery."""
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject")
    body_html: Optional[str] = Field(None, description="HTML email body")
    body_text: Optional[str] = Field(None, description="Plain text email body")
    attachment_path: Optional[str] = Field(None, description="Path to attachment")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class EmailDeliveryCreate(EmailDeliveryBase):
    """Schema for creating email delivery."""
    report_id: Optional[int] = Field(None, description="Associated report ID")


class EmailDeliveryResponse(EmailDeliveryBase):
    """Schema for email delivery response."""
    id: int
    report_id: Optional[int]
    status: str
    provider: Optional[str]
    provider_message_id: Optional[str]
    error_message: Optional[str]
    retry_count: int
    sent_at: Optional[datetime]
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    bounced_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        orm_mode = True


class EmailDeliveryListResponse(BaseModel):
    """Schema for list of email deliveries."""
    deliveries: List[EmailDeliveryResponse]
    total: int
    page: int
    page_size: int


class EmailDeliveryMetricsResponse(BaseModel):
    """Schema for email delivery metrics."""
    status: str
    retry_count: int
    sent: bool
    opened: bool
    clicked: bool
    bounced: bool
    delivery_time_seconds: Optional[float]
    time_to_open_seconds: Optional[float]
    time_to_click_seconds: Optional[float]


class RetryDeliveryResponse(BaseModel):
    """Schema for retry delivery response."""
    message: str
    delivery_id: int
    new_retry_count: int
    status: str
