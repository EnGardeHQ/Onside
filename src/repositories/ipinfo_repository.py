"""IPInfo Repository Module.

This module provides database operations for IPInfo record entities.
Handles storage, retrieval, and management of IP geolocation data
from the IPInfo API.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import select, delete, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.external_api import IPInfoRecord


class IPInfoRepository:
    """Repository for IPInfo record database operations.

    Provides methods for storing and retrieving IP geolocation data
    fetched from the IPInfo API for domain infrastructure analysis.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def create(self, ip_info: IPInfoRecord) -> IPInfoRecord:
        """Create a new IP info record.

        Args:
            ip_info: IPInfoRecord instance to store

        Returns:
            Created IPInfoRecord with populated ID
        """
        self.db.add(ip_info)
        await self.db.commit()
        await self.db.refresh(ip_info)
        return ip_info

    async def create_or_update(self, ip_info: IPInfoRecord) -> IPInfoRecord:
        """Create or update an IP info record (upsert).

        If a record with the same IP address exists, update it.
        Otherwise, create a new record.

        Args:
            ip_info: IPInfoRecord instance to create or update

        Returns:
            Created or updated IPInfoRecord
        """
        existing = await self.get_by_ip(ip_info.ip_address)

        if existing:
            # Update existing record
            existing.hostname = ip_info.hostname
            existing.city = ip_info.city
            existing.region = ip_info.region
            existing.country = ip_info.country
            existing.location = ip_info.location
            existing.organization = ip_info.organization
            existing.postal = ip_info.postal
            existing.timezone = ip_info.timezone
            existing.domain_id = ip_info.domain_id

            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new record
            self.db.add(ip_info)
            await self.db.commit()
            await self.db.refresh(ip_info)
            return ip_info

    async def get_by_id(self, record_id: int) -> Optional[IPInfoRecord]:
        """Get an IP info record by its database ID.

        Args:
            record_id: Database ID of the record

        Returns:
            IPInfoRecord if found, None otherwise
        """
        result = await self.db.execute(
            select(IPInfoRecord).where(IPInfoRecord.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_by_ip(self, ip_address: str) -> Optional[IPInfoRecord]:
        """Get an IP info record by IP address.

        Args:
            ip_address: IP address to look up

        Returns:
            IPInfoRecord if found, None otherwise
        """
        result = await self.db.execute(
            select(IPInfoRecord).where(IPInfoRecord.ip_address == ip_address)
        )
        return result.scalar_one_or_none()

    async def get_by_domain(self, domain_id: int) -> List[IPInfoRecord]:
        """Get all IP info records associated with a domain.

        Args:
            domain_id: ID of the domain

        Returns:
            List of IPInfoRecord instances for the domain
        """
        result = await self.db.execute(
            select(IPInfoRecord)
            .where(IPInfoRecord.domain_id == domain_id)
            .order_by(IPInfoRecord.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_country(
        self,
        country_code: str,
        limit: int = 100
    ) -> List[IPInfoRecord]:
        """Get IP info records by country code.

        Args:
            country_code: ISO 3166-1 alpha-2 country code
            limit: Maximum number of records to return

        Returns:
            List of IPInfoRecord instances from the country
        """
        result = await self.db.execute(
            select(IPInfoRecord)
            .where(IPInfoRecord.country == country_code.upper())
            .order_by(IPInfoRecord.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_stale_records(self, days_old: int) -> int:
        """Delete IP info records older than the specified number of days.

        Args:
            days_old: Delete records older than this many days

        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        result = await self.db.execute(
            delete(IPInfoRecord).where(
                IPInfoRecord.updated_at < cutoff_date
            )
        )
        await self.db.commit()

        return result.rowcount

    async def delete_by_id(self, record_id: int) -> bool:
        """Delete an IP info record by its database ID.

        Args:
            record_id: Database ID of the record to delete

        Returns:
            True if record was deleted, False if not found
        """
        result = await self.db.execute(
            delete(IPInfoRecord).where(IPInfoRecord.id == record_id)
        )
        await self.db.commit()

        return result.rowcount > 0

    async def delete_by_ip(self, ip_address: str) -> bool:
        """Delete an IP info record by IP address.

        Args:
            ip_address: IP address of the record to delete

        Returns:
            True if record was deleted, False if not found
        """
        result = await self.db.execute(
            delete(IPInfoRecord).where(IPInfoRecord.ip_address == ip_address)
        )
        await self.db.commit()

        return result.rowcount > 0

    async def get_by_organization(
        self,
        organization: str,
        limit: int = 100
    ) -> List[IPInfoRecord]:
        """Get IP info records by organization/ISP name.

        Args:
            organization: Organization or ISP name to search
            limit: Maximum number of records to return

        Returns:
            List of IPInfoRecord instances from the organization
        """
        result = await self.db.execute(
            select(IPInfoRecord)
            .where(IPInfoRecord.organization.ilike(f"%{organization}%"))
            .order_by(IPInfoRecord.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_country(self) -> Dict[str, int]:
        """Count IP info records grouped by country.

        Returns:
            Dictionary mapping country codes to record counts
        """
        from sqlalchemy import func

        result = await self.db.execute(
            select(
                IPInfoRecord.country,
                func.count(IPInfoRecord.id).label("count")
            )
            .where(IPInfoRecord.country.isnot(None))
            .group_by(IPInfoRecord.country)
            .order_by(func.count(IPInfoRecord.id).desc())
        )

        return {row.country: row.count for row in result.all()}

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[IPInfoRecord]:
        """Get all IP info records with pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of IPInfoRecord instances
        """
        result = await self.db.execute(
            select(IPInfoRecord)
            .order_by(IPInfoRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
