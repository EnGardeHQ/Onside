from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta, timezone
from src.database.config import get_db
from src.auth.security import get_current_user
from src.models.user import User
from src.models.content import Content
from src.models.engagement import EngagementMetrics
from src.models.report import Report, ReportStatus, ReportType
from src.services.analytics import AnalyticsService
from src.services.competitive_analysis import CompetitiveAnalysisService
from src.services.report_generator import ReportGeneratorService
from src.schemas.report import ReportCreate, ReportResponse, ReportListResponse
from pydantic import BaseModel, constr, Field
from collections import defaultdict

router = APIRouter(tags=["reports"])

class TimeframeEnum(str):
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"
    YEAR = "1y"

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body, BackgroundTasks, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta, timezone

from src.database.config import get_db
from src.auth.security import get_current_user
from src.models.user import User
from src.models.content import Content
from src.models.engagement import EngagementMetrics
from src.models.report import Report, ReportStatus, ReportType
from src.services.analytics import AnalyticsService
from src.services.competitive_analysis import CompetitiveAnalysisService
from src.services.report_generator import ReportGeneratorService
from src.services.progress import ProgressService, get_progress_service
from src.schemas.report import ReportCreate, ReportResponse, ReportListResponse
from src.schemas.requests import (
    CompetitorReportRequest,
    MarketReportRequest,
    AudienceReportRequest,
    TemporalReportRequest,
    SEOReportRequest,
    ContentReportRequest,
    SentimentReportRequest
)
from src.schemas.responses import (
    ProgressResponse,
    WebSocketMessage,
    ErrorResponse
)

router = APIRouter(tags=["reports"])

@router.get("/kpi", response_model=Dict[str, Any])
async def generate_kpi_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    platforms: str = Query(default=""),
    metrics: str = Query(default="engagement,reach,conversion"),
    with_chain_of_thought: bool = Query(default=True, description="Include AI reasoning steps"),
    confidence_threshold: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Parse platforms and metrics
        platform_list = [p.strip() for p in platforms.split(",")] if platforms else []
        metric_list = [m.strip() for m in metrics.split(",")] if metrics else []

        # Parse dates if provided
        if start_date:
            parsed_start_date = datetime.fromisoformat(start_date)
            if not parsed_start_date.tzinfo:
                parsed_start_date = parsed_start_date.replace(tzinfo=timezone.utc)
        else:
            parsed_start_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        if end_date:
            parsed_end_date = datetime.fromisoformat(end_date)
            if not parsed_end_date.tzinfo:
                parsed_end_date = parsed_end_date.replace(tzinfo=timezone.utc)
        else:
            parsed_end_date = datetime.now(timezone.utc)

        # Validate date range
        if parsed_end_date < parsed_start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )

        # Generate KPI report
        report = {
            "metrics": {
                "engagement": {"total": 0, "average": 0.0, "trend": []},
                "reach": {"total": 0, "average": 0.0, "trend": []},
                "conversion": {"total": 0, "average": 0.0, "trend": []},
                "share_of_voice": {"total": 0, "average": 0.0, "trend": []}
            },
            "date_range": {
                "start": parsed_start_date.isoformat(),
                "end": parsed_end_date.isoformat()
            },
            "content_count": 0,
            "platforms": platform_list
        }

        # Query content items
        content_query = db.query(Content)
        if content_type:
            content_query = content_query.filter(Content.content_type == content_type)
        if platform_list:
            # Filter content based on platform in metadata
            content_items = [
                content for content in content_query.all()
                if content.content_metadata and
                content.content_metadata.get('platform') in platform_list
            ]
        else:
            content_items = content_query.all()
        
        report["content_count"] = len(content_items)

        # Query engagement metrics
        metrics_query = db.query(EngagementMetrics)
        if content_items:
            metrics_query = metrics_query.filter(
                EngagementMetrics.content_id.in_([c.id for c in content_items])
            )
        engagement_metrics = metrics_query.all()

        # Group metrics by type
        metrics_by_type = defaultdict(list)
        for metric in engagement_metrics:
            metrics_by_type[metric.metric_type].append(metric)

        # Calculate totals and averages
        for metric_type in metric_list:
            if metric_type in metrics_by_type:
                values = [m.metric_value for m in metrics_by_type[metric_type]]
                report["metrics"][metric_type]["total"] = sum(values)
                report["metrics"][metric_type]["average"] = sum(values) / len(values) if values else 0

                # Calculate trend (last 7 days)
                trend_data = []
                current_date = parsed_start_date
                while current_date <= parsed_end_date:
                    next_date = current_date + timedelta(days=1)
                    day_metrics = [
                        m for m in metrics_by_type[metric_type]
                        if m.created_at and (
                            current_date <= m.created_at.replace(tzinfo=timezone.utc) < next_date
                        )
                    ]
                    trend_data.append({
                        "date": current_date.isoformat(),
                        "value": sum(m.metric_value for m in day_metrics)
                    })
                    current_date = next_date
                report["metrics"][metric_type]["trend"] = trend_data

        return report

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating KPI report: {str(e)}"
        )

@router.post("/competitor", response_model=ReportResponse)
async def create_competitor_report(
    request: CompetitorReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    progress_service: ProgressService = Depends(get_progress_service)
) -> Report:
    """Create a new competitor intelligence report with AI-powered analysis.
    
    This endpoint is part of Sprint 4's AI/ML enhancements, providing:
    - Chain-of-thought reasoning
    - Data quality and confidence scoring
    - Real-time progress tracking
    - Integration with AI services:
      * Competitor Analysis Service
      * Market Analysis Service
      * Audience Analysis Service
    """
    # Create report
    report = Report(
        user_id=current_user.id,
        type=ReportType.COMPETITOR,
        status=ReportStatus.PENDING,
        parameters={
            "competitor_ids": request.competitor_ids,
            "metrics": request.metrics,
            "timeframe": request.timeframe or "30d",
            "with_chain_of_thought": request.with_chain_of_thought,
            "confidence_threshold": request.confidence_threshold,
            "include_historical": request.include_historical
        }
    )
    
    if not report.validate_parameters():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report parameters"
        )
    
    # Create progress tracker
    tracker = await progress_service.create_tracker(
        report_id=report.id,
        user_id=current_user.id
    )
    
    # Save report to database
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # Start async report generation with progress tracking
    background_tasks.add_task(
        report_generator.generate_competitor_report,
        report_id=report.id,
        tracker_id=tracker.id,
        db=db,
        progress_service=progress_service
    )
    
    return report

@router.websocket("/ws/{report_id}")
async def report_progress(websocket: WebSocket, report_id: int):
    """WebSocket endpoint for real-time progress updates.
    
    Features:
    - Real-time progress tracking
    - Stage-by-stage updates
    - Error notifications
    - Integration with AI services
    """
    try:
        await websocket.accept()
        
        # Get progress service
        progress_service = get_progress_service()
        
        # Subscribe to progress updates
        await progress_service.websocket_manager.connect(
            websocket=websocket,
            report_id=report_id
        )
        
        while True:
            try:
                # Keep connection alive and handle client messages
                data = await websocket.receive_json()
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    finally:
        # Clean up connection
        await progress_service.websocket_manager.disconnect(websocket)

@router.post("/market", response_model=ReportResponse)
async def create_market_report(
    request: MarketReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    progress_service: ProgressService = Depends(get_progress_service)
) -> Report:
    """Create a new market analysis report with predictive insights.
    
    Features:
    - Predictive analytics with ML model integration
    - Enhanced LLM insights for market predictions
    - Sector-specific trend analysis
    - Real-time progress tracking
    """
    # Create report with market analysis parameters
    report = Report(
        user_id=current_user.id,
        type=ReportType.MARKET,
        status=ReportStatus.PENDING,
        parameters={
            "company_id": request.company_id,
            "sectors": request.sectors,
            "timeframe": request.timeframe or "30d",
            "with_chain_of_thought": request.with_chain_of_thought,
            "confidence_threshold": request.confidence_threshold,
            "include_predictions": request.include_predictions
        }
    )
    
    if not report.validate_parameters():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report parameters"
        )
    
    # Create progress tracker
    tracker = await progress_service.create_tracker(
        report_id=report.id,
        user_id=current_user.id
    )
    
    # Save report to database
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # Start async report generation with progress tracking
    background_tasks.add_task(
        report_generator.generate_market_report,
        report_id=report.id,
        tracker_id=tracker.id,
        db=db,
        progress_service=progress_service
    )
    
    return report

@router.post("/audience", response_model=ReportResponse)
async def create_audience_report(
    request: AudienceReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    progress_service: ProgressService = Depends(get_progress_service)
) -> Report:
    """Create a new audience analysis report with AI-driven persona insights.
    
    Features:
    - AI-driven persona generation
    - Engagement pattern analysis
    - Demographic insights with confidence scoring
    - Real-time progress tracking
    """
    # Create report with audience analysis parameters
    report = Report(
        user_id=current_user.id,
        type=ReportType.AUDIENCE,
        status=ReportStatus.PENDING,
        parameters={
            "company_id": request.company_id,
            "segment_id": request.segment_id,
            "demographic_filters": request.demographic_filters,
            "timeframe": request.timeframe or "30d",
            "with_chain_of_thought": request.with_chain_of_thought,
            "confidence_threshold": request.confidence_threshold
        }
    )
    
    if not report.validate_parameters():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report parameters"
        )
    
    # Create progress tracker
    tracker = await progress_service.create_tracker(
        report_id=report.id,
        user_id=current_user.id
    )
    
    # Save report to database
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # Start async report generation with progress tracking
    background_tasks.add_task(
        report_generator.generate_audience_report,
        report_id=report.id,
        tracker_id=tracker.id,
        db=db,
        progress_service=progress_service
    )
    
    return report

@router.get("/progress/{report_id}", response_model=ProgressResponse)
async def get_report_progress(
    report_id: int = Path(..., description="ID of the report to get progress for"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    progress_service: ProgressService = Depends(get_progress_service)
) -> ProgressResponse:
    """Get the current progress of a report generation task.
    
    Features:
    - Real-time progress status
    - Stage-by-stage progress tracking
    - Error reporting
    - AI service metrics
    """
    # Get report to verify ownership
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this report's progress"
        )
    
    # Get progress from tracker
    progress = await progress_service.get_progress(report_id)
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress tracker not found"
        )
    
    return progress

@router.post("/cancel/{report_id}", response_model=Dict[str, Any])
async def cancel_report_generation(
    report_id: int = Path(..., description="ID of the report to cancel"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    progress_service: ProgressService = Depends(get_progress_service)
) -> Dict[str, Any]:
    """Cancel an ongoing report generation task.
    
    Features:
    - Safe cancellation of AI/ML tasks
    - Progress cleanup
    - Resource release
    """
    # Get report to verify ownership
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this report"
        )
    
    # Cancel report generation
    cancelled = await progress_service.cancel_report(
        report_id=report_id,
        user_id=current_user.id
    )
    
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to cancel report generation"
        )
    
    return {"status": "cancelled", "report_id": report_id}

@router.post("/market", response_model=ReportResponse)
async def create_market_report(
    request: MarketReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    progress_service: ProgressService = Depends(get_progress_service)
) -> Report:
    """Create a new market analysis report with predictive insights.
    
    Features:
    - Predictive analytics with ML model integration
    - Enhanced LLM insights for market predictions
    - Sector-specific trend analysis
    - Real-time progress tracking
    """
    # Create report with market analysis parameters
    report = Report(
        user_id=current_user.id,
        type=ReportType.MARKET,
        status=ReportStatus.PENDING,
        parameters={
            "company_id": request.company_id,
            "sectors": request.sectors,
            "timeframe": request.timeframe or "30d",
            "with_chain_of_thought": request.with_chain_of_thought,
            "confidence_threshold": request.confidence_threshold,
            "include_predictions": request.include_predictions
        }
    )
    
    if not report.validate_parameters():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report parameters"
        )
    
    # Create progress tracker
    tracker = await progress_service.create_tracker(
        report_id=report.id,
        user_id=current_user.id
    )
    
    # Save report to database
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # Start async report generation with progress tracking
    background_tasks.add_task(
        report_generator.generate_market_report,
        report_id=report.id,
        tracker_id=tracker.id,
        db=db,
        progress_service=progress_service
    )
    
@router.post("/sentiment", response_model=ReportResponse)
async def create_sentiment_report(
    request: SentimentReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    progress_service: ProgressService = Depends(get_progress_service)
) -> Report:
    """Create a new sentiment analysis report with AI reasoning.
    
    Features:
    - Advanced sentiment analysis
    - Context-aware analysis
    - Aspect-based insights
    - Real-time progress tracking
    """
    # Create report with sentiment analysis parameters
    report = Report(
        user_id=current_user.id,
        type=ReportType.SENTIMENT,
        status=ReportStatus.PENDING,
        parameters={
            "content_ids": request.content_ids,
            "context_window": request.context_window,
            "sentiment_aspects": request.sentiment_aspects,
            "timeframe": request.timeframe or "30d",
            "with_chain_of_thought": request.with_chain_of_thought,
            "confidence_threshold": request.confidence_threshold
        }
    )
    
    if not report.validate_parameters():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report parameters"
        )
    
    # Create progress tracker
    tracker = await progress_service.create_tracker(
        report_id=report.id,
        user_id=current_user.id
    )
    
    # Save report to database
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # Start async report generation with progress tracking
    background_tasks.add_task(
        report_generator.generate_sentiment_report,
        report_id=report.id,
        tracker_id=tracker.id,
        db=db,
        progress_service=progress_service
    )
    
    return report

@router.post("/temporal", response_model=ReportResponse)
async def create_temporal_report(
    request: TemporalReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    progress_service: ProgressService = Depends(get_progress_service)
) -> Report:
    """Create a new temporal analysis report with trend detection.
    
    Features:
    - Time series analysis
    - Trend detection with ML models
    - Pattern recognition
    - Real-time progress tracking
    """
    # Create report with temporal analysis parameters
    report = Report(
        user_id=current_user.id,
        type=ReportType.TEMPORAL,
        status=ReportStatus.PENDING,
        parameters={
            "content_id": request.content_id,
            "interval": request.interval,
            "timeframe": request.timeframe or "30d",
            "with_chain_of_thought": request.with_chain_of_thought,
            "confidence_threshold": request.confidence_threshold,
            "trend_detection": request.trend_detection
        }
    )
    
    if not report.validate_parameters():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report parameters"
        )
    
    # Create progress tracker
    tracker = await progress_service.create_tracker(
        report_id=report.id,
        user_id=current_user.id
    )
    
    # Save report to database
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # Start async report generation with progress tracking
    background_tasks.add_task(
        report_generator.generate_temporal_report,
        report_id=report.id,
        tracker_id=tracker.id,
        db=db,
        progress_service=progress_service
    )
    
    return report

@router.post("/seo", response_model=ReportResponse)
async def create_seo_report(
    request: SEOReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    progress_service: ProgressService = Depends(get_progress_service)
) -> Report:
    """Create a new SEO analysis report with competitor benchmarking.
    
    Features:
    - Enhanced SEO analysis
    - Competitor benchmarking
    - Subject-based insights
    - Real-time progress tracking
    """
    # Create report with SEO analysis parameters
    report = Report(
        user_id=current_user.id,
        type=ReportType.SEO,
        status=ReportStatus.PENDING,
        parameters={
            "content_id": request.content_id,
            "enhanced": request.enhanced,
            "competitors_count": request.competitors_count,
            "subject_ids": request.subject_ids,
            "timeframe": request.timeframe or "30d",
            "with_chain_of_thought": request.with_chain_of_thought,
            "confidence_threshold": request.confidence_threshold
        }
    )
    
    if not report.validate_parameters():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report parameters"
        )
    
    # Create progress tracker
    tracker = await progress_service.create_tracker(
        report_id=report.id,
        user_id=current_user.id
    )
    
    # Save report to database
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # Start async report generation with progress tracking
    background_tasks.add_task(
        report_generator.generate_seo_report,
        report_id=report.id,
        tracker_id=tracker.id,
        db=db,
        progress_service=progress_service
    )
    
    return report
    
    return report

@router.post("/audience", response_model=ReportResponse)
async def create_audience_report(
    request: AudienceReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Report:
    """Create a new audience analysis report with AI-driven persona insights."""
    report = Report(
        user_id=current_user.id,
        type=ReportType.AUDIENCE,
        status=ReportStatus.PENDING,
        parameters={
            "company_id": request.company_id,
            "segment_id": request.segment_id,
            "timeframe": request.timeframe or "30d",
            "with_chain_of_thought": request.with_chain_of_thought,
            "confidence_threshold": request.confidence_threshold,
            "demographic_filters": request.demographic_filters
        }
    )
    
    if not report.validate_parameters():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report parameters"
        )
    
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    background_tasks.add_task(
        report_generator.generate_audience_report,
        report_id=report.id,
        db=db
    )
    
    return report

@router.post("/temporal", response_model=ReportResponse)
async def create_temporal_report(
    request: TemporalReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Report:
    """Create a new temporal analysis report with trend detection."""
    report = Report(
        user_id=current_user.id,
        type=ReportType.TEMPORAL,
        status=ReportStatus.PENDING,
        parameters={
            "content_id": request.content_id,
            "interval": request.interval,
            "timeframe": request.timeframe or "30d",
            "with_chain_of_thought": request.with_chain_of_thought,
            "confidence_threshold": request.confidence_threshold,
            "trend_detection": request.trend_detection
        }
    )
    
    if not report.validate_parameters():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report parameters"
        )
    
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    background_tasks.add_task(
        report_generator.generate_temporal_report,
        report_id=report.id,
        db=db
    )
    
    return report

@router.post("/seo", response_model=ReportResponse)
async def create_seo_report(
    request: SEOReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Report:
    """Create a new SEO analysis report with competitor benchmarking."""
    report = Report(
        user_id=current_user.id,
        type=ReportType.SEO,
        status=ReportStatus.PENDING,
        parameters={
            "content_id": request.content_id,
            "enhanced": request.enhanced,
            "timeframe": request.timeframe or "30d",
            "with_chain_of_thought": request.with_chain_of_thought,
            "confidence_threshold": request.confidence_threshold,
            "competitors_count": request.competitors_count
        }
    )
    
    if not report.validate_parameters():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report parameters"
        )
    
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    background_tasks.add_task(
        report_generator.generate_seo_report,
        report_id=report.id,
        db=db
    )
    
    return report
    # Convert timeframe to start_date
    timeframe_days = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "1y": 365
    }.get(timeframe, 30)
    
    start_date = datetime.now(timezone.utc) - timedelta(days=timeframe_days)
    end_date = datetime.now(timezone.utc)
    
    # Initialize competitive analysis service
    competitive_service = CompetitiveAnalysisService(db)
    
    try:
        report_data = competitive_service.generate_report(
            user_id=current_user.id,
            competitor_ids=competitor_ids,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            content_types=content_types,
            platforms=platforms
        )
        return report_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# New API Endpoints for Sprint 4: Report Generation with Job Status Tracking

class BaseReportRequest(BaseModel):
    """Base request model for all report types."""
    timeframe: Optional[str] = Field(None, description="Time range for analysis (7d, 30d, 90d, 1y)")
    with_chain_of_thought: bool = Field(default=True, description="Include AI reasoning steps")
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum confidence score")

class ContentReportRequest(BaseReportRequest):
    """Request model for content report generation with AI analysis."""
    content_types: List[str] = Field(default_factory=list)
    platforms: List[str] = Field(default_factory=list)
    analysis_depth: int = Field(default=1, ge=1, le=3, description="Depth of content analysis")
    extract_entities: bool = Field(default=True, description="Extract named entities")


class SentimentReportRequest(BaseReportRequest):
    """Request model for sentiment report generation with AI reasoning."""
    content_ids: List[int] = Field(..., description="Content IDs to analyze")
    context_window: int = Field(default=3, ge=1, le=10, description="Context window size")
    sentiment_aspects: List[str] = Field(default_factory=list, description="Specific aspects to analyze")

class CompetitorReportRequest(BaseReportRequest):
    """Request model for competitor intelligence reports."""
    competitor_ids: List[int] = Field(..., description="Competitor IDs to analyze")
    metrics: List[str] = Field(default=["engagement", "reach", "share_of_voice"])
    include_historical: bool = Field(default=True, description="Include historical trends")

class MarketReportRequest(BaseReportRequest):
    """Request model for market analysis reports."""
    company_id: int = Field(..., description="Company ID for market analysis")
    sectors: List[str] = Field(default_factory=list, description="Market sectors to analyze")
    include_predictions: bool = Field(default=True, description="Include market predictions")

class AudienceReportRequest(BaseReportRequest):
    """Request model for audience analysis reports."""
    company_id: int = Field(..., description="Company ID for audience analysis")
    segment_id: Optional[int] = Field(None, description="Specific audience segment to analyze")
    demographic_filters: Dict[str, Any] = Field(default_factory=dict)

class TemporalReportRequest(BaseReportRequest):
    """Request model for temporal analysis reports."""
    content_id: int = Field(..., description="Content ID for temporal analysis")
    interval: str = Field(default="1d", description="Time interval for analysis")
    trend_detection: bool = Field(default=True, description="Enable trend detection")

class SEOReportRequest(BaseReportRequest):
    """Request model for SEO analysis reports."""
    content_id: int = Field(..., description="Content ID for SEO analysis")
    enhanced: bool = Field(default=True, description="Enable enhanced SEO analysis")
    competitors_count: int = Field(default=5, ge=1, le=10, description="Number of competitors to analyze")
    subject_ids: Optional[List[int]] = None


@router.post("/content", response_model=ReportResponse)
async def create_content_report(
    request: ContentReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    progress_service: ProgressService = Depends(get_progress_service)
) -> Report:
    """Create a new content report with AI-powered analysis.
    
    Features:
    - Content analysis with AI/ML models
    - Entity extraction
    - Platform-specific insights
    - Real-time progress tracking
    """
    # Create report with content analysis parameters
    report = Report(
        user_id=current_user.id,
        type=ReportType.CONTENT,
        status=ReportStatus.PENDING,
        parameters={
            "content_types": request.content_types,
            "platforms": request.platforms,
            "analysis_depth": request.analysis_depth,
            "extract_entities": request.extract_entities,
            "timeframe": request.timeframe or "30d",
            "with_chain_of_thought": request.with_chain_of_thought,
            "confidence_threshold": request.confidence_threshold
        }
    )
    
    if not report.validate_parameters():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report parameters"
        )
    
    # Create progress tracker
    tracker = await progress_service.create_tracker(
        report_id=report.id,
        user_id=current_user.id
    )
    
    # Save report to database
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # Start async report generation with progress tracking
    background_tasks.add_task(
        report_generator.generate_content_report,
        report_id=report.id,
        tracker_id=tracker.id,
        db=db,
        progress_service=progress_service
    )
    
    return report


@router.post("/sentiment", response_model=ReportResponse)
async def create_sentiment_report(
    request: SentimentReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    progress_service: ProgressService = Depends(get_progress_service)
) -> Report:
    """Create a new sentiment analysis report with AI reasoning.
    
    Features:
    - Advanced sentiment analysis
    - Context-aware analysis
    - Aspect-based insights
    - Real-time progress tracking
    """
    # Validate that at least one filter is provided
    if not request.content_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content IDs must be provided for sentiment analysis"
        )
    
    # Create report with sentiment analysis parameters
    report = Report(
        user_id=current_user.id,
        type=ReportType.SENTIMENT,
        status=ReportStatus.PENDING,
        parameters={
            "content_ids": request.content_ids,
            "context_window": request.context_window,
            "sentiment_aspects": request.sentiment_aspects,
            "timeframe": request.timeframe or "30d",
            "with_chain_of_thought": request.with_chain_of_thought,
            "confidence_threshold": request.confidence_threshold
        }
    )
    
    if not report.validate_parameters():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report parameters"
        )
    
    # Create progress tracker
    tracker = await progress_service.create_tracker(
        report_id=report.id,
        user_id=current_user.id
    )
    
    # Save report to database
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # Start async report generation with progress tracking
    background_tasks.add_task(
        report_generator.generate_sentiment_report,
        report_id=report.id,
        tracker_id=tracker.id,
        db=db,
        progress_service=progress_service
    )
    
    return report


@router.get("/{report_id}", response_model=ReportResponse, summary="Get Report", description="Get a report by ID with detailed status information")
async def get_report(
    report_id: int = Path(..., description="ID of the report to retrieve"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a report by ID."""
    try:
        # Initialize report generator service
        report_service = ReportGeneratorService(db)
        
        # Get report
        report = await report_service.get_report(report_id)
        
        # Check if report exists
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Check if user has access to this report
        if report.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this report"
            )
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving report: {str(e)}"
        )


@router.get("", response_model=ReportListResponse, summary="List Reports", description="List reports with filtering options for type and status")
async def list_reports(
    type: Optional[str] = Query(None, description="Filter by report type"),
    status: Optional[str] = Query(None, description="Filter by report status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List reports for the current user."""
    try:
        # Initialize report generator service
        report_service = ReportGeneratorService(db)
        
        # Convert string values to enum types if provided
        report_type = ReportType[type.upper()] if type else None
        report_status = ReportStatus[status.upper()] if status else None
        
        # Get reports
        reports, total = await report_service.get_user_reports(
            user_id=current_user.id,
            report_type=report_type,
            status=report_status,
            page=page,
            page_size=page_size
        )
        
        return {
            "reports": reports,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameter: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing reports: {str(e)}"
        )
