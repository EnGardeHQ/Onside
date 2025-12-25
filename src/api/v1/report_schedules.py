"""API endpoints for Report Schedules.

This module provides REST API endpoints for managing automated report schedules,
including CRUD operations, execution tracking, and schedule management.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime

from src.database.config import get_db
from src.auth.security import get_current_user
from src.models.user import User
from src.models.report_schedule import ReportSchedule, ScheduleExecution
from src.schemas.report_schedule import (
    ReportScheduleCreate,
    ReportScheduleUpdate,
    ReportScheduleResponse,
    ReportScheduleListResponse,
    ScheduleExecutionResponse,
    ScheduleExecutionListResponse,
    ScheduleStatsResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/report-schedules", tags=["report-schedules"])


@router.post("", response_model=ReportScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_report_schedule(
    schedule_data: ReportScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new report schedule.

    Args:
        schedule_data: Schedule configuration
        db: Database session
        current_user: Authenticated user

    Returns:
        Created report schedule

    Raises:
        HTTPException: If cron expression is invalid or creation fails
    """
    try:
        # Create schedule
        schedule = ReportSchedule(
            user_id=current_user.id,
            company_id=schedule_data.company_id,
            name=schedule_data.name,
            description=schedule_data.description,
            report_type=schedule_data.report_type,
            cron_expression=schedule_data.cron_expression,
            parameters=schedule_data.parameters,
            email_recipients=schedule_data.email_recipients,
            notify_on_completion=schedule_data.notify_on_completion,
            is_active=True
        )

        # Validate cron expression
        if not schedule.validate_cron_expression():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cron expression"
            )

        # Calculate next run time
        schedule.next_run_at = schedule.calculate_next_run()

        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)

        logger.info(f"Created report schedule {schedule.id} for user {current_user.id}")
        return schedule

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating report schedule: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create report schedule: {str(e)}"
        )


@router.get("", response_model=ReportScheduleListResponse)
async def list_report_schedules(
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List report schedules with filtering.

    Args:
        company_id: Optional company ID filter
        report_type: Optional report type filter
        is_active: Optional active status filter
        page: Page number
        page_size: Items per page
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of report schedules
    """
    try:
        # Build query
        query = select(ReportSchedule).where(ReportSchedule.user_id == current_user.id)

        # Apply filters
        if company_id:
            query = query.where(ReportSchedule.company_id == company_id)
        if report_type:
            query = query.where(ReportSchedule.report_type == report_type)
        if is_active is not None:
            query = query.where(ReportSchedule.is_active == is_active)

        # Order by created_at descending
        query = query.order_by(desc(ReportSchedule.created_at))

        # Get total count
        count_query = select(ReportSchedule).where(ReportSchedule.user_id == current_user.id)
        if company_id:
            count_query = count_query.where(ReportSchedule.company_id == company_id)
        if report_type:
            count_query = count_query.where(ReportSchedule.report_type == report_type)
        if is_active is not None:
            count_query = count_query.where(ReportSchedule.is_active == is_active)

        result = await db.execute(count_query)
        total = len(result.scalars().all())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await db.execute(query)
        schedules = result.scalars().all()

        return {
            "schedules": schedules,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        logger.error(f"Error listing report schedules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list report schedules: {str(e)}"
        )


@router.get("/{schedule_id}", response_model=ReportScheduleResponse)
async def get_report_schedule(
    schedule_id: int = Path(..., description="Schedule ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get report schedule details.

    Args:
        schedule_id: Schedule ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Report schedule details

    Raises:
        HTTPException: If schedule not found or access denied
    """
    try:
        result = await db.execute(
            select(ReportSchedule).where(
                and_(
                    ReportSchedule.id == schedule_id,
                    ReportSchedule.user_id == current_user.id
                )
            )
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report schedule not found"
            )

        return schedule

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report schedule: {str(e)}"
        )


@router.put("/{schedule_id}", response_model=ReportScheduleResponse)
async def update_report_schedule(
    schedule_id: int = Path(..., description="Schedule ID"),
    schedule_data: ReportScheduleUpdate = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update report schedule.

    Args:
        schedule_id: Schedule ID
        schedule_data: Updated schedule data
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated report schedule

    Raises:
        HTTPException: If schedule not found or update fails
    """
    try:
        # Get schedule
        result = await db.execute(
            select(ReportSchedule).where(
                and_(
                    ReportSchedule.id == schedule_id,
                    ReportSchedule.user_id == current_user.id
                )
            )
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report schedule not found"
            )

        # Update fields
        update_data = schedule_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(schedule, field, value)

        # Validate cron expression if updated
        if 'cron_expression' in update_data:
            if not schedule.validate_cron_expression():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid cron expression"
                )
            schedule.next_run_at = schedule.calculate_next_run()

        schedule.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(schedule)

        logger.info(f"Updated report schedule {schedule_id}")
        return schedule

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating report schedule: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update report schedule: {str(e)}"
        )


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report_schedule(
    schedule_id: int = Path(..., description="Schedule ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete report schedule.

    Args:
        schedule_id: Schedule ID
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException: If schedule not found or deletion fails
    """
    try:
        # Get schedule
        result = await db.execute(
            select(ReportSchedule).where(
                and_(
                    ReportSchedule.id == schedule_id,
                    ReportSchedule.user_id == current_user.id
                )
            )
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report schedule not found"
            )

        await db.delete(schedule)
        await db.commit()

        logger.info(f"Deleted report schedule {schedule_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report schedule: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete report schedule: {str(e)}"
        )


@router.post("/{schedule_id}/pause", response_model=ReportScheduleResponse)
async def pause_report_schedule(
    schedule_id: int = Path(..., description="Schedule ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pause report schedule.

    Args:
        schedule_id: Schedule ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated report schedule

    Raises:
        HTTPException: If schedule not found
    """
    try:
        # Get schedule
        result = await db.execute(
            select(ReportSchedule).where(
                and_(
                    ReportSchedule.id == schedule_id,
                    ReportSchedule.user_id == current_user.id
                )
            )
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report schedule not found"
            )

        schedule.pause()
        await db.commit()
        await db.refresh(schedule)

        logger.info(f"Paused report schedule {schedule_id}")
        return schedule

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing report schedule: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause report schedule: {str(e)}"
        )


@router.post("/{schedule_id}/resume", response_model=ReportScheduleResponse)
async def resume_report_schedule(
    schedule_id: int = Path(..., description="Schedule ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resume report schedule.

    Args:
        schedule_id: Schedule ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated report schedule

    Raises:
        HTTPException: If schedule not found
    """
    try:
        # Get schedule
        result = await db.execute(
            select(ReportSchedule).where(
                and_(
                    ReportSchedule.id == schedule_id,
                    ReportSchedule.user_id == current_user.id
                )
            )
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report schedule not found"
            )

        schedule.resume()
        await db.commit()
        await db.refresh(schedule)

        logger.info(f"Resumed report schedule {schedule_id}")
        return schedule

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming report schedule: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume report schedule: {str(e)}"
        )


@router.get("/{schedule_id}/executions", response_model=ScheduleExecutionListResponse)
async def get_schedule_executions(
    schedule_id: int = Path(..., description="Schedule ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get execution history for a schedule.

    Args:
        schedule_id: Schedule ID
        page: Page number
        page_size: Items per page
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of executions

    Raises:
        HTTPException: If schedule not found
    """
    try:
        # Verify schedule ownership
        result = await db.execute(
            select(ReportSchedule).where(
                and_(
                    ReportSchedule.id == schedule_id,
                    ReportSchedule.user_id == current_user.id
                )
            )
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report schedule not found"
            )

        # Get executions
        query = select(ScheduleExecution).where(
            ScheduleExecution.schedule_id == schedule_id
        ).order_by(desc(ScheduleExecution.started_at))

        # Get total count
        count_result = await db.execute(
            select(ScheduleExecution).where(ScheduleExecution.schedule_id == schedule_id)
        )
        total = len(count_result.scalars().all())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        executions = result.scalars().all()

        return {
            "executions": executions,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schedule executions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schedule executions: {str(e)}"
        )


@router.get("/{schedule_id}/stats", response_model=ScheduleStatsResponse)
async def get_schedule_stats(
    schedule_id: int = Path(..., description="Schedule ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get execution statistics for a schedule.

    Args:
        schedule_id: Schedule ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Schedule execution statistics

    Raises:
        HTTPException: If schedule not found
    """
    try:
        # Get schedule with executions
        result = await db.execute(
            select(ReportSchedule).where(
                and_(
                    ReportSchedule.id == schedule_id,
                    ReportSchedule.user_id == current_user.id
                )
            )
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report schedule not found"
            )

        # Get statistics
        stats = schedule.get_execution_stats()
        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schedule stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schedule stats: {str(e)}"
        )
