"""WhoAPI Service Adapter.

This module provides a service adapter for the WhoAPI service, which offers
domain WHOIS data, SSL certificate information, DNS records, and domain
availability checking.

API Documentation: https://whoapi.com/documentation/api
"""
import asyncio
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, TypeVar, Union

import httpx
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import cache
from src.models.external_api import WhoisRecord
from src.repositories.whoapi_repository import WhoAPIRepository

logger = logging.getLogger(__name__)

# Type variable for generic typing
T = TypeVar("T", bound=BaseModel)

# Cache TTL settings (in seconds)
WHOIS_CACHE_TTL = 86400  # 24 hours - WHOIS data changes infrequently
SSL_CACHE_TTL = 43200  # 12 hours
DNS_CACHE_TTL = 3600  # 1 hour
TECH_CACHE_TTL = 86400  # 24 hours


class WhoAPIError(Exception):
    """Base exception for WhoAPI-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class RateLimitError(WhoAPIError):
    """Raised when API rate limit is exceeded."""

    pass


class DomainNotFoundError(WhoAPIError):
    """Raised when domain is not found."""

    pass


class WhoisData(BaseModel):
    """Pydantic model for WHOIS response data."""

    domain_name: str = Field(..., description="The domain name")
    registrar: Optional[str] = Field(None, description="Domain registrar")
    registration_date: Optional[datetime] = Field(
        None, description="Domain registration date"
    )
    expiration_date: Optional[datetime] = Field(
        None, description="Domain expiration date"
    )
    updated_date: Optional[datetime] = Field(
        None, description="Last WHOIS update date"
    )
    nameservers: List[str] = Field(
        default_factory=list, description="List of nameservers"
    )
    status: List[str] = Field(
        default_factory=list, description="Domain status codes"
    )
    dnssec: Optional[bool] = Field(None, description="DNSSEC status")
    registrant_name: Optional[str] = Field(
        None, description="Registrant name"
    )
    registrant_org: Optional[str] = Field(
        None, description="Registrant organization"
    )
    registrant_country: Optional[str] = Field(
        None, description="Registrant country code"
    )
    registrant_email: Optional[str] = Field(
        None, description="Registrant email (if available)"
    )
    admin_email: Optional[str] = Field(
        None, description="Admin contact email"
    )
    tech_email: Optional[str] = Field(
        None, description="Tech contact email"
    )
    raw_whois: Optional[str] = Field(
        None, description="Raw WHOIS response"
    )

    class Config:
        """Pydantic config."""

        extra = "ignore"


class SSLInfo(BaseModel):
    """Pydantic model for SSL certificate information."""

    domain: str = Field(..., description="Domain name")
    valid: bool = Field(..., description="Whether SSL is valid")
    issuer: Optional[str] = Field(None, description="Certificate issuer")
    issued_date: Optional[datetime] = Field(
        None, description="Certificate issue date"
    )
    expiry_date: Optional[datetime] = Field(
        None, description="Certificate expiry date"
    )
    days_until_expiry: Optional[int] = Field(
        None, description="Days until certificate expires"
    )
    subject: Optional[str] = Field(
        None, description="Certificate subject"
    )
    san: List[str] = Field(
        default_factory=list,
        description="Subject Alternative Names",
    )
    fingerprint: Optional[str] = Field(
        None, description="Certificate fingerprint"
    )
    serial_number: Optional[str] = Field(
        None, description="Certificate serial number"
    )
    signature_algorithm: Optional[str] = Field(
        None, description="Signature algorithm"
    )
    protocol_version: Optional[str] = Field(
        None, description="TLS/SSL protocol version"
    )

    class Config:
        """Pydantic config."""

        extra = "ignore"


class DNSRecord(BaseModel):
    """Pydantic model for DNS record."""

    type: str = Field(..., description="Record type (A, AAAA, MX, etc.)")
    name: str = Field(..., description="Record name")
    value: str = Field(..., description="Record value")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")
    priority: Optional[int] = Field(
        None, description="Priority (for MX records)"
    )

    class Config:
        """Pydantic config."""

        extra = "ignore"


class DNSInfo(BaseModel):
    """Pydantic model for DNS information."""

    domain: str = Field(..., description="Domain name")
    records: List[DNSRecord] = Field(
        default_factory=list, description="List of DNS records"
    )
    a_records: List[str] = Field(
        default_factory=list, description="A record IPs"
    )
    aaaa_records: List[str] = Field(
        default_factory=list, description="AAAA record IPs"
    )
    mx_records: List[Dict[str, Any]] = Field(
        default_factory=list, description="MX records"
    )
    ns_records: List[str] = Field(
        default_factory=list, description="NS records"
    )
    txt_records: List[str] = Field(
        default_factory=list, description="TXT records"
    )
    cname_records: List[str] = Field(
        default_factory=list, description="CNAME records"
    )

    class Config:
        """Pydantic config."""

        extra = "ignore"


class TechStackInfo(BaseModel):
    """Pydantic model for technology stack detection."""

    domain: str = Field(..., description="Domain name")
    technologies: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detected technologies",
    )
    cms: Optional[str] = Field(
        None, description="Content Management System"
    )
    ecommerce: Optional[str] = Field(
        None, description="E-commerce platform"
    )
    analytics: List[str] = Field(
        default_factory=list, description="Analytics tools"
    )
    frameworks: List[str] = Field(
        default_factory=list, description="Web frameworks"
    )
    cdn: Optional[str] = Field(
        None, description="Content Delivery Network"
    )
    hosting: Optional[str] = Field(None, description="Hosting provider")
    server: Optional[str] = Field(None, description="Web server")
    ssl_provider: Optional[str] = Field(None, description="SSL provider")

    class Config:
        """Pydantic config."""

        extra = "ignore"


class DomainAge(BaseModel):
    """Pydantic model for domain age information."""

    domain: str = Field(..., description="Domain name")
    registration_date: Optional[datetime] = Field(
        None, description="Registration date"
    )
    age_days: Optional[int] = Field(
        None, description="Age in days"
    )
    age_months: Optional[int] = Field(
        None, description="Age in months"
    )
    age_years: Optional[int] = Field(
        None, description="Age in years"
    )
    age_string: Optional[str] = Field(
        None, description="Human-readable age string"
    )

    class Config:
        """Pydantic config."""

        extra = "ignore"


class DomainAvailability(BaseModel):
    """Pydantic model for domain availability check."""

    domain: str = Field(..., description="Domain name")
    available: bool = Field(..., description="Whether domain is available")
    premium: Optional[bool] = Field(
        None, description="Whether it's a premium domain"
    )
    price: Optional[float] = Field(
        None, description="Price if available"
    )
    currency: Optional[str] = Field(None, description="Price currency")

    class Config:
        """Pydantic config."""

        extra = "ignore"


class WhoAPIService:
    """Service adapter for WhoAPI.

    This service provides methods to interact with the WhoAPI for domain
    intelligence including WHOIS lookups, SSL info, DNS records, and more.

    Attributes:
        base_url: WhoAPI base URL
        api_key: WhoAPI API key
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts for failed requests
    """

    BASE_URL = "https://api.whoapi.com"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

    def __init__(
        self,
        api_key: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ):
        """Initialize the WhoAPI service.

        Args:
            api_key: WhoAPI API key. If not provided, reads from WHOAPI_API_KEY env var.
            db: Optional async database session for persistence.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts for failed requests.
        """
        self.api_key = api_key or os.environ.get("WHOAPI_API_KEY", "")
        self.db = db
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None
        self._repository: Optional[WhoAPIRepository] = None

        if db:
            self._repository = WhoAPIRepository(db)

        if not self.api_key:
            logger.warning(
                "WhoAPI API key not configured. Set WHOAPI_API_KEY environment variable."
            )

    async def __aenter__(self) -> "WhoAPIService":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=self.timeout,
            headers={"Accept": "application/json"},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _normalize_domain(self, domain: str) -> str:
        """Normalize a domain name for consistent lookups.

        Args:
            domain: The domain to normalize.

        Returns:
            Normalized domain name (lowercase, no protocol/path).
        """
        # Remove protocol if present
        domain = re.sub(r"^https?://", "", domain.lower().strip())
        # Remove path and query string
        domain = domain.split("/")[0]
        # Remove port if present
        domain = domain.split(":")[0]
        # Remove www prefix for consistency
        domain = re.sub(r"^www\.", "", domain)
        return domain

    async def _make_request(
        self,
        request_type: str,
        domain: str,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the WhoAPI.

        Args:
            request_type: The type of request (e.g., 'whois', 'ssl', 'dns').
            domain: The domain to query.
            extra_params: Additional query parameters.

        Returns:
            JSON response from the API.

        Raises:
            WhoAPIError: If the request fails.
            RateLimitError: If rate limit is exceeded.
        """
        if not self.api_key:
            raise WhoAPIError("WhoAPI API key not configured")

        params = {
            "apikey": self.api_key,
            "r": request_type,
            "domain": self._normalize_domain(domain),
        }
        if extra_params:
            params.update(extra_params)

        # Ensure we have a client
        client = self._client
        if not client:
            client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
            )

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                response = await client.get("/", params=params)

                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(
                        response.headers.get("Retry-After", 60)
                    )
                    raise RateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after}s",
                        status_code=429,
                        details={"retry_after": retry_after},
                    )

                response.raise_for_status()
                data = response.json()

                # Check for API-level errors
                if data.get("status") == 0:
                    error_code = data.get("status_desc", "Unknown error")
                    raise WhoAPIError(
                        f"WhoAPI error: {error_code}",
                        error_code=data.get("status"),
                        details=data,
                    )

                return data

            except httpx.TimeoutException as e:
                last_error = WhoAPIError(
                    f"Request timed out: {str(e)}",
                    details={"attempt": attempt + 1},
                )
                logger.warning(
                    f"WhoAPI request timed out (attempt {attempt + 1}/{self.max_retries})"
                )

            except httpx.HTTPStatusError as e:
                last_error = WhoAPIError(
                    f"HTTP error: {e.response.status_code}",
                    status_code=e.response.status_code,
                    details={"response": str(e)},
                )
                logger.error(f"WhoAPI HTTP error: {e}")
                if e.response.status_code < 500:
                    raise last_error

            except RateLimitError:
                raise

            except WhoAPIError:
                raise

            except Exception as e:
                last_error = WhoAPIError(
                    f"Unexpected error: {str(e)}",
                    details={"error_type": type(e).__name__},
                )
                logger.error(f"WhoAPI unexpected error: {e}")

            # Wait before retry
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))

        # Clean up client if we created it
        if not self._client and client:
            await client.aclose()

        raise last_error or WhoAPIError("Request failed after all retries")

    async def get_whois_info(self, domain: str) -> WhoisData:
        """Get WHOIS information for a domain.

        Args:
            domain: The domain to look up.

        Returns:
            WhoisData object with WHOIS information.

        Raises:
            WhoAPIError: If the request fails.
        """
        normalized_domain = self._normalize_domain(domain)
        cache_key = f"whoapi:whois:{normalized_domain}"

        # Try cache first
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for WHOIS: {normalized_domain}")
            return WhoisData(**cached)

        logger.info(f"Fetching WHOIS for: {normalized_domain}")
        data = await self._make_request("whois", domain)

        # Parse dates
        def parse_date(date_str: Optional[str]) -> Optional[datetime]:
            if not date_str:
                return None
            try:
                # Try multiple date formats
                for fmt in [
                    "%Y-%m-%d",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%d %H:%M:%S",
                    "%d-%b-%Y",
                ]:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
                return None
            except Exception:
                return None

        whois_data = WhoisData(
            domain_name=normalized_domain,
            registrar=data.get("registrar_name") or data.get("registrar"),
            registration_date=parse_date(
                data.get("date_created") or data.get("creation_date")
            ),
            expiration_date=parse_date(
                data.get("date_expires") or data.get("expiration_date")
            ),
            updated_date=parse_date(
                data.get("date_updated") or data.get("updated_date")
            ),
            nameservers=data.get("nameservers", []) or [],
            status=data.get("status", []) or [],
            dnssec=(
                data.get("dnssec", "").lower() == "yes"
                if data.get("dnssec")
                else None
            ),
            registrant_name=data.get("registrant_name"),
            registrant_org=data.get("registrant_org")
            or data.get("registrant_organization"),
            registrant_country=data.get("registrant_country"),
            registrant_email=data.get("registrant_email"),
            admin_email=data.get("admin_email"),
            tech_email=data.get("tech_email"),
            raw_whois=data.get("rawdata") or data.get("raw_whois"),
        )

        # Cache the result
        cache.set(cache_key, whois_data.dict(), ttl=WHOIS_CACHE_TTL)

        # Store in database if repository is available
        if self._repository:
            try:
                record = WhoisRecord(
                    domain_name=normalized_domain,
                    registrar=whois_data.registrar,
                    registration_date=whois_data.registration_date,
                    expiration_date=whois_data.expiration_date,
                    nameservers=whois_data.nameservers,
                    status=whois_data.status,
                    dnssec=whois_data.dnssec,
                    registrant_name=whois_data.registrant_name,
                    registrant_org=whois_data.registrant_org,
                    registrant_country=whois_data.registrant_country,
                )
                await self._repository.create_or_update(record)
            except Exception as e:
                logger.error(f"Failed to store WHOIS record: {e}")

        return whois_data

    async def get_domain_age(self, domain: str) -> DomainAge:
        """Calculate domain age from WHOIS data.

        Args:
            domain: The domain to check.

        Returns:
            DomainAge object with age information.
        """
        whois_data = await self.get_whois_info(domain)
        normalized_domain = self._normalize_domain(domain)

        age_days: Optional[int] = None
        age_months: Optional[int] = None
        age_years: Optional[int] = None
        age_string: Optional[str] = None

        if whois_data.registration_date:
            delta = datetime.now(timezone.utc) - whois_data.registration_date.replace(tzinfo=timezone.utc)
            age_days = delta.days
            age_months = age_days // 30
            age_years = age_days // 365

            # Create human-readable string
            if age_years > 0:
                age_string = f"{age_years} year(s), {age_months % 12} month(s)"
            elif age_months > 0:
                age_string = f"{age_months} month(s), {age_days % 30} day(s)"
            else:
                age_string = f"{age_days} day(s)"

        return DomainAge(
            domain=normalized_domain,
            registration_date=whois_data.registration_date,
            age_days=age_days,
            age_months=age_months,
            age_years=age_years,
            age_string=age_string,
        )

    async def get_ssl_info(self, domain: str) -> SSLInfo:
        """Get SSL certificate information for a domain.

        Args:
            domain: The domain to check.

        Returns:
            SSLInfo object with certificate details.
        """
        normalized_domain = self._normalize_domain(domain)
        cache_key = f"whoapi:ssl:{normalized_domain}"

        # Try cache first
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for SSL: {normalized_domain}")
            return SSLInfo(**cached)

        logger.info(f"Fetching SSL info for: {normalized_domain}")
        data = await self._make_request("sslcert", domain)

        # Parse dates
        def parse_date(date_str: Optional[str]) -> Optional[datetime]:
            if not date_str:
                return None
            try:
                for fmt in [
                    "%Y-%m-%d",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%d %H:%M:%S",
                    "%b %d %H:%M:%S %Y GMT",
                ]:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
                return None
            except Exception:
                return None

        expiry_date = parse_date(
            data.get("date_expire") or data.get("not_after")
        )
        days_until_expiry = None
        if expiry_date:
            days_until_expiry = (expiry_date.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).days

        ssl_info = SSLInfo(
            domain=normalized_domain,
            valid=data.get("valid", False),
            issuer=data.get("issuer") or data.get("issuer_cn"),
            issued_date=parse_date(
                data.get("date_issue") or data.get("not_before")
            ),
            expiry_date=expiry_date,
            days_until_expiry=days_until_expiry,
            subject=data.get("subject") or data.get("subject_cn"),
            san=data.get("san", []) or [],
            fingerprint=data.get("fingerprint") or data.get("fingerprint_sha256"),
            serial_number=data.get("serial_number"),
            signature_algorithm=data.get("signature_algorithm"),
            protocol_version=data.get("protocol_version") or data.get("ssl_version"),
        )

        # Cache the result
        cache.set(cache_key, ssl_info.dict(), ttl=SSL_CACHE_TTL)

        return ssl_info

    async def get_dns_records(self, domain: str) -> DNSInfo:
        """Get DNS records for a domain.

        Args:
            domain: The domain to check.

        Returns:
            DNSInfo object with DNS records.
        """
        normalized_domain = self._normalize_domain(domain)
        cache_key = f"whoapi:dns:{normalized_domain}"

        # Try cache first
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for DNS: {normalized_domain}")
            return DNSInfo(**cached)

        logger.info(f"Fetching DNS records for: {normalized_domain}")
        data = await self._make_request("dns", domain)

        records: List[DNSRecord] = []
        a_records: List[str] = []
        aaaa_records: List[str] = []
        mx_records: List[Dict[str, Any]] = []
        ns_records: List[str] = []
        txt_records: List[str] = []
        cname_records: List[str] = []

        # Parse DNS records from response
        for record_type in ["a", "aaaa", "mx", "ns", "txt", "cname"]:
            type_records = data.get(record_type, []) or []
            if isinstance(type_records, list):
                for rec in type_records:
                    if isinstance(rec, dict):
                        value = rec.get("data") or rec.get("target") or ""
                        priority = rec.get("priority")
                        ttl = rec.get("ttl")
                    else:
                        value = str(rec)
                        priority = None
                        ttl = None

                    records.append(
                        DNSRecord(
                            type=record_type.upper(),
                            name=normalized_domain,
                            value=value,
                            ttl=ttl,
                            priority=priority,
                        )
                    )

                    if record_type == "a":
                        a_records.append(value)
                    elif record_type == "aaaa":
                        aaaa_records.append(value)
                    elif record_type == "mx":
                        mx_records.append({"priority": priority, "target": value})
                    elif record_type == "ns":
                        ns_records.append(value)
                    elif record_type == "txt":
                        txt_records.append(value)
                    elif record_type == "cname":
                        cname_records.append(value)

        dns_info = DNSInfo(
            domain=normalized_domain,
            records=records,
            a_records=a_records,
            aaaa_records=aaaa_records,
            mx_records=mx_records,
            ns_records=ns_records,
            txt_records=txt_records,
            cname_records=cname_records,
        )

        # Cache the result
        cache.set(cache_key, dns_info.dict(), ttl=DNS_CACHE_TTL)

        return dns_info

    async def analyze_tech_stack(self, domain: str) -> TechStackInfo:
        """Detect technologies used by a domain.

        Args:
            domain: The domain to analyze.

        Returns:
            TechStackInfo object with detected technologies.
        """
        normalized_domain = self._normalize_domain(domain)
        cache_key = f"whoapi:tech:{normalized_domain}"

        # Try cache first
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for tech stack: {normalized_domain}")
            return TechStackInfo(**cached)

        logger.info(f"Analyzing tech stack for: {normalized_domain}")
        data = await self._make_request("tech", domain)

        technologies: List[Dict[str, Any]] = []
        analytics: List[str] = []
        frameworks: List[str] = []

        # Parse technology data
        tech_list = data.get("technologies", []) or data.get("tech", []) or []
        for tech in tech_list:
            if isinstance(tech, dict):
                technologies.append(tech)
                category = tech.get("category", "").lower()
                name = tech.get("name", "")
                if "analytics" in category:
                    analytics.append(name)
                elif "framework" in category:
                    frameworks.append(name)
            else:
                technologies.append({"name": str(tech)})

        tech_info = TechStackInfo(
            domain=normalized_domain,
            technologies=technologies,
            cms=data.get("cms") or data.get("content_management_system"),
            ecommerce=data.get("ecommerce") or data.get("ecommerce_platform"),
            analytics=analytics,
            frameworks=frameworks,
            cdn=data.get("cdn") or data.get("content_delivery_network"),
            hosting=data.get("hosting") or data.get("hosting_provider"),
            server=data.get("server") or data.get("web_server"),
            ssl_provider=data.get("ssl_provider"),
        )

        # Cache the result
        cache.set(cache_key, tech_info.dict(), ttl=TECH_CACHE_TTL)

        return tech_info

    async def check_domain_availability(
        self, domain: str
    ) -> DomainAvailability:
        """Check if a domain is available for registration.

        Args:
            domain: The domain to check.

        Returns:
            DomainAvailability object with availability status.
        """
        normalized_domain = self._normalize_domain(domain)
        logger.info(f"Checking availability for: {normalized_domain}")

        data = await self._make_request("taken", domain)

        available = data.get("taken") == 0 or data.get("available") is True

        return DomainAvailability(
            domain=normalized_domain,
            available=available,
            premium=data.get("premium"),
            price=data.get("price"),
            currency=data.get("currency"),
        )

    async def get_expiring_domains(
        self, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get domains expiring within the specified number of days.

        This method queries the database for stored WHOIS records with
        expiration dates within the specified window.

        Args:
            days: Number of days to look ahead for expiring domains.

        Returns:
            List of expiring domain records.
        """
        if not self._repository:
            logger.warning(
                "Database not available for expiring domains query"
            )
            return []

        logger.info(f"Fetching domains expiring within {days} days")

        try:
            expiring_records = await self._repository.get_expiring_domains(
                days_until_expiry=days
            )

            return [
                {
                    "domain": record.domain_name,
                    "expiration_date": (
                        record.expiration_date.isoformat()
                        if record.expiration_date
                        else None
                    ),
                    "days_until_expiry": (
                        (record.expiration_date.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).days
                        if record.expiration_date
                        else None
                    ),
                    "registrar": record.registrar,
                    "registrant_org": record.registrant_org,
                }
                for record in expiring_records
            ]
        except Exception as e:
            logger.error(f"Error fetching expiring domains: {e}")
            return []

    async def test_connection(self) -> bool:
        """Test the API connection.

        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            # Use a well-known domain for testing
            await self._make_request("whois", "google.com")
            return True
        except Exception as e:
            logger.error(f"WhoAPI connection test failed: {e}")
            return False

    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status.

        Note: WhoAPI doesn't provide explicit rate limit headers,
        so this returns estimated usage based on plan limits.

        Returns:
            Dictionary with rate limit information.
        """
        # WhoAPI typically has monthly quotas rather than per-minute limits
        return {
            "api_name": "whoapi",
            "status": "active" if self.api_key else "not_configured",
            "note": "WhoAPI uses monthly quotas. Check your account dashboard for usage.",
        }
