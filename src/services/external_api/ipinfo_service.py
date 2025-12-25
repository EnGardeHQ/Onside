"""IPInfo API Service Adapter.

This module provides a service adapter for the IPInfo API, enabling
IP geolocation lookups for competitive intelligence and domain
infrastructure analysis.
"""
import asyncio
import logging
import os
import socket
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.external_api import IPInfoRecord, APIUsageRecord
from src.repositories.ipinfo_repository import IPInfoRepository

logger = logging.getLogger(__name__)


class IPInfoError(Exception):
    """Base exception for IPInfo API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class RateLimitExceededError(IPInfoError):
    """Raised when API rate limit is exceeded."""
    pass


class IPInfoService:
    """Service adapter for IPInfo API.

    Provides methods for IP geolocation lookups, batch processing,
    domain IP resolution, and geographic distribution analysis.

    Attributes:
        BASE_URL: IPInfo API base URL
        RATE_LIMIT: Maximum requests per period
        RATE_PERIOD_SECONDS: Rate limit period in seconds
        CACHE_TTL_HOURS: Cache time-to-live in hours
    """

    BASE_URL: str = "https://ipinfo.io"
    RATE_LIMIT: int = 50000  # Monthly limit for free tier
    RATE_PERIOD_SECONDS: int = 60
    CACHE_TTL_HOURS: int = 24
    DEFAULT_TIMEOUT: int = 30
    MAX_BATCH_SIZE: int = 1000
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: float = 1.0

    def __init__(
        self,
        db: AsyncSession,
        api_key: Optional[str] = None,
        http_client: Optional[httpx.AsyncClient] = None
    ):
        """Initialize the IPInfo service.

        Args:
            db: Async database session for caching and persistence
            api_key: IPInfo API key (defaults to IPINFO_API_KEY env var)
            http_client: Optional httpx client for connection pooling
        """
        self.db = db
        self.api_key = api_key or os.getenv("IPINFO_API_KEY", "")
        self._client = http_client
        self._client_owner = http_client is None
        self.repository = IPInfoRepository(db)
        self._request_count = 0
        self._period_start = datetime.utcnow()

    async def __aenter__(self) -> "IPInfoService":
        """Async context manager entry."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client_owner and self._client:
            await self._client.aclose()
            self._client = None

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication.

        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting.

        Raises:
            RateLimitExceededError: When rate limit is exceeded
        """
        now = datetime.utcnow()
        if (now - self._period_start).total_seconds() >= self.RATE_PERIOD_SECONDS:
            self._request_count = 0
            self._period_start = now

        if self._request_count >= self.RATE_LIMIT:
            raise RateLimitExceededError(
                "Rate limit exceeded",
                status_code=429,
                details={"retry_after": self.RATE_PERIOD_SECONDS}
            )

        self._request_count += 1

    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the IPInfo API with retry logic.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            params: Query parameters
            data: Request body data

        Returns:
            Parsed JSON response

        Raises:
            IPInfoError: For API errors
            RateLimitExceededError: When rate limit is exceeded
        """
        await self._check_rate_limit()

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT)
            self._client_owner = True

        last_exception: Optional[Exception] = None

        for attempt in range(self.MAX_RETRIES):
            try:
                if method.upper() == "GET":
                    response = await self._client.get(
                        url, headers=headers, params=params
                    )
                elif method.upper() == "POST":
                    response = await self._client.post(
                        url, headers=headers, json=data
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitExceededError(
                        "Rate limit exceeded",
                        status_code=429,
                        details={"retry_after": retry_after}
                    )

                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    raise IPInfoError(
                        error_data.get("error", {}).get("message", "API request failed"),
                        status_code=response.status_code,
                        details=error_data
                    )

                return response.json()

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(
                        self.RETRY_DELAY_SECONDS * (2 ** attempt)
                    )
                continue

            except (RateLimitExceededError, IPInfoError):
                raise

        raise IPInfoError(
            f"Request failed after {self.MAX_RETRIES} retries",
            details={"last_error": str(last_exception)}
        )

    def _parse_location(self, loc: Optional[str]) -> Optional[Dict[str, float]]:
        """Parse location string to lat/lng dictionary.

        Args:
            loc: Location string in "lat,lng" format

        Returns:
            Dictionary with lat and lng keys, or None if parsing fails
        """
        if not loc:
            return None
        try:
            lat, lng = loc.split(",")
            return {"lat": float(lat), "lng": float(lng)}
        except (ValueError, AttributeError):
            return None

    def _api_response_to_record(
        self,
        data: Dict[str, Any],
        domain_id: Optional[int] = None
    ) -> IPInfoRecord:
        """Convert API response to IPInfoRecord model.

        Args:
            data: API response data
            domain_id: Optional domain ID for association

        Returns:
            IPInfoRecord instance
        """
        return IPInfoRecord(
            ip_address=data.get("ip", ""),
            hostname=data.get("hostname"),
            city=data.get("city"),
            region=data.get("region"),
            country=data.get("country"),
            location=self._parse_location(data.get("loc")),
            organization=data.get("org"),
            postal=data.get("postal"),
            timezone=data.get("timezone"),
            domain_id=domain_id
        )

    async def _get_cached_ip_info(
        self,
        ip_address: str
    ) -> Optional[IPInfoRecord]:
        """Get cached IP info if still valid.

        Args:
            ip_address: IP address to look up

        Returns:
            Cached IPInfoRecord if valid, None otherwise
        """
        record = await self.repository.get_by_ip(ip_address)
        if record:
            cache_expiry = datetime.utcnow() - timedelta(hours=self.CACHE_TTL_HOURS)
            if record.created_at and record.created_at > cache_expiry:
                return record
        return None

    async def get_ip_info(
        self,
        ip_address: str,
        use_cache: bool = True,
        domain_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get geolocation info for a single IP address.

        Args:
            ip_address: IP address to look up
            use_cache: Whether to use cached results
            domain_id: Optional domain ID for association

        Returns:
            Dictionary containing IP geolocation data

        Raises:
            IPInfoError: For API errors
            ValueError: For invalid IP addresses
        """
        # Validate IP address format
        try:
            socket.inet_pton(
                socket.AF_INET6 if ":" in ip_address else socket.AF_INET,
                ip_address
            )
        except socket.error as e:
            raise ValueError(f"Invalid IP address format: {ip_address}") from e

        # Check cache first
        if use_cache:
            cached = await self._get_cached_ip_info(ip_address)
            if cached:
                logger.debug(f"Cache hit for IP: {ip_address}")
                return cached.to_dict()

        # Make API request
        logger.info(f"Fetching IP info from API: {ip_address}")
        data = await self._make_request(f"{ip_address}/json")

        # Create and cache the record
        record = self._api_response_to_record(data, domain_id)
        saved_record = await self.repository.create_or_update(record)

        return saved_record.to_dict()

    async def get_batch_ip_info(
        self,
        ip_addresses: List[str],
        use_cache: bool = True,
        domain_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get geolocation info for multiple IP addresses.

        Uses batch API endpoint when available, otherwise makes
        concurrent individual requests.

        Args:
            ip_addresses: List of IP addresses to look up
            use_cache: Whether to use cached results
            domain_id: Optional domain ID for association

        Returns:
            List of dictionaries containing IP geolocation data

        Raises:
            IPInfoError: For API errors
            ValueError: If batch size exceeds maximum
        """
        if len(ip_addresses) > self.MAX_BATCH_SIZE:
            raise ValueError(
                f"Batch size {len(ip_addresses)} exceeds maximum of {self.MAX_BATCH_SIZE}"
            )

        results: List[Dict[str, Any]] = []
        uncached_ips: List[str] = []

        # Check cache for each IP
        if use_cache:
            for ip in ip_addresses:
                cached = await self._get_cached_ip_info(ip)
                if cached:
                    results.append(cached.to_dict())
                else:
                    uncached_ips.append(ip)
        else:
            uncached_ips = list(ip_addresses)

        if not uncached_ips:
            return results

        # Try batch API first (available for paid plans)
        if self.api_key:
            try:
                batch_data = await self._make_request(
                    "batch",
                    method="POST",
                    data=uncached_ips
                )

                for ip, data in batch_data.items():
                    if isinstance(data, dict) and "ip" in data:
                        record = self._api_response_to_record(data, domain_id)
                        saved_record = await self.repository.create_or_update(record)
                        results.append(saved_record.to_dict())

                return results

            except IPInfoError as e:
                if e.status_code != 403:  # Not a permission error
                    raise
                logger.info("Batch API not available, falling back to individual requests")

        # Fallback to concurrent individual requests
        async def fetch_single(ip: str) -> Optional[Dict[str, Any]]:
            try:
                return await self.get_ip_info(ip, use_cache=False, domain_id=domain_id)
            except (IPInfoError, ValueError) as e:
                logger.warning(f"Failed to fetch IP info for {ip}: {e}")
                return None

        batch_results = await asyncio.gather(
            *[fetch_single(ip) for ip in uncached_ips],
            return_exceptions=False
        )

        results.extend([r for r in batch_results if r is not None])
        return results

    async def get_domain_ips(
        self,
        domain: str,
        include_ipv6: bool = True
    ) -> List[Dict[str, Any]]:
        """Resolve domain to IPs and get info for each.

        Args:
            domain: Domain name to resolve
            include_ipv6: Whether to include IPv6 addresses

        Returns:
            List of dictionaries containing IP geolocation data

        Raises:
            IPInfoError: For API errors
            ValueError: If domain resolution fails
        """
        try:
            # Get both A and AAAA records
            ip_addresses: List[str] = []

            try:
                # Get IPv4 addresses
                ipv4_info = socket.getaddrinfo(
                    domain, None, socket.AF_INET, socket.SOCK_STREAM
                )
                ip_addresses.extend([info[4][0] for info in ipv4_info])
            except socket.gaierror:
                pass

            if include_ipv6:
                try:
                    # Get IPv6 addresses
                    ipv6_info = socket.getaddrinfo(
                        domain, None, socket.AF_INET6, socket.SOCK_STREAM
                    )
                    ip_addresses.extend([info[4][0] for info in ipv6_info])
                except socket.gaierror:
                    pass

            # Remove duplicates while preserving order
            unique_ips = list(dict.fromkeys(ip_addresses))

            if not unique_ips:
                raise ValueError(f"Could not resolve domain: {domain}")

            return await self.get_batch_ip_info(unique_ips)

        except socket.gaierror as e:
            raise ValueError(f"Failed to resolve domain {domain}: {e}") from e

    async def get_geographic_distribution(
        self,
        domain_id: int
    ) -> Dict[str, Any]:
        """Get geographic distribution of IPs for a domain.

        Analyzes stored IP records for a domain to provide
        geographic breakdown by country and region.

        Args:
            domain_id: Database ID of the domain

        Returns:
            Dictionary containing geographic distribution data:
            - countries: Dict mapping country codes to counts
            - regions: Dict mapping regions to counts
            - cities: Dict mapping cities to counts
            - total_ips: Total number of IPs
            - primary_country: Most common country
            - primary_region: Most common region
        """
        records = await self.repository.get_by_domain(domain_id)

        if not records:
            return {
                "countries": {},
                "regions": {},
                "cities": {},
                "total_ips": 0,
                "primary_country": None,
                "primary_region": None
            }

        countries: Dict[str, int] = {}
        regions: Dict[str, int] = {}
        cities: Dict[str, int] = {}

        for record in records:
            if record.country:
                countries[record.country] = countries.get(record.country, 0) + 1
            if record.region:
                regions[record.region] = regions.get(record.region, 0) + 1
            if record.city:
                cities[record.city] = cities.get(record.city, 0) + 1

        primary_country = max(countries.items(), key=lambda x: x[1])[0] if countries else None
        primary_region = max(regions.items(), key=lambda x: x[1])[0] if regions else None

        return {
            "countries": countries,
            "regions": regions,
            "cities": cities,
            "total_ips": len(records),
            "primary_country": primary_country,
            "primary_region": primary_region
        }

    async def analyze_regional_presence(
        self,
        competitor_id: int
    ) -> Dict[str, Any]:
        """Analyze regional market presence for a competitor.

        Provides insights into a competitor's infrastructure
        geographic distribution for market analysis.

        Args:
            competitor_id: Database ID of the competitor

        Returns:
            Dictionary containing regional analysis:
            - presence_score: Overall geographic presence score (0-100)
            - regions: List of regions with presence details
            - market_coverage: Percentage of target markets covered
            - infrastructure_diversity: Score for geographic diversity
            - recommendations: List of market expansion recommendations
        """
        # Import here to avoid circular imports
        from sqlalchemy import select
        from src.models.competitor import Competitor
        from src.models.domain import Domain

        # Get competitor info
        result = await self.db.execute(
            select(Competitor).where(Competitor.id == competitor_id)
        )
        competitor = result.scalar_one_or_none()

        if not competitor:
            raise ValueError(f"Competitor with ID {competitor_id} not found")

        # Get domain associated with competitor
        domain_result = await self.db.execute(
            select(Domain).where(Domain.name == competitor.domain)
        )
        domain = domain_result.scalar_one_or_none()

        if not domain:
            # Try to resolve and store domain IPs
            try:
                await self.get_domain_ips(competitor.domain)
                # Try again after resolution
                domain_result = await self.db.execute(
                    select(Domain).where(Domain.name == competitor.domain)
                )
                domain = domain_result.scalar_one_or_none()
            except ValueError:
                pass

        # Get geographic distribution if we have domain data
        geo_distribution: Dict[str, Any] = {
            "countries": {},
            "regions": {},
            "total_ips": 0
        }

        if domain:
            geo_distribution = await self.get_geographic_distribution(domain.id)

        # Calculate presence metrics
        country_count = len(geo_distribution.get("countries", {}))
        region_count = len(geo_distribution.get("regions", {}))
        total_ips = geo_distribution.get("total_ips", 0)

        # Presence score based on geographic diversity
        # Higher score for more countries and regions
        presence_score = min(100, (country_count * 15) + (region_count * 5) + (total_ips * 2))

        # Infrastructure diversity score
        if total_ips > 0:
            infrastructure_diversity = min(100, (country_count / total_ips) * 100 * 10)
        else:
            infrastructure_diversity = 0

        # Build region details
        regions = []
        for country, count in geo_distribution.get("countries", {}).items():
            country_regions = [
                r for r in geo_distribution.get("regions", {}).keys()
            ]
            regions.append({
                "country": country,
                "ip_count": count,
                "percentage": (count / total_ips * 100) if total_ips > 0 else 0,
                "regions": country_regions[:5]  # Limit to top 5 regions per country
            })

        # Sort by IP count descending
        regions.sort(key=lambda x: x["ip_count"], reverse=True)

        # Generate recommendations
        recommendations = []
        if country_count < 3:
            recommendations.append(
                "Consider expanding infrastructure to additional regions for better global coverage"
            )
        if infrastructure_diversity < 30:
            recommendations.append(
                "Infrastructure is concentrated in few locations - consider geographic distribution"
            )
        if total_ips < 2:
            recommendations.append(
                "Limited IP data available - consider refreshing domain IP information"
            )

        # Estimate market coverage (simplified - would need market data for accuracy)
        # Assume major markets are US, EU, APAC
        major_markets = {"US", "GB", "DE", "FR", "JP", "CN", "AU", "CA", "BR", "IN"}
        covered_markets = set(geo_distribution.get("countries", {}).keys()) & major_markets
        market_coverage = len(covered_markets) / len(major_markets) * 100

        return {
            "competitor_id": competitor_id,
            "competitor_name": competitor.name,
            "competitor_domain": competitor.domain,
            "presence_score": round(presence_score, 2),
            "regions": regions,
            "market_coverage": round(market_coverage, 2),
            "infrastructure_diversity": round(infrastructure_diversity, 2),
            "recommendations": recommendations,
            "total_ips_analyzed": total_ips,
            "countries_count": country_count,
            "regions_count": region_count
        }

    async def track_api_usage(
        self,
        endpoint: str,
        request_count: int = 1
    ) -> None:
        """Track API usage for quota management.

        Args:
            endpoint: API endpoint called
            request_count: Number of requests made
        """
        now = datetime.utcnow()
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=1)

        usage_record = APIUsageRecord(
            api_name="ipinfo",
            endpoint=endpoint,
            request_count=request_count,
            quota_limit=self.RATE_LIMIT,
            period_start=period_start,
            period_end=period_end
        )

        self.db.add(usage_record)
        await self.db.commit()

    async def test_connection(self) -> bool:
        """Test the API connection.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Use a known IP for testing
            await self._make_request("8.8.8.8/json")
            return True
        except (IPInfoError, Exception) as e:
            logger.error(f"IPInfo connection test failed: {e}")
            return False

    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status.

        Returns:
            Dictionary with rate limit information
        """
        now = datetime.utcnow()
        period_elapsed = (now - self._period_start).total_seconds()

        return {
            "requests_made": self._request_count,
            "rate_limit": self.RATE_LIMIT,
            "period_seconds": self.RATE_PERIOD_SECONDS,
            "period_elapsed": period_elapsed,
            "remaining": max(0, self.RATE_LIMIT - self._request_count),
            "reset_in": max(0, self.RATE_PERIOD_SECONDS - period_elapsed)
        }
