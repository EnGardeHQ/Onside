"""API Usage Repository Module.

This module provides database operations for API usage tracking.
Handles recording, retrieval, and management of external API usage
metrics and quota information.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any

from sqlalchemy import select, delete, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.external_api import APIUsageRecord


class APIUsageRepository:
    """Repository for API usage tracking database operations.

    Provides methods for recording API calls, tracking quotas,
    and managing billing periods for external API integrations.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def create(self, usage: APIUsageRecord) -> APIUsageRecord:
        """Create a new API usage record.

        Args:
            usage: APIUsageRecord instance to store

        Returns:
            Created APIUsageRecord with populated ID
        """
        self.db.add(usage)
        await self.db.commit()
        await self.db.refresh(usage)
        return usage

    async def record_usage(
        self,
        api_name: str,
        endpoint: Optional[str] = None,
        count: int = 1,
        cost_per_call: Optional[Decimal] = None
    ) -> APIUsageRecord:
        """Record API usage, creating or updating the current period's record.

        This method finds or creates an API usage record for the current
        billing period and increments the request count.

        Args:
            api_name: Name of the API (e.g., 'gnews', 'ipinfo')
            endpoint: Specific API endpoint called (optional)
            count: Number of requests to add (default: 1)
            cost_per_call: Cost per API call in USD (optional)

        Returns:
            Updated or created APIUsageRecord
        """
        # Get current period (monthly by default)
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Calculate period end (first day of next month)
        if period_start.month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1)
        else:
            period_end = period_start.replace(month=period_start.month + 1)

        # Try to find existing record for this period
        existing = await self._get_current_period_record(
            api_name, endpoint, period_start, period_end
        )

        if existing:
            # Update existing record
            existing.request_count += count
            if cost_per_call and existing.cost_per_call:
                existing.total_cost = (
                    existing.cost_per_call * existing.request_count
                )

            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new record
            usage = APIUsageRecord(
                api_name=api_name,
                endpoint=endpoint,
                request_count=count,
                period_start=period_start,
                period_end=period_end,
                cost_per_call=cost_per_call,
                total_cost=cost_per_call * count if cost_per_call else None
            )
            self.db.add(usage)
            await self.db.commit()
            await self.db.refresh(usage)
            return usage

    async def _get_current_period_record(
        self,
        api_name: str,
        endpoint: Optional[str],
        period_start: datetime,
        period_end: datetime
    ) -> Optional[APIUsageRecord]:
        """Get the current period's usage record for an API.

        Args:
            api_name: Name of the API
            endpoint: Specific endpoint (optional)
            period_start: Start of the period
            period_end: End of the period

        Returns:
            APIUsageRecord if found, None otherwise
        """
        conditions = [
            APIUsageRecord.api_name == api_name,
            APIUsageRecord.period_start == period_start,
            APIUsageRecord.period_end == period_end
        ]

        if endpoint:
            conditions.append(APIUsageRecord.endpoint == endpoint)
        else:
            conditions.append(APIUsageRecord.endpoint.is_(None))

        result = await self.db.execute(
            select(APIUsageRecord).where(and_(*conditions))
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, record_id: int) -> Optional[APIUsageRecord]:
        """Get an API usage record by its database ID.

        Args:
            record_id: Database ID of the record

        Returns:
            APIUsageRecord if found, None otherwise
        """
        result = await self.db.execute(
            select(APIUsageRecord).where(APIUsageRecord.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_usage(
        self,
        api_name: str,
        period_start: datetime,
        period_end: datetime
    ) -> List[APIUsageRecord]:
        """Get API usage records for a specific period.

        Args:
            api_name: Name of the API
            period_start: Start of the period
            period_end: End of the period

        Returns:
            List of APIUsageRecord instances for the period
        """
        result = await self.db.execute(
            select(APIUsageRecord)
            .where(
                and_(
                    APIUsageRecord.api_name == api_name,
                    APIUsageRecord.period_start >= period_start,
                    APIUsageRecord.period_end <= period_end
                )
            )
            .order_by(APIUsageRecord.period_start.desc())
        )
        return list(result.scalars().all())

    async def get_quota_status(self, api_name: str) -> Dict[str, Any]:
        """Get current quota status for an API.

        Returns usage statistics including request count, quota limit,
        remaining quota, and usage percentage.

        Args:
            api_name: Name of the API

        Returns:
            Dictionary with quota status information
        """
        # Get current period
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if period_start.month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1)
        else:
            period_end = period_start.replace(month=period_start.month + 1)

        # Get total usage for current period
        result = await self.db.execute(
            select(
                func.sum(APIUsageRecord.request_count).label("total_requests"),
                func.max(APIUsageRecord.quota_limit).label("quota_limit"),
                func.sum(APIUsageRecord.total_cost).label("total_cost")
            )
            .where(
                and_(
                    APIUsageRecord.api_name == api_name,
                    APIUsageRecord.period_start == period_start,
                    APIUsageRecord.period_end == period_end
                )
            )
        )

        row = result.one_or_none()

        total_requests = row.total_requests or 0 if row else 0
        quota_limit = row.quota_limit if row else None
        total_cost = float(row.total_cost) if row and row.total_cost else 0.0

        quota_remaining = None
        usage_percentage = None
        is_exceeded = False

        if quota_limit:
            quota_remaining = max(0, quota_limit - total_requests)
            usage_percentage = (total_requests / quota_limit) * 100
            is_exceeded = total_requests >= quota_limit

        return {
            "api_name": api_name,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "request_count": total_requests,
            "quota_limit": quota_limit,
            "quota_remaining": quota_remaining,
            "usage_percentage": usage_percentage,
            "is_exceeded": is_exceeded,
            "total_cost": total_cost
        }

    async def set_quota_limit(
        self,
        api_name: str,
        quota_limit: int,
        endpoint: Optional[str] = None
    ) -> bool:
        """Set the quota limit for an API for the current period.

        Args:
            api_name: Name of the API
            quota_limit: Maximum allowed requests
            endpoint: Specific endpoint (optional)

        Returns:
            True if quota was set, False otherwise
        """
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if period_start.month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1)
        else:
            period_end = period_start.replace(month=period_start.month + 1)

        # Get or create current period record
        existing = await self._get_current_period_record(
            api_name, endpoint, period_start, period_end
        )

        if existing:
            existing.quota_limit = quota_limit
            await self.db.commit()
            return True
        else:
            # Create new record with quota
            usage = APIUsageRecord(
                api_name=api_name,
                endpoint=endpoint,
                request_count=0,
                quota_limit=quota_limit,
                period_start=period_start,
                period_end=period_end
            )
            self.db.add(usage)
            await self.db.commit()
            return True

    async def reset_period(self, api_name: str) -> bool:
        """Reset usage for the current billing period.

        Creates a new period record with zero usage.
        Typically called at the start of a new billing cycle.

        Args:
            api_name: Name of the API to reset

        Returns:
            True if reset was successful
        """
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if period_start.month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1)
        else:
            period_end = period_start.replace(month=period_start.month + 1)

        # Delete existing records for current period
        await self.db.execute(
            delete(APIUsageRecord).where(
                and_(
                    APIUsageRecord.api_name == api_name,
                    APIUsageRecord.period_start == period_start,
                    APIUsageRecord.period_end == period_end
                )
            )
        )
        await self.db.commit()

        return True

    async def get_usage_by_endpoint(
        self,
        api_name: str
    ) -> Dict[str, int]:
        """Get usage breakdown by endpoint for current period.

        Args:
            api_name: Name of the API

        Returns:
            Dictionary mapping endpoints to request counts
        """
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if period_start.month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1)
        else:
            period_end = period_start.replace(month=period_start.month + 1)

        result = await self.db.execute(
            select(
                APIUsageRecord.endpoint,
                func.sum(APIUsageRecord.request_count).label("count")
            )
            .where(
                and_(
                    APIUsageRecord.api_name == api_name,
                    APIUsageRecord.period_start == period_start,
                    APIUsageRecord.period_end == period_end
                )
            )
            .group_by(APIUsageRecord.endpoint)
        )

        return {
            row.endpoint or "default": row.count
            for row in result.all()
        }

    async def get_all_apis_usage(self) -> List[Dict[str, Any]]:
        """Get current usage status for all APIs.

        Returns:
            List of quota status dictionaries for all tracked APIs
        """
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if period_start.month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1)
        else:
            period_end = period_start.replace(month=period_start.month + 1)

        result = await self.db.execute(
            select(
                APIUsageRecord.api_name,
                func.sum(APIUsageRecord.request_count).label("total_requests"),
                func.max(APIUsageRecord.quota_limit).label("quota_limit"),
                func.sum(APIUsageRecord.total_cost).label("total_cost")
            )
            .where(
                and_(
                    APIUsageRecord.period_start == period_start,
                    APIUsageRecord.period_end == period_end
                )
            )
            .group_by(APIUsageRecord.api_name)
        )

        usage_list = []
        for row in result.all():
            total_requests = row.total_requests or 0
            quota_limit = row.quota_limit

            quota_remaining = None
            usage_percentage = None
            is_exceeded = False

            if quota_limit:
                quota_remaining = max(0, quota_limit - total_requests)
                usage_percentage = (total_requests / quota_limit) * 100
                is_exceeded = total_requests >= quota_limit

            usage_list.append({
                "api_name": row.api_name,
                "request_count": total_requests,
                "quota_limit": quota_limit,
                "quota_remaining": quota_remaining,
                "usage_percentage": usage_percentage,
                "is_exceeded": is_exceeded,
                "total_cost": float(row.total_cost) if row.total_cost else 0.0
            })

        return usage_list

    async def delete_old_records(self, months_old: int) -> int:
        """Delete API usage records older than specified months.

        Args:
            months_old: Delete records older than this many months

        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=months_old * 30)

        result = await self.db.execute(
            delete(APIUsageRecord).where(
                APIUsageRecord.period_end < cutoff_date
            )
        )
        await self.db.commit()

        return result.rowcount
