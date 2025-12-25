"""
API Usage Monitoring and Quota Tracking Service

Tracks external API usage and manages quotas across all integrated services:
- GNews API (1000 req/day free tier)
- SERP API
- IPInfo API
- WhoAPI
- Google Analytics API
- PageSpeed Insights API
- YouTube API
- Google Custom Search API

Features:
- Real-time usage tracking
- Quota management and enforcement
- Cost estimation
- Threshold alerts (80%, 90%, 100%)
- Usage analytics and reporting
- Automatic throttling
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from src.models.external_api import APIUsageRecord

logger = logging.getLogger(__name__)


class APIName(str, Enum):
    """Supported external APIs."""
    GNEWS = "gnews"
    SERP = "serp"
    IPINFO = "ipinfo"
    WHOAPI = "whoapi"
    GOOGLE_ANALYTICS = "google_analytics"
    PAGESPEED = "pagespeed"
    YOUTUBE = "youtube"
    GOOGLE_CUSTOM_SEARCH = "google_custom_search"


class QuotaPeriod(str, Enum):
    """Quota period types."""
    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"


# API quota configurations
API_QUOTAS = {
    APIName.GNEWS: {
        'limit': 1000,
        'period': QuotaPeriod.DAILY,
        'cost_per_call': Decimal('0.0'),  # Free tier
        'warning_threshold': 0.8
    },
    APIName.SERP: {
        'limit': 5000,
        'period': QuotaPeriod.MONTHLY,
        'cost_per_call': Decimal('0.002'),
        'warning_threshold': 0.8
    },
    APIName.IPINFO: {
        'limit': 50000,
        'period': QuotaPeriod.MONTHLY,
        'cost_per_call': Decimal('0.0'),  # Free tier
        'warning_threshold': 0.8
    },
    APIName.WHOAPI: {
        'limit': 500,
        'period': QuotaPeriod.MONTHLY,
        'cost_per_call': Decimal('0.01'),
        'warning_threshold': 0.8
    },
    APIName.GOOGLE_ANALYTICS: {
        'limit': 25000,
        'period': QuotaPeriod.DAILY,
        'cost_per_call': Decimal('0.0'),  # Free tier
        'warning_threshold': 0.8
    },
    APIName.PAGESPEED: {
        'limit': 25000,
        'period': QuotaPeriod.DAILY,
        'cost_per_call': Decimal('0.0'),  # Free tier
        'warning_threshold': 0.8
    },
    APIName.YOUTUBE: {
        'limit': 10000,
        'period': QuotaPeriod.DAILY,
        'cost_per_call': Decimal('0.0'),  # Quota units, not cost
        'warning_threshold': 0.8
    },
    APIName.GOOGLE_CUSTOM_SEARCH: {
        'limit': 100,
        'period': QuotaPeriod.DAILY,
        'cost_per_call': Decimal('0.005'),
        'warning_threshold': 0.8
    }
}


class APIUsageTracker:
    """
    Tracks API usage and manages quotas.
    """

    def __init__(self, db: AsyncSession):
        """Initialize usage tracker.

        Args:
            db: Database session
        """
        self.db = db

    async def track_api_call(
        self,
        api_name: APIName,
        endpoint: Optional[str] = None,
        success: bool = True,
        cost_override: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Track an API call.

        Args:
            api_name: Name of the API
            endpoint: Specific endpoint called
            success: Whether call was successful
            cost_override: Override default cost per call

        Returns:
            Dictionary with tracking result and current status
        """
        # Get current period
        period_start, period_end = self._get_current_period(api_name)

        # Get or create usage record
        usage_record = await self._get_or_create_usage_record(
            api_name, endpoint, period_start, period_end
        )

        # Increment request count (only if successful)
        if success:
            usage_record.request_count += 1

        # Update cost
        quota_config = API_QUOTAS.get(api_name)
        if quota_config:
            cost_per_call = cost_override or quota_config['cost_per_call']
            if usage_record.total_cost is None:
                usage_record.total_cost = Decimal('0.0')
            usage_record.total_cost += cost_per_call

        await self.db.commit()
        await self.db.refresh(usage_record)

        # Check quota status
        quota_status = await self.check_quota_status(api_name)

        return {
            'tracked': True,
            'api_name': api_name.value,
            'current_count': usage_record.request_count,
            'quota_limit': usage_record.quota_limit,
            'quota_status': quota_status
        }

    async def check_quota_status(self, api_name: APIName) -> Dict[str, Any]:
        """Check quota status for an API.

        Args:
            api_name: Name of the API

        Returns:
            Dictionary with quota status
        """
        period_start, period_end = self._get_current_period(api_name)

        usage_record = await self._get_usage_record(
            api_name, None, period_start, period_end
        )

        if not usage_record:
            return {
                'quota_available': True,
                'usage_count': 0,
                'quota_limit': API_QUOTAS.get(api_name, {}).get('limit', 0),
                'usage_percentage': 0.0,
                'remaining': API_QUOTAS.get(api_name, {}).get('limit', 0),
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat()
            }

        quota_limit = usage_record.quota_limit or 0
        usage_count = usage_record.request_count
        usage_percentage = (usage_count / quota_limit * 100) if quota_limit > 0 else 0

        quota_available = usage_count < quota_limit
        threshold_status = self._get_threshold_status(usage_percentage)

        return {
            'quota_available': quota_available,
            'usage_count': usage_count,
            'quota_limit': quota_limit,
            'usage_percentage': round(usage_percentage, 2),
            'remaining': max(0, quota_limit - usage_count),
            'threshold_status': threshold_status,
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'estimated_cost': float(usage_record.total_cost or 0)
        }

    async def can_make_api_call(self, api_name: APIName) -> bool:
        """Check if API call can be made without exceeding quota.

        Args:
            api_name: Name of the API

        Returns:
            True if call can be made, False otherwise
        """
        status = await self.check_quota_status(api_name)
        return status['quota_available']

    async def get_usage_analytics(
        self,
        api_name: Optional[APIName] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get usage analytics.

        Args:
            api_name: Optional API name to filter by
            days: Number of days to analyze

        Returns:
            Dictionary with usage analytics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Build query
        query = select(APIUsageRecord).where(
            APIUsageRecord.period_start >= cutoff_date
        )

        if api_name:
            query = query.where(APIUsageRecord.api_name == api_name.value)

        result = await self.db.execute(query)
        records = result.scalars().all()

        # Calculate analytics
        total_requests = sum(r.request_count for r in records)
        total_cost = sum(float(r.total_cost or 0) for r in records)

        # Group by API
        by_api = {}
        for record in records:
            api = record.api_name
            if api not in by_api:
                by_api[api] = {
                    'requests': 0,
                    'cost': 0.0,
                    'quota_exceeded_count': 0
                }

            by_api[api]['requests'] += record.request_count
            by_api[api]['cost'] += float(record.total_cost or 0)

            if record.is_quota_exceeded:
                by_api[api]['quota_exceeded_count'] += 1

        return {
            'period_days': days,
            'total_requests': total_requests,
            'total_cost': round(total_cost, 2),
            'by_api': by_api,
            'records_analyzed': len(records)
        }

    async def get_cost_estimate(
        self,
        api_name: APIName,
        projected_calls: int
    ) -> Dict[str, Any]:
        """Get cost estimate for projected API calls.

        Args:
            api_name: Name of the API
            projected_calls: Number of projected calls

        Returns:
            Dictionary with cost estimate
        """
        quota_config = API_QUOTAS.get(api_name)
        if not quota_config:
            return {'error': 'Unknown API'}

        cost_per_call = quota_config['cost_per_call']
        estimated_cost = float(cost_per_call * projected_calls)

        # Check against quota
        quota_limit = quota_config['limit']
        periods_needed = (projected_calls + quota_limit - 1) // quota_limit

        return {
            'api_name': api_name.value,
            'projected_calls': projected_calls,
            'cost_per_call': float(cost_per_call),
            'estimated_cost': round(estimated_cost, 2),
            'quota_limit': quota_limit,
            'periods_needed': periods_needed,
            'quota_period': quota_config['period'].value
        }

    async def reset_quota(self, api_name: APIName) -> Dict[str, Any]:
        """Reset quota for an API (admin function).

        Args:
            api_name: Name of the API

        Returns:
            Dictionary with reset result
        """
        period_start, period_end = self._get_current_period(api_name)

        result = await self.db.execute(
            select(APIUsageRecord).where(
                and_(
                    APIUsageRecord.api_name == api_name.value,
                    APIUsageRecord.period_start >= period_start,
                    APIUsageRecord.period_end <= period_end
                )
            )
        )

        records = result.scalars().all()

        for record in records:
            record.request_count = 0
            record.total_cost = Decimal('0.0')

        await self.db.commit()

        return {
            'reset': True,
            'api_name': api_name.value,
            'records_reset': len(records)
        }

    def _get_current_period(self, api_name: APIName) -> tuple:
        """Get current period start and end.

        Args:
            api_name: Name of the API

        Returns:
            Tuple of (period_start, period_end)
        """
        quota_config = API_QUOTAS.get(api_name)
        if not quota_config:
            # Default to daily
            period = QuotaPeriod.DAILY
        else:
            period = quota_config['period']

        now = datetime.utcnow()

        if period == QuotaPeriod.HOURLY:
            period_start = now.replace(minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(hours=1)
        elif period == QuotaPeriod.DAILY:
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
        else:  # MONTHLY
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Get first day of next month
            if now.month == 12:
                period_end = period_start.replace(year=now.year + 1, month=1)
            else:
                period_end = period_start.replace(month=now.month + 1)

        return period_start, period_end

    async def _get_usage_record(
        self,
        api_name: APIName,
        endpoint: Optional[str],
        period_start: datetime,
        period_end: datetime
    ) -> Optional[APIUsageRecord]:
        """Get usage record for current period.

        Args:
            api_name: Name of the API
            endpoint: Optional endpoint
            period_start: Period start time
            period_end: Period end time

        Returns:
            APIUsageRecord or None
        """
        query = select(APIUsageRecord).where(
            and_(
                APIUsageRecord.api_name == api_name.value,
                APIUsageRecord.period_start == period_start,
                APIUsageRecord.period_end == period_end
            )
        )

        if endpoint:
            query = query.where(APIUsageRecord.endpoint == endpoint)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_or_create_usage_record(
        self,
        api_name: APIName,
        endpoint: Optional[str],
        period_start: datetime,
        period_end: datetime
    ) -> APIUsageRecord:
        """Get or create usage record.

        Args:
            api_name: Name of the API
            endpoint: Optional endpoint
            period_start: Period start time
            period_end: Period end time

        Returns:
            APIUsageRecord
        """
        record = await self._get_usage_record(api_name, endpoint, period_start, period_end)

        if not record:
            quota_config = API_QUOTAS.get(api_name)
            record = APIUsageRecord(
                api_name=api_name.value,
                endpoint=endpoint,
                request_count=0,
                quota_limit=quota_config['limit'] if quota_config else 0,
                period_start=period_start,
                period_end=period_end,
                cost_per_call=quota_config['cost_per_call'] if quota_config else Decimal('0.0'),
                total_cost=Decimal('0.0')
            )
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)

        return record

    def _get_threshold_status(self, usage_percentage: float) -> str:
        """Get threshold status based on usage percentage.

        Args:
            usage_percentage: Current usage percentage

        Returns:
            Status string
        """
        if usage_percentage >= 100:
            return "EXCEEDED"
        elif usage_percentage >= 90:
            return "CRITICAL"
        elif usage_percentage >= 80:
            return "WARNING"
        else:
            return "NORMAL"


async def get_usage_tracker(db: AsyncSession) -> APIUsageTracker:
    """Get usage tracker instance.

    Args:
        db: Database session

    Returns:
        APIUsageTracker instance
    """
    return APIUsageTracker(db)
