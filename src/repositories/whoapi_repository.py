"""WhoAPI Repository Module.

This module provides database operations for WHOIS record entities.
Handles storage, retrieval, and management of domain WHOIS data
from the WhoAPI service.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.external_api import WhoisRecord


class WhoAPIRepository:
    """Repository for WHOIS record database operations.

    Provides methods for storing and retrieving domain WHOIS data
    fetched from the WhoAPI service for domain intelligence.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def create(self, whois: WhoisRecord) -> WhoisRecord:
        """Create a new WHOIS record.

        Args:
            whois: WhoisRecord instance to store

        Returns:
            Created WhoisRecord with populated ID
        """
        self.db.add(whois)
        await self.db.commit()
        await self.db.refresh(whois)
        return whois

    async def create_or_update(self, whois: WhoisRecord) -> WhoisRecord:
        """Create or update a WHOIS record (upsert).

        If a record with the same domain name exists, update it.
        Otherwise, create a new record.

        Args:
            whois: WhoisRecord instance to create or update

        Returns:
            Created or updated WhoisRecord
        """
        existing = await self.get_by_domain(whois.domain_name)

        if existing:
            # Update existing record
            existing.registrar = whois.registrar
            existing.registration_date = whois.registration_date
            existing.expiration_date = whois.expiration_date
            existing.nameservers = whois.nameservers
            existing.status = whois.status
            existing.dnssec = whois.dnssec
            existing.registrant_name = whois.registrant_name
            existing.registrant_org = whois.registrant_org
            existing.registrant_country = whois.registrant_country
            existing.domain_id = whois.domain_id

            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new record
            self.db.add(whois)
            await self.db.commit()
            await self.db.refresh(whois)
            return whois

    async def get_by_id(self, record_id: int) -> Optional[WhoisRecord]:
        """Get a WHOIS record by its database ID.

        Args:
            record_id: Database ID of the record

        Returns:
            WhoisRecord if found, None otherwise
        """
        result = await self.db.execute(
            select(WhoisRecord).where(WhoisRecord.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_by_domain(self, domain_name: str) -> Optional[WhoisRecord]:
        """Get a WHOIS record by domain name.

        Args:
            domain_name: Domain name to look up

        Returns:
            WhoisRecord if found, None otherwise
        """
        result = await self.db.execute(
            select(WhoisRecord).where(
                WhoisRecord.domain_name == domain_name.lower()
            )
        )
        return result.scalar_one_or_none()

    async def get_by_domain_id(self, domain_id: int) -> Optional[WhoisRecord]:
        """Get a WHOIS record by the associated domain ID.

        Args:
            domain_id: ID of the associated domain record

        Returns:
            WhoisRecord if found, None otherwise
        """
        result = await self.db.execute(
            select(WhoisRecord)
            .where(WhoisRecord.domain_id == domain_id)
            .order_by(WhoisRecord.updated_at.desc())
        )
        return result.scalar_one_or_none()

    async def get_expiring_domains(
        self,
        days_until_expiry: int
    ) -> List[WhoisRecord]:
        """Get WHOIS records for domains expiring within specified days.

        Args:
            days_until_expiry: Number of days until expiration threshold

        Returns:
            List of WhoisRecord instances for expiring domains
        """
        expiry_threshold = datetime.utcnow() + timedelta(days=days_until_expiry)

        result = await self.db.execute(
            select(WhoisRecord)
            .where(
                and_(
                    WhoisRecord.expiration_date.isnot(None),
                    WhoisRecord.expiration_date <= expiry_threshold,
                    WhoisRecord.expiration_date > datetime.utcnow()
                )
            )
            .order_by(WhoisRecord.expiration_date.asc())
        )
        return list(result.scalars().all())

    async def get_by_registrar(
        self,
        registrar: str,
        limit: int = 100
    ) -> List[WhoisRecord]:
        """Get WHOIS records by registrar name.

        Args:
            registrar: Registrar name to search (partial match)
            limit: Maximum number of records to return

        Returns:
            List of WhoisRecord instances from the registrar
        """
        result = await self.db.execute(
            select(WhoisRecord)
            .where(WhoisRecord.registrar.ilike(f"%{registrar}%"))
            .order_by(WhoisRecord.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_stale_records(self, days_old: int) -> int:
        """Delete WHOIS records older than the specified number of days.

        Args:
            days_old: Delete records older than this many days

        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        result = await self.db.execute(
            delete(WhoisRecord).where(
                WhoisRecord.updated_at < cutoff_date
            )
        )
        await self.db.commit()

        return result.rowcount

    async def delete_by_id(self, record_id: int) -> bool:
        """Delete a WHOIS record by its database ID.

        Args:
            record_id: Database ID of the record to delete

        Returns:
            True if record was deleted, False if not found
        """
        result = await self.db.execute(
            delete(WhoisRecord).where(WhoisRecord.id == record_id)
        )
        await self.db.commit()

        return result.rowcount > 0

    async def delete_by_domain(self, domain_name: str) -> bool:
        """Delete a WHOIS record by domain name.

        Args:
            domain_name: Domain name of the record to delete

        Returns:
            True if record was deleted, False if not found
        """
        result = await self.db.execute(
            delete(WhoisRecord).where(
                WhoisRecord.domain_name == domain_name.lower()
            )
        )
        await self.db.commit()

        return result.rowcount > 0

    async def get_recently_updated(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[WhoisRecord]:
        """Get recently updated WHOIS records.

        Args:
            days: Number of days to look back
            limit: Maximum number of records to return

        Returns:
            List of recently updated WhoisRecord instances
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(WhoisRecord)
            .where(WhoisRecord.updated_at >= cutoff_date)
            .order_by(WhoisRecord.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_expired_domains(self, limit: int = 100) -> List[WhoisRecord]:
        """Get WHOIS records for expired domains.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of WhoisRecord instances for expired domains
        """
        result = await self.db.execute(
            select(WhoisRecord)
            .where(
                and_(
                    WhoisRecord.expiration_date.isnot(None),
                    WhoisRecord.expiration_date < datetime.utcnow()
                )
            )
            .order_by(WhoisRecord.expiration_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_registrar(self) -> Dict[str, int]:
        """Count WHOIS records grouped by registrar.

        Returns:
            Dictionary mapping registrar names to record counts
        """
        from sqlalchemy import func

        result = await self.db.execute(
            select(
                WhoisRecord.registrar,
                func.count(WhoisRecord.id).label("count")
            )
            .where(WhoisRecord.registrar.isnot(None))
            .group_by(WhoisRecord.registrar)
            .order_by(func.count(WhoisRecord.id).desc())
        )

        return {row.registrar: row.count for row in result.all()}

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[WhoisRecord]:
        """Get all WHOIS records with pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of WhoisRecord instances
        """
        result = await self.db.execute(
            select(WhoisRecord)
            .order_by(WhoisRecord.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
