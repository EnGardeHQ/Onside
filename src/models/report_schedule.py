"""Report Schedule models for scheduled report generation."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, Optional, List
from sqlalchemy import ForeignKey, JSON, DateTime, String, Boolean, Integer, Float, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from croniter import croniter

from src.database import Base


class ReportSchedule(Base):
    """Model for scheduling automated report generation.

    This model supports cron-style scheduling for report generation with
    configurable parameters, email notifications, and execution tracking.
    """
    __tablename__ = "report_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    parameters: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_recipients: Mapped[Optional[List]] = mapped_column(JSON, nullable=True)
    notify_on_completion: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()", onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="report_schedules")
    company = relationship("Company", back_populates="report_schedules")
    executions = relationship("ScheduleExecution", back_populates="schedule", cascade="all, delete-orphan")

    def validate_cron_expression(self) -> bool:
        """Validate the cron expression.

        Returns:
            bool: True if cron expression is valid
        """
        try:
            croniter(self.cron_expression)
            return True
        except Exception:
            return False

    def calculate_next_run(self) -> Optional[datetime]:
        """Calculate the next execution time based on cron expression.

        Returns:
            Optional[datetime]: Next scheduled execution time
        """
        try:
            base_time = self.last_run_at or datetime.utcnow()
            cron = croniter(self.cron_expression, base_time)
            return cron.get_next(datetime)
        except Exception:
            return None

    def pause(self) -> None:
        """Pause the schedule."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def resume(self) -> None:
        """Resume the schedule."""
        self.is_active = True
        self.next_run_at = self.calculate_next_run()
        self.updated_at = datetime.utcnow()

    def get_execution_stats(self) -> Dict:
        """Get execution statistics for this schedule.

        Returns:
            Dict: Statistics including success rate, average execution time, etc.
        """
        if not self.executions:
            return {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0
            }

        total = len(self.executions)
        successful = sum(1 for e in self.executions if e.status == "completed")
        failed = sum(1 for e in self.executions if e.status == "failed")

        execution_times = [
            e.execution_time_seconds
            for e in self.executions
            if e.execution_time_seconds is not None
        ]
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0.0

        return {
            "total_runs": total,
            "successful_runs": successful,
            "failed_runs": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0.0,
            "avg_execution_time": avg_time
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"<ReportSchedule(id={self.id}, name='{self.name}', active={self.is_active})>"


class ScheduleExecution(Base):
    """Model for tracking schedule execution history.

    This model stores detailed information about each scheduled report execution,
    including status, timing, and error information.
    """
    __tablename__ = "schedule_executions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("report_schedules.id", ondelete="CASCADE"), nullable=False)
    report_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reports.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()")

    # Relationships
    schedule = relationship("ReportSchedule", back_populates="executions")
    report = relationship("Report", back_populates="schedule_executions")

    def complete(self, report_id: Optional[int] = None) -> None:
        """Mark execution as completed.

        Args:
            report_id: ID of the generated report
        """
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.report_id = report_id
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()

    def fail(self, error_message: str) -> None:
        """Mark execution as failed.

        Args:
            error_message: Error description
        """
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()

    def __repr__(self) -> str:
        """String representation."""
        return f"<ScheduleExecution(id={self.id}, schedule_id={self.schedule_id}, status='{self.status}')>"
