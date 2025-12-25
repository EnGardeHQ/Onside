"""Pydantic schemas for brand discovery chat."""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExtractedData(BaseModel):
    """Structured data extracted from conversation."""
    brand_name: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    products_services: Optional[str] = None
    target_markets: Optional[List[str]] = None
    target_audience: Optional[str] = None
    competitors: Optional[List[str]] = None
    marketing_goals: Optional[str] = None
    keywords: Optional[List[str]] = None


class ConversationState(BaseModel):
    """Current state of conversation with progress tracking."""
    session_id: uuid.UUID
    extracted_data: ExtractedData
    progress_pct: int = Field(..., ge=0, le=100, description="Completion percentage 0-100")
    missing_fields: List[str] = Field(default_factory=list, description="Required fields not yet collected")
    is_complete: bool = False


class ChatStartResponse(BaseModel):
    """Response when starting a new chat session."""
    session_id: uuid.UUID
    first_message: str


class UserMessageRequest(BaseModel):
    """Request to send a user message."""
    message: str = Field(..., min_length=1, description="User's message")


class ChatMessageResponse(BaseModel):
    """Response after processing user message."""
    ai_response: str
    progress_pct: int = Field(..., ge=0, le=100)
    extracted_data: ExtractedData
    is_complete: bool
    session_id: uuid.UUID


class ChatStatusResponse(BaseModel):
    """Status of current chat session."""
    session_id: uuid.UUID
    progress_pct: int
    extracted_data: ExtractedData
    missing_fields: List[str]
    is_complete: bool
    status: str


class BrandAnalysisQuestionnaire(BaseModel):
    """Complete questionnaire ready for brand analysis."""
    brand_name: str
    website: str
    industry: str
    products_services: str
    target_markets: Optional[List[str]] = None
    target_audience: Optional[str] = None
    competitors: Optional[List[str]] = None
    marketing_goals: Optional[str] = None
    keywords: Optional[List[str]] = None

    @validator('website')
    def validate_website(cls, v):
        """Ensure website has proper format."""
        if not v:
            raise ValueError("Website is required")

        # Add protocol if missing
        if not v.startswith(('http://', 'https://')):
            v = f'https://{v}'

        return v


class FinalizeResponse(BaseModel):
    """Response after finalizing conversation."""
    questionnaire: BrandAnalysisQuestionnaire
    analysis_job_id: Optional[uuid.UUID] = None
    message: str
