"""Response Models for OnSide API (S5-04)

This module defines Pydantic models for API responses following
Semantic Seed Venture Studio Coding Standards V2.0.

Features:
1. Structured responses for report generation
2. Integration with AI/ML services from Sprint 4:
   - Competitor Analysis Service
   - Market Analysis Service
   - Audience Analysis Service
3. Progress tracking and error handling
4. Confidence scoring and data quality metrics
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field

class ProgressStatus(str, Enum):
    """Status of report generation progress."""
    QUEUED = "QUEUED"
    INITIALIZING = "INITIALIZING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ProgressStage(str, Enum):
    """Stages of report generation."""
    DATA_COLLECTION = "DATA_COLLECTION"
    COMPETITOR_ANALYSIS = "COMPETITOR_ANALYSIS"
    MARKET_ANALYSIS = "MARKET_ANALYSIS"
    AUDIENCE_ANALYSIS = "AUDIENCE_ANALYSIS"
    REPORT_GENERATION = "REPORT_GENERATION"
    VISUALIZATION = "VISUALIZATION"
    FINALIZATION = "FINALIZATION"

class StageProgress(BaseModel):
    """Progress details for a specific stage."""
    stage: ProgressStage
    progress: float = Field(..., ge=0.0, le=1.0)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    confidence_score: Optional[float] = Field(
        None,
        description="Confidence score for stage results",
        ge=0.0,
        le=1.0
    )
    data_quality_score: Optional[float] = Field(
        None,
        description="Data quality score for stage",
        ge=0.0,
        le=1.0
    )
    error: Optional[str] = None

class ProgressResponse(BaseModel):
    """Response model for progress tracking."""
    report_id: int
    status: ProgressStatus
    current_stage: Optional[ProgressStage] = None
    progress_percent: float = Field(..., ge=0.0, le=100.0)
    stage_progress: Dict[ProgressStage, StageProgress]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion_time: Optional[datetime] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict] = None

class AIServiceMetrics(BaseModel):
    """Metrics for AI service execution."""
    execution_time: float
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    data_quality_score: float = Field(..., ge=0.0, le=1.0)
    reasoning_steps: List[str]
    fallback_used: bool = False
    retry_count: int = 0

class CompetitorInsight(BaseModel):
    """Structured insight from competitor analysis."""
    competitor_id: int
    insight_type: str  # trend, opportunity, threat, recommendation
    content: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    data_sources: List[str]
    generated_at: datetime
    service_metrics: AIServiceMetrics

class MarketInsight(BaseModel):
    """Structured insight from market analysis."""
    sector: str
    trend_type: str  # growth, decline, disruption, etc.
    prediction: str
    probability: float = Field(..., ge=0.0, le=1.0)
    impact_score: float = Field(..., ge=0.0, le=1.0)
    timeframe: str  # short_term, medium_term, long_term
    supporting_data: Dict
    service_metrics: AIServiceMetrics

class AudienceInsight(BaseModel):
    """Structured insight from audience analysis."""
    segment_id: str
    persona_name: str
    characteristics: Dict
    engagement_patterns: List[Dict]
    market_fit_score: float = Field(..., ge=0.0, le=1.0)
    growth_potential: float = Field(..., ge=0.0, le=1.0)
    service_metrics: AIServiceMetrics

class ReportGenerationResponse(BaseModel):
    """Complete response for report generation."""
    report_id: int
    status: ProgressStatus
    progress: ProgressResponse
    competitor_insights: Optional[List[CompetitorInsight]] = None
    market_insights: Optional[List[MarketInsight]] = None
    audience_insights: Optional[List[AudienceInsight]] = None
    overall_confidence_score: float = Field(..., ge=0.0, le=1.0)
    execution_summary: Dict[str, AIServiceMetrics]
    generated_at: datetime
    download_url: Optional[str] = None

class WebSocketMessage(BaseModel):
    """Message format for WebSocket communication."""
    type: str = Field(..., description="Message type: progress, error, complete")
    report_id: int
    data: Union[ProgressResponse, Dict]
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseModel):
    """Standardized error response."""
    error: str
    error_type: str
    details: Optional[Dict] = None
    correlation_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
