"""
Progress Tracking Models (S5-04)

This module defines the database models for tracking report generation progress
in real-time, following Semantic Seed Venture Studio Coding Standards V2.0.

The models connect to the actual PostgreSQL database as required:
- Host: localhost
- Port: 5432
- Database: onside
- User: tobymorning
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

class ProgressStatus(str, Enum):
    """Status of a tracked operation."""
    QUEUED = "QUEUED"           # Operation is queued but not started
    INITIALIZING = "INITIALIZING"  # Operation is starting up
    IN_PROGRESS = "IN_PROGRESS"  # Operation is running
    COMPLETED = "COMPLETED"      # Operation completed successfully
    FAILED = "FAILED"           # Operation failed
    CANCELLED = "CANCELLED"      # Operation was cancelled

class ProgressStage(str, Enum):
    """Stages of report generation."""
    DATA_COLLECTION = "DATA_COLLECTION"
    COMPETITOR_ANALYSIS = "COMPETITOR_ANALYSIS"
    MARKET_ANALYSIS = "MARKET_ANALYSIS"
    AUDIENCE_ANALYSIS = "AUDIENCE_ANALYSIS"
    REPORT_GENERATION = "REPORT_GENERATION"
    VISUALIZATION = "VISUALIZATION"
    FINALIZATION = "FINALIZATION"

class ProgressTracker(Base):
    """Model for tracking operation progress."""
    
    __tablename__ = "progress_trackers"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Status tracking
    status: Mapped[ProgressStatus] = mapped_column(SQLEnum(ProgressStatus), default=ProgressStatus.QUEUED)
    current_stage: Mapped[ProgressStage] = mapped_column(SQLEnum(ProgressStage), nullable=True)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Stage weights for progress calculation
    stage_weights: Mapped[Dict[str, float]] = mapped_column(
        JSON,
        default={
            ProgressStage.DATA_COLLECTION: 0.15,
            ProgressStage.COMPETITOR_ANALYSIS: 0.25,
            ProgressStage.MARKET_ANALYSIS: 0.20,
            ProgressStage.AUDIENCE_ANALYSIS: 0.20,
            ProgressStage.REPORT_GENERATION: 0.10,
            ProgressStage.VISUALIZATION: 0.05,
            ProgressStage.FINALIZATION: 0.05
        }
    )
    
    # Stage progress tracking
    stage_progress: Mapped[Dict[str, float]] = mapped_column(
        JSON,
        default={}
    )
    
    # Timing information
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    estimated_completion_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    report = relationship("Report", back_populates="progress_tracker")
    user = relationship("User", back_populates="progress_trackers")
    
    def calculate_overall_progress(self) -> float:
        """Calculate overall progress based on stage weights and progress."""
        overall_progress = 0.0
        
        for stage, weight in self.stage_weights.items():
            stage_progress = self.stage_progress.get(stage, 0.0)
            overall_progress += weight * stage_progress
        
        return round(overall_progress, 2)
    
    def update_stage_progress(self, stage: ProgressStage, progress: float):
        """Update progress for a specific stage.
        
        Args:
            stage: The stage to update
            progress: Progress value between 0 and 1
        """
        # Ensure progress is between 0 and 1
        progress = max(0.0, min(1.0, progress))
        
        # Update stage progress
        self.stage_progress[stage] = progress
        
        # Update overall progress
        self.progress_percent = self.calculate_overall_progress()
        
        # Update current stage if not set
        if not self.current_stage:
            self.current_stage = stage
        
        # Update status if needed
        if self.status == ProgressStatus.QUEUED and progress > 0:
            self.status = ProgressStatus.IN_PROGRESS
            self.started_at = datetime.utcnow()
        elif progress >= 1.0 and all(
            self.stage_progress.get(s, 0.0) >= 1.0 
            for s in self.stage_weights.keys()
        ):
            self.status = ProgressStatus.COMPLETED
            self.completed_at = datetime.utcnow()
    
    def estimate_completion_time(self) -> Optional[datetime]:
        """Estimate completion time based on current progress and elapsed time.
        
        Returns:
            Estimated completion time or None if cannot be estimated
        """
        if not self.started_at or self.progress_percent <= 0:
            return None
        
        elapsed_time = (datetime.utcnow() - self.started_at).total_seconds()
        if elapsed_time <= 0:
            return None
        
        # Calculate rate of progress
        rate = self.progress_percent / elapsed_time
        if rate <= 0:
            return None
        
        # Estimate remaining time
        remaining_progress = 1.0 - self.progress_percent
        remaining_seconds = remaining_progress / rate
        
        return datetime.utcnow().fromtimestamp(
            datetime.utcnow().timestamp() + remaining_seconds
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tracker to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "report_id": self.report_id,
            "user_id": self.user_id,
            "status": self.status,
            "current_stage": self.current_stage,
            "progress_percent": self.progress_percent,
            "stage_progress": self.stage_progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_completion_time": (
                self.estimated_completion_time.isoformat() 
                if self.estimated_completion_time else None
            ),
            "error_message": self.error_message,
            "error_details": self.error_details
        }
