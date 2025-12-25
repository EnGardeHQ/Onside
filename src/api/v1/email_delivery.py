"""API endpoints for Email Delivery.

This module provides REST API endpoints for managing email recipients and
tracking email delivery status.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime

from src.database.config import get_db
from src.auth.security import get_current_user
from src.models.user import User
from src.models.email_delivery import EmailRecipient, EmailDelivery, EmailStatus
from src.schemas.email_delivery import (
    EmailRecipientCreate,
    EmailRecipientUpdate,
    EmailRecipientResponse,
    EmailRecipientListResponse,
    EmailDeliveryResponse,
    EmailDeliveryListResponse,
    EmailDeliveryMetricsResponse,
    RetryDeliveryResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/email", tags=["email"])


# Email Recipients Endpoints

@router.post("/recipients", response_model=EmailRecipientResponse, status_code=status.HTTP_201_CREATED)
async def create_email_recipient(
    recipient_data: EmailRecipientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new email recipient."""
    try:
        # Check for duplicate
        result = await db.execute(
            select(EmailRecipient).where(
                and_(
                    EmailRecipient.company_id == recipient_data.company_id,
                    EmailRecipient.email == recipient_data.email
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email recipient already exists for this company"
            )

        recipient = EmailRecipient(
            company_id=recipient_data.company_id,
            email=recipient_data.email,
            name=recipient_data.name,
            is_active=True
        )

        db.add(recipient)
        await db.commit()
        await db.refresh(recipient)

        logger.info(f"Created email recipient {recipient.id}")
        return recipient

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating email recipient: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create email recipient: {str(e)}"
        )


@router.get("/recipients", response_model=EmailRecipientListResponse)
async def list_email_recipients(
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List email recipients with filtering."""
    try:
        query = select(EmailRecipient)

        filters = []
        if company_id:
            filters.append(EmailRecipient.company_id == company_id)
        if is_active is not None:
            filters.append(EmailRecipient.is_active == is_active)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(desc(EmailRecipient.created_at))

        # Get total
        count_query = select(EmailRecipient)
        if filters:
            count_query = count_query.where(and_(*filters))

        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        recipients = result.scalars().all()

        return {
            "recipients": recipients,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        logger.error(f"Error listing email recipients: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list email recipients: {str(e)}"
        )


@router.put("/recipients/{recipient_id}", response_model=EmailRecipientResponse)
async def update_email_recipient(
    recipient_id: int = Path(..., description="Recipient ID"),
    recipient_data: EmailRecipientUpdate = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update email recipient."""
    try:
        result = await db.execute(
            select(EmailRecipient).where(EmailRecipient.id == recipient_id)
        )
        recipient = result.scalar_one_or_none()

        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email recipient not found"
            )

        update_data = recipient_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(recipient, field, value)

        recipient.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(recipient)

        logger.info(f"Updated email recipient {recipient_id}")
        return recipient

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating email recipient: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update email recipient: {str(e)}"
        )


@router.delete("/recipients/{recipient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_email_recipient(
    recipient_id: int = Path(..., description="Recipient ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete email recipient."""
    try:
        result = await db.execute(
            select(EmailRecipient).where(EmailRecipient.id == recipient_id)
        )
        recipient = result.scalar_one_or_none()

        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email recipient not found"
            )

        await db.delete(recipient)
        await db.commit()

        logger.info(f"Deleted email recipient {recipient_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting email recipient: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete email recipient: {str(e)}"
        )


# Email Delivery Endpoints

@router.get("/deliveries", response_model=EmailDeliveryListResponse)
async def list_email_deliveries(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    report_id: Optional[int] = Query(None, description="Filter by report ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List email deliveries with filtering."""
    try:
        query = select(EmailDelivery)

        filters = []
        if status_filter:
            filters.append(EmailDelivery.status == status_filter)
        if report_id:
            filters.append(EmailDelivery.report_id == report_id)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(desc(EmailDelivery.created_at))

        # Get total
        count_query = select(EmailDelivery)
        if filters:
            count_query = count_query.where(and_(*filters))

        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        deliveries = result.scalars().all()

        return {
            "deliveries": deliveries,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        logger.error(f"Error listing email deliveries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list email deliveries: {str(e)}"
        )


@router.get("/deliveries/{delivery_id}", response_model=EmailDeliveryResponse)
async def get_email_delivery(
    delivery_id: int = Path(..., description="Delivery ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get email delivery details."""
    try:
        result = await db.execute(
            select(EmailDelivery).where(EmailDelivery.id == delivery_id)
        )
        delivery = result.scalar_one_or_none()

        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email delivery not found"
            )

        return delivery

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email delivery: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email delivery: {str(e)}"
        )


@router.post("/deliveries/{delivery_id}/retry", response_model=RetryDeliveryResponse)
async def retry_failed_delivery(
    delivery_id: int = Path(..., description="Delivery ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retry a failed email delivery."""
    try:
        result = await db.execute(
            select(EmailDelivery).where(EmailDelivery.id == delivery_id)
        )
        delivery = result.scalar_one_or_none()

        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email delivery not found"
            )

        if not delivery.should_retry():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Delivery cannot be retried (max retries exceeded or not in failed status)"
            )

        # Reset status to queued for retry
        delivery.status = EmailStatus.QUEUED.value
        delivery.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(delivery)

        logger.info(f"Retrying email delivery {delivery_id}")

        return {
            "message": "Email delivery queued for retry",
            "delivery_id": delivery_id,
            "new_retry_count": delivery.retry_count,
            "status": delivery.status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying email delivery: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry email delivery: {str(e)}"
        )


@router.get("/deliveries/{delivery_id}/metrics", response_model=EmailDeliveryMetricsResponse)
async def get_delivery_metrics(
    delivery_id: int = Path(..., description="Delivery ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get metrics for an email delivery."""
    try:
        result = await db.execute(
            select(EmailDelivery).where(EmailDelivery.id == delivery_id)
        )
        delivery = result.scalar_one_or_none()

        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email delivery not found"
            )

        metrics = delivery.get_delivery_metrics()
        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting delivery metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get delivery metrics: {str(e)}"
        )
