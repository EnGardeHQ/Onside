"""
Real-Time Progress Tracking Service (S5-04)

This module implements WebSocket-based real-time progress tracking for report generation,
following Semantic Seed Venture Studio Coding Standards V2.0.

Features:
1. Real-time progress updates via WebSocket
2. Integration with AI/ML services from Sprint 4
3. Progress estimation with remaining time calculation
4. Detailed stage-by-stage tracking
5. Error handling with graceful fallbacks

All database operations use the actual PostgreSQL database as required:
- Host: localhost
- Port: 5432
- Database: onside
- User: tobymorning
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Set, List
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.progress import ProgressTracker, ProgressStatus, ProgressStage
from src.models.report import Report
from src.database import get_db
from src.utilities.error_reporting import ErrorReporter, ErrorSeverity, with_error_reporting
from src.services.llm_provider import LLMWithChainOfThought

# Configure logger
logger = logging.getLogger(__name__)

class ProgressManager:
    """Manages WebSocket connections and progress updates."""
    
    def __init__(self):
        """Initialize the progress manager."""
        # Active WebSocket connections: {report_id: {user_id: websocket}}
        self.connections: Dict[int, Dict[int, WebSocket]] = {}
        
        # Active progress trackers: {report_id: tracker}
        self.active_trackers: Dict[int, ProgressTracker] = {}
    
    async def connect(self, websocket: WebSocket, report_id: int, user_id: int):
        """Connect a new WebSocket client.
        
        Args:
            websocket: WebSocket connection
            report_id: ID of the report being tracked
            user_id: ID of the user connecting
        """
        await websocket.accept()
        
        # Initialize connection dictionaries if needed
        if report_id not in self.connections:
            self.connections[report_id] = {}
        
        # Store the connection
        self.connections[report_id][user_id] = websocket
        
        logger.info(f"WebSocket connected for report {report_id}, user {user_id}")
    
    def disconnect(self, report_id: int, user_id: int):
        """Disconnect a WebSocket client.
        
        Args:
            report_id: ID of the report being tracked
            user_id: ID of the user disconnecting
        """
        if report_id in self.connections:
            if user_id in self.connections[report_id]:
                del self.connections[report_id][user_id]
            
            if not self.connections[report_id]:
                del self.connections[report_id]
        
        logger.info(f"WebSocket disconnected for report {report_id}, user {user_id}")
    
    async def broadcast_progress(self, report_id: int, progress_data: Dict[str, Any]):
        """Broadcast progress update to all connected clients for a report.
        
        Args:
            report_id: ID of the report
            progress_data: Progress data to broadcast
        """
        if report_id not in self.connections:
            return
        
        # Convert progress data to JSON
        message = json.dumps(progress_data)
        
        # Send to all connected clients for this report
        for websocket in self.connections[report_id].values():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting progress: {str(e)}")
                # Don't raise, just log the error
    
    def register_tracker(self, report_id: int, tracker: ProgressTracker):
        """Register an active progress tracker.
        
        Args:
            report_id: ID of the report
            tracker: Progress tracker instance
        """
        self.active_trackers[report_id] = tracker
    
    def unregister_tracker(self, report_id: int):
        """Unregister a progress tracker.
        
        Args:
            report_id: ID of the report
        """
        if report_id in self.active_trackers:
            del self.active_trackers[report_id]


class ProgressService:
    """Service for managing report generation progress."""
    
    def __init__(self, session: AsyncSession, progress_manager: ProgressManager):
        """Initialize the progress service.
        
        Args:
            session: Database session
            progress_manager: Progress manager instance
        """
        self.session = session
        self.progress_manager = progress_manager
    
    @with_error_reporting(severity=ErrorSeverity.ERROR)
    async def create_tracker(
        self, 
        report_id: int,
        user_id: int
    ) -> ProgressTracker:
        """Create a new progress tracker.
        
        Args:
            report_id: ID of the report
            user_id: ID of the user
            
        Returns:
            Created progress tracker
        """
        # Create new tracker
        tracker = ProgressTracker(
            report_id=report_id,
            user_id=user_id
        )
        
        # Add to database
        self.session.add(tracker)
        await self.session.commit()
        await self.session.refresh(tracker)
        
        # Register with manager
        self.progress_manager.register_tracker(report_id, tracker)
        
        return tracker
    
    @with_error_reporting(severity=ErrorSeverity.ERROR)
    async def update_progress(
        self,
        report_id: int,
        stage: ProgressStage,
        progress: float,
        error: Optional[Dict[str, Any]] = None
    ):
        """Update progress for a report generation stage.
        
        Args:
            report_id: ID of the report
            stage: Current stage
            progress: Progress value between 0 and 1
            error: Optional error information
        """
        # Get tracker
        tracker = await self._get_tracker(report_id)
        if not tracker:
            raise ValueError(f"No tracker found for report {report_id}")
        
        # Update progress
        tracker.update_stage_progress(stage, progress)
        
        # Handle error if present
        if error:
            tracker.status = ProgressStatus.FAILED
            tracker.error_message = error.get("message")
            tracker.error_details = error
        
        # Update estimated completion time
        tracker.estimated_completion_time = tracker.estimate_completion_time()
        
        # Save changes
        await self.session.commit()
        
        # Broadcast update
        await self.progress_manager.broadcast_progress(
            report_id,
            tracker.to_dict()
        )
    
    @with_error_reporting(severity=ErrorSeverity.ERROR)
    async def handle_websocket(
        self,
        websocket: WebSocket,
        report_id: int,
        user_id: int
    ):
        """Handle WebSocket connection for progress tracking.
        
        Args:
            websocket: WebSocket connection
            report_id: ID of the report
            user_id: ID of the user
        """
        try:
            # Connect the WebSocket
            await self.progress_manager.connect(websocket, report_id, user_id)
            
            # Get or create tracker
            tracker = await self._get_tracker(report_id)
            if not tracker:
                tracker = await self.create_tracker(report_id, user_id)
            
            # Send initial state
            await websocket.send_text(json.dumps(tracker.to_dict()))
            
            # Keep connection alive and handle messages
            while True:
                try:
                    # Wait for messages (client might send commands like cancel)
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle commands
                    if message.get("command") == "cancel":
                        await self.cancel_report(report_id)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {str(e)}")
        finally:
            # Clean up connection
            self.progress_manager.disconnect(report_id, user_id)
    
    @with_error_reporting(severity=ErrorSeverity.ERROR)
    async def cancel_report(self, report_id: int):
        """Cancel report generation.
        
        Args:
            report_id: ID of the report to cancel
        """
        tracker = await self._get_tracker(report_id)
        if tracker and tracker.status not in (
            ProgressStatus.COMPLETED,
            ProgressStatus.FAILED,
            ProgressStatus.CANCELLED
        ):
            tracker.status = ProgressStatus.CANCELLED
            await self.session.commit()
            
            # Broadcast cancellation
            await self.progress_manager.broadcast_progress(
                report_id,
                tracker.to_dict()
            )
    
    async def _get_tracker(self, report_id: int) -> Optional[ProgressTracker]:
        """Get progress tracker for a report.
        
        Args:
            report_id: ID of the report
            
        Returns:
            Progress tracker if found, None otherwise
        """
        # Check active trackers first
        if report_id in self.progress_manager.active_trackers:
            return self.progress_manager.active_trackers[report_id]
        
        # Query database
        query = select(ProgressTracker).where(ProgressTracker.report_id == report_id)
        result = await self.session.execute(query)
        tracker = result.scalar_one_or_none()
        
        if tracker:
            # Register in manager
            self.progress_manager.register_tracker(report_id, tracker)
        
        return tracker


# Global progress manager instance
progress_manager = ProgressManager()

async def get_progress_service(
    session: AsyncSession = Depends(get_db)
) -> ProgressService:
    """FastAPI dependency for progress service.
    
    Args:
        session: Database session
        
    Returns:
        Progress service instance
    """
    return ProgressService(session, progress_manager)
