"""External API data models for OnSide application.

This module contains SQLAlchemy models for storing data retrieved from external APIs:
- GNews API: News articles data
- IPInfo API: IP/Domain geolocation data
- WhoAPI API: Domain WHOIS data
- API Usage Tracking: Track API calls and quotas
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, JSON,
    ForeignKey, Boolean, Numeric, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from src.database import Base

# Handle circular imports
if TYPE_CHECKING:
    from .competitor import Competitor
    from .domain import Domain


class GNewsArticle(Base):
    """Model for storing news articles from GNews API.

    Stores news article data retrieved from GNews API for competitor monitoring
    and market intelligence purposes.

    Attributes:
        id: Primary key
        article_id: Unique identifier from GNews API
        title: Article headline
        description: Short article description/summary
        content: Full article content (if available)
        url: Link to the original article
        image_url: URL to article's featured image
        published_at: When the article was published
        source_name: Name of the news source
        source_url: URL of the news source
        query_term: Search term used to find this article
        language: Language code of the article
        country: Country code for the article
        competitor_id: FK to associated competitor
        created_at: When the record was created
        updated_at: When the record was last updated
    """
    __tablename__ = "gnews_articles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    article_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    query_term: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Foreign keys
    competitor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competitors.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )

    # Relationships
    competitor: Mapped[Optional["Competitor"]] = relationship(
        "Competitor",
        foreign_keys=[competitor_id],
        lazy="select"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_gnews_articles_competitor_published', 'competitor_id', 'published_at'),
        Index('ix_gnews_articles_query_published', 'query_term', 'published_at'),
    )

    def __repr__(self) -> str:
        return f"<GNewsArticle(id={self.id}, title='{self.title[:50]}...', source='{self.source_name}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert article to dictionary.

        Returns:
            Dict containing article attributes
        """
        return {
            "id": self.id,
            "article_id": self.article_id,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "url": self.url,
            "image_url": self.image_url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "query_term": self.query_term,
            "language": self.language,
            "country": self.country,
            "competitor_id": self.competitor_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class IPInfoRecord(Base):
    """Model for storing IP/domain geolocation data from IPInfo API.

    Stores geolocation and organization information for IP addresses
    associated with domains for competitive intelligence.

    Attributes:
        id: Primary key
        ip_address: The IP address
        hostname: Reverse DNS hostname
        city: City location
        region: State/region location
        country: Country code (ISO 3166-1 alpha-2)
        location: Latitude/Longitude as JSON {"lat": float, "lng": float}
        organization: Organization/ISP name
        postal: Postal/ZIP code
        timezone: Timezone identifier
        domain_id: FK to associated domain
        created_at: When the record was created
        updated_at: When the record was last updated
    """
    __tablename__ = "ipinfo_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, index=True)  # IPv6 max length
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True, index=True)
    location: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)  # {"lat": float, "lng": float}
    organization: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    postal: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Foreign keys
    domain_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("domains.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )

    # Relationships
    domain: Mapped[Optional["Domain"]] = relationship(
        "Domain",
        foreign_keys=[domain_id],
        lazy="select"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_ipinfo_records_domain_created', 'domain_id', 'created_at'),
        Index('ix_ipinfo_records_ip_domain', 'ip_address', 'domain_id', unique=True),
    )

    def __repr__(self) -> str:
        return f"<IPInfoRecord(id={self.id}, ip='{self.ip_address}', country='{self.country}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert IP info record to dictionary.

        Returns:
            Dict containing IP info attributes
        """
        return {
            "id": self.id,
            "ip_address": self.ip_address,
            "hostname": self.hostname,
            "city": self.city,
            "region": self.region,
            "country": self.country,
            "location": self.location,
            "organization": self.organization,
            "postal": self.postal,
            "timezone": self.timezone,
            "domain_id": self.domain_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WhoisRecord(Base):
    """Model for storing domain WHOIS data from WhoAPI.

    Stores WHOIS registration information for domains to track
    ownership changes and domain intelligence.

    Attributes:
        id: Primary key
        domain_name: The domain name
        registrar: Domain registrar name
        registration_date: When the domain was first registered
        expiration_date: When the domain registration expires
        nameservers: List of nameservers as JSON array
        status: Domain status codes as JSON array
        dnssec: Whether DNSSEC is enabled
        registrant_name: Name of the domain registrant
        registrant_org: Organization of the domain registrant
        registrant_country: Country of the domain registrant
        domain_id: FK to associated domain
        created_at: When the record was created
        updated_at: When the record was last updated
    """
    __tablename__ = "whois_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    domain_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    registrar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    registration_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    expiration_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    nameservers: Mapped[Optional[List]] = mapped_column(JSON, nullable=True)  # ["ns1.example.com", ...]
    status: Mapped[Optional[List]] = mapped_column(JSON, nullable=True)  # ["clientTransferProhibited", ...]
    dnssec: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    registrant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    registrant_org: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    registrant_country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)

    # Foreign keys
    domain_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("domains.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )

    # Relationships
    domain: Mapped[Optional["Domain"]] = relationship(
        "Domain",
        foreign_keys=[domain_id],
        lazy="select"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_whois_records_domain_updated', 'domain_id', 'updated_at'),
        Index('ix_whois_records_expiration', 'expiration_date'),
    )

    def __repr__(self) -> str:
        return f"<WhoisRecord(id={self.id}, domain='{self.domain_name}', registrar='{self.registrar}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert WHOIS record to dictionary.

        Returns:
            Dict containing WHOIS attributes
        """
        return {
            "id": self.id,
            "domain_name": self.domain_name,
            "registrar": self.registrar,
            "registration_date": self.registration_date.isoformat() if self.registration_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "nameservers": self.nameservers,
            "status": self.status,
            "dnssec": self.dnssec,
            "registrant_name": self.registrant_name,
            "registrant_org": self.registrant_org,
            "registrant_country": self.registrant_country,
            "domain_id": self.domain_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_expiring_soon(self) -> bool:
        """Check if domain expires within 30 days.

        Returns:
            True if domain expires within 30 days, False otherwise
        """
        if not self.expiration_date:
            return False
        days_until_expiration = (self.expiration_date - datetime.now(self.expiration_date.tzinfo)).days
        return 0 < days_until_expiration <= 30


class APIUsageRecord(Base):
    """Model for tracking API calls and quotas.

    Stores API usage metrics to monitor consumption, track costs,
    and manage rate limits across external API integrations.

    Attributes:
        id: Primary key
        api_name: Name of the API (e.g., 'gnews', 'ipinfo', 'whoapi')
        endpoint: Specific API endpoint called
        request_count: Number of requests made in the period
        quota_limit: Maximum allowed requests for the period
        period_start: Start of the tracking period
        period_end: End of the tracking period
        cost_per_call: Cost per API call in USD
        total_cost: Total cost for the period in USD
        created_at: When the record was created
    """
    __tablename__ = "api_usage_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    endpoint: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quota_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    cost_per_call: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 6),
        nullable=True
    )
    total_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 4),
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_api_usage_api_period', 'api_name', 'period_start', 'period_end'),
        Index('ix_api_usage_created', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<APIUsageRecord(id={self.id}, api='{self.api_name}', count={self.request_count})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert API usage record to dictionary.

        Returns:
            Dict containing API usage attributes
        """
        return {
            "id": self.id,
            "api_name": self.api_name,
            "endpoint": self.endpoint,
            "request_count": self.request_count,
            "quota_limit": self.quota_limit,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "cost_per_call": float(self.cost_per_call) if self.cost_per_call else None,
            "total_cost": float(self.total_cost) if self.total_cost else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @property
    def usage_percentage(self) -> Optional[float]:
        """Calculate usage percentage of quota.

        Returns:
            Percentage of quota used, or None if no quota limit
        """
        if not self.quota_limit or self.quota_limit == 0:
            return None
        return (self.request_count / self.quota_limit) * 100

    @property
    def is_quota_exceeded(self) -> bool:
        """Check if quota has been exceeded.

        Returns:
            True if request count exceeds quota limit
        """
        if not self.quota_limit:
            return False
        return self.request_count >= self.quota_limit
