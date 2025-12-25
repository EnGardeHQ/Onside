"""
Progress Tracking API Routes (S5-04)

This module implements FastAPI routes for real-time progress tracking,
integrating with our AI/ML services from Sprint 4 and following
Semantic Seed Venture Studio Coding Standards V2.0.

Features:
1. WebSocket endpoint for real-time updates
2. REST endpoints for progress management
3. Integration with competitor, market, and audience analysis services
4. Proper error handling and logging
"""
from fastapi import APIRouter, WebSocket, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
import logging

from src.database import get_db
from src.models.progress import ProgressTracker, ProgressStatus, ProgressStage
from src.services.progress.progress_service import (
    ProgressService,
    get_progress_service
)
from src.services.competitor_analysis import CompetitorAnalysisService
from src.services.market_analysis import MarketAnalysisService
from src.services.audience_analysis import AudienceAnalysisService
from src.utilities.error_reporting import ErrorReporter, ErrorSeverity, with_error_reporting

# Configure router
router = APIRouter(prefix="/api/v1/progress", tags=["progress"])

# Configure logger
logger = logging.getLogger(__name__)

@router.websocket("/ws/{report_id}")
async def progress_websocket(
    websocket: WebSocket,
    report_id: int,
    user_id: int,
    progress_service: ProgressService = Depends(get_progress_service)
):
    """WebSocket endpoint for real-time progress updates.
    
    Args:
        websocket: WebSocket connection
        report_id: ID of the report to track
        user_id: ID of the user connecting
        progress_service: Progress tracking service
    """
    await progress_service.handle_websocket(websocket, report_id, user_id)

@router.post("/reports/{report_id}/start")
@with_error_reporting(severity=ErrorSeverity.ERROR)
async def start_report_generation(
    report_id: int,
    user_id: int,
    progress_service: ProgressService = Depends(get_progress_service),
    competitor_service: CompetitorAnalysisService = Depends(),
    market_service: MarketAnalysisService = Depends(),
    audience_service: AudienceAnalysisService = Depends(),
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Start report generation with progress tracking.
    
    Args:
        report_id: ID of the report
        user_id: ID of the user
        progress_service: Progress tracking service
        competitor_service: Competitor analysis service
        market_service: Market analysis service
        audience_service: Audience analysis service
        session: Database session
        
    Returns:
        Progress tracker information
    """
    try:
        # Create progress tracker
        tracker = await progress_service.create_tracker(report_id, user_id)
        
        # Start async report generation
        asyncio.create_task(
            generate_report_with_progress(
                report_id=report_id,
                progress_service=progress_service,
                competitor_service=competitor_service,
                market_service=market_service,
                audience_service=audience_service,
                session=session
            )
        )
        
        return tracker.to_dict()
    except Exception as e:
        ErrorReporter.report(
            message=f"Failed to start report generation: {str(e)}",
            severity=ErrorSeverity.ERROR,
            exception=e,
            context={"report_id": report_id, "user_id": user_id}
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to start report generation"
        )

@router.post("/reports/{report_id}/cancel")
@with_error_reporting(severity=ErrorSeverity.ERROR)
async def cancel_report_generation(
    report_id: int,
    progress_service: ProgressService = Depends(get_progress_service)
) -> Dict[str, Any]:
    """Cancel report generation.
    
    Args:
        report_id: ID of the report
        progress_service: Progress tracking service
        
    Returns:
        Updated progress tracker information
    """
    try:
        await progress_service.cancel_report(report_id)
        
        # Get updated tracker
        tracker = await progress_service._get_tracker(report_id)
        if not tracker:
            raise HTTPException(
                status_code=404,
                detail=f"No tracker found for report {report_id}"
            )
        
        return tracker.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        ErrorReporter.report(
            message=f"Failed to cancel report generation: {str(e)}",
            severity=ErrorSeverity.ERROR,
            exception=e,
            context={"report_id": report_id}
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to cancel report generation"
        )

@router.get("/reports/{report_id}")
@with_error_reporting(severity=ErrorSeverity.ERROR)
async def get_report_progress(
    report_id: int,
    progress_service: ProgressService = Depends(get_progress_service)
) -> Dict[str, Any]:
    """Get current progress for a report.
    
    Args:
        report_id: ID of the report
        progress_service: Progress tracking service
        
    Returns:
        Progress tracker information
    """
    try:
        tracker = await progress_service._get_tracker(report_id)
        if not tracker:
            raise HTTPException(
                status_code=404,
                detail=f"No tracker found for report {report_id}"
            )
        
        return tracker.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        ErrorReporter.report(
            message=f"Failed to get report progress: {str(e)}",
            severity=ErrorSeverity.ERROR,
            exception=e,
            context={"report_id": report_id}
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to get report progress"
        )

async def generate_report_with_progress(
    report_id: int,
    progress_service: ProgressService,
    competitor_service: CompetitorAnalysisService,
    market_service: MarketAnalysisService,
    audience_service: AudienceAnalysisService,
    session: AsyncSession
):
    """Generate report with progress tracking.
    
    This function runs asynchronously and updates progress in real-time.
    
    Args:
        report_id: ID of the report
        progress_service: Progress tracking service
        competitor_service: Competitor analysis service
        market_service: Market analysis service
        audience_service: Audience analysis service
        session: Database session
    """
    try:
        # Stage 1: Data Collection
        await progress_service.update_progress(
            report_id,
            ProgressStage.DATA_COLLECTION,
            0.0
        )
        
        # Collect data using chain-of-thought reasoning
        data = await competitor_service.collect_data_with_reasoning(report_id)
        
        await progress_service.update_progress(
            report_id,
            ProgressStage.DATA_COLLECTION,
            1.0
        )
        
        # Stage 2: Competitor Analysis
        await progress_service.update_progress(
            report_id,
            ProgressStage.COMPETITOR_ANALYSIS,
            0.0
        )
        
        competitor_insights = await competitor_service.analyze_with_confidence(
            data,
            report_id
        )
        
        await progress_service.update_progress(
            report_id,
            ProgressStage.COMPETITOR_ANALYSIS,
            1.0
        )
        
        # Stage 3: Market Analysis
        await progress_service.update_progress(
            report_id,
            ProgressStage.MARKET_ANALYSIS,
            0.0
        )
        
        market_insights = await market_service.analyze_with_predictions(
            data,
            report_id
        )
        
        await progress_service.update_progress(
            report_id,
            ProgressStage.MARKET_ANALYSIS,
            1.0
        )
        
        # Stage 4: Audience Analysis
        await progress_service.update_progress(
            report_id,
            ProgressStage.AUDIENCE_ANALYSIS,
            0.0
        )
        
        audience_insights = await audience_service.generate_personas(
            data,
            report_id
        )
        
        await progress_service.update_progress(
            report_id,
            ProgressStage.AUDIENCE_ANALYSIS,
            1.0
        )
        
        # Stage 5: Report Generation
        await progress_service.update_progress(
            report_id,
            ProgressStage.REPORT_GENERATION,
            0.0
        )
        
        report = await competitor_service.generate_report(
            competitor_insights=competitor_insights,
            market_insights=market_insights,
            audience_insights=audience_insights,
            report_id=report_id
        )
        
        await progress_service.update_progress(
            report_id,
            ProgressStage.REPORT_GENERATION,
            1.0
        )
        
        # Stage 6: Visualization
        await progress_service.update_progress(
            report_id,
            ProgressStage.VISUALIZATION,
            0.0
        )
        
        visualizations = await competitor_service.generate_visualizations(
            report,
            report_id
        )
        
        await progress_service.update_progress(
            report_id,
            ProgressStage.VISUALIZATION,
            1.0
        )
        
        # Stage 7: Finalization
        await progress_service.update_progress(
            report_id,
            ProgressStage.FINALIZATION,
            0.0
        )
        
        await competitor_service.finalize_report(
            report,
            visualizations,
            report_id
        )
        
        await progress_service.update_progress(
            report_id,
            ProgressStage.FINALIZATION,
            1.0
        )
        
    except Exception as e:
        # Report error and update progress
        error_details = {
            "message": str(e),
            "type": type(e).__name__
        }
        
        await progress_service.update_progress(
            report_id,
            stage=progress_service._get_tracker(report_id).current_stage,
            progress=progress_service._get_tracker(report_id).progress_percent,
            error=error_details
        )
        
        ErrorReporter.report(
            message=f"Report generation failed: {str(e)}",
            severity=ErrorSeverity.ERROR,
            exception=e,
            context={"report_id": report_id}
        )
