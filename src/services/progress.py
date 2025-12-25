"""
Progress Service (S5-04)

This module provides services for tracking progress of report generation operations,
following Semantic Seed Venture Studio Coding Standards V2.0.

The services connect to the actual PostgreSQL database as required:
- Host: localhost
- Port: 5432
- Database: onside
- User: tobymorning
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from src.database import get_db
from src.models.progress import ProgressTracker, ProgressStatus, ProgressStage


class ProgressService:
    """Service for managing progress tracking operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db
    
    async def get_tracker(self, tracker_id: int) -> Optional[ProgressTracker]:
        """Get a progress tracker by ID."""
        query = select(ProgressTracker).where(ProgressTracker.id == tracker_id)
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_trackers_by_report(self, report_id: int) -> List[ProgressTracker]:
        """Get all progress trackers for a report."""
        query = select(ProgressTracker).where(ProgressTracker.report_id == report_id)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_trackers_by_user(self, user_id: int) -> List[ProgressTracker]:
        """Get all progress trackers for a user."""
        query = select(ProgressTracker).where(ProgressTracker.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create_tracker(self, report_id: int, user_id: int) -> ProgressTracker:
        """Create a new progress tracker."""
        tracker = ProgressTracker(
            report_id=report_id,
            user_id=user_id,
            status=ProgressStatus.QUEUED
        )
        self.db.add(tracker)
        await self.db.flush()
        await self.db.refresh(tracker)
        return tracker
    
    async def update_stage_progress(
        self, 
        tracker_id: int, 
        stage: ProgressStage, 
        progress: float
    ) -> Optional[ProgressTracker]:
        """Update progress for a specific stage of an operation."""
        tracker = await self.get_tracker(tracker_id)
        if not tracker:
            return None
        
        tracker.update_stage_progress(stage, progress)
        tracker.estimated_completion_time = tracker.estimate_completion_time()
        
        await self.db.flush()
        await self.db.refresh(tracker)
        return tracker
    
    async def mark_completed(self, tracker_id: int) -> Optional[ProgressTracker]:
        """Mark a tracker as completed."""
        tracker = await self.get_tracker(tracker_id)
        if not tracker:
            return None
        
        tracker.status = ProgressStatus.COMPLETED
        tracker.progress_percent = 1.0
        tracker.completed_at = datetime.utcnow()
        
        # Set all stages to complete
        for stage in ProgressStage:
            tracker.stage_progress[stage] = 1.0
        
        await self.db.flush()
        await self.db.refresh(tracker)
        return tracker
    
    async def mark_failed(
        self, 
        tracker_id: int, 
        error_message: str, 
        error_details: Optional[Dict[str, Any]] = None
    ) -> Optional[ProgressTracker]:
        """Mark a tracker as failed."""
        tracker = await self.get_tracker(tracker_id)
        if not tracker:
            return None
        
        tracker.status = ProgressStatus.FAILED
        tracker.error_message = error_message
        tracker.error_details = error_details
        tracker.completed_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(tracker)
        return tracker
    
    async def cancel_tracker(self, tracker_id: int) -> Optional[ProgressTracker]:
        """Cancel a progress tracker."""
        tracker = await self.get_tracker(tracker_id)
        if not tracker:
            return None
        
        tracker.status = ProgressStatus.CANCELLED
        tracker.completed_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(tracker)
        return tracker


# Dependency for FastAPI
async def get_progress_service(db: AsyncSession = Depends(get_db)) -> ProgressService:
    """Get an instance of the ProgressService."""
    return ProgressService(db)
