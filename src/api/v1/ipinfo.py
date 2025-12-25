"""IPInfo API endpoints.

This module provides REST API endpoints for IP geolocation lookups
and geographic analysis using the IPInfo service.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.services.external_api.ipinfo_service import (
    IPInfoService,
    IPInfoError,
    RateLimitExceededError
)

router = APIRouter()


# Request/Response Models
class IPInfoResponse(BaseModel):
    """Response model for IP info lookup."""
    id: Optional[int] = None
    ip_address: str
    hostname: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    location: Optional[dict] = None
    organization: Optional[str] = None
    postal: Optional[str] = None
    timezone: Optional[str] = None
    domain_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        """Pydantic model configuration."""
        from_attributes = True


class BatchIPRequest(BaseModel):
    """Request model for batch IP lookup."""
    ip_addresses: List[str] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of IP addresses to look up"
    )
    use_cache: bool = Field(
        default=True,
        description="Whether to use cached results"
    )
    domain_id: Optional[int] = Field(
        default=None,
        description="Optional domain ID for association"
    )

    @field_validator("ip_addresses")
    @classmethod
    def validate_ip_addresses(cls, v: List[str]) -> List[str]:
        """Validate IP addresses list."""
        if not v:
            raise ValueError("At least one IP address is required")
        return v


class BatchIPResponse(BaseModel):
    """Response model for batch IP lookup."""
    results: List[IPInfoResponse]
    total: int
    cached: int
    fetched: int


class GeographicDistributionResponse(BaseModel):
    """Response model for geographic distribution."""
    countries: dict = Field(
        default_factory=dict,
        description="IP count by country code"
    )
    regions: dict = Field(
        default_factory=dict,
        description="IP count by region"
    )
    cities: dict = Field(
        default_factory=dict,
        description="IP count by city"
    )
    total_ips: int = Field(
        default=0,
        description="Total number of IPs analyzed"
    )
    primary_country: Optional[str] = Field(
        default=None,
        description="Most common country"
    )
    primary_region: Optional[str] = Field(
        default=None,
        description="Most common region"
    )


class RegionPresence(BaseModel):
    """Model for region presence details."""
    country: str
    ip_count: int
    percentage: float
    regions: List[str]


class RegionalAnalysisResponse(BaseModel):
    """Response model for regional presence analysis."""
    competitor_id: int
    competitor_name: str
    competitor_domain: str
    presence_score: float = Field(
        description="Overall geographic presence score (0-100)"
    )
    regions: List[RegionPresence] = Field(
        description="List of regions with presence details"
    )
    market_coverage: float = Field(
        description="Percentage of major markets covered"
    )
    infrastructure_diversity: float = Field(
        description="Score for geographic diversity"
    )
    recommendations: List[str] = Field(
        description="Market expansion recommendations"
    )
    total_ips_analyzed: int
    countries_count: int
    regions_count: int


class RateLimitStatusResponse(BaseModel):
    """Response model for rate limit status."""
    requests_made: int
    rate_limit: int
    period_seconds: int
    period_elapsed: float
    remaining: int
    reset_in: float


class ErrorResponse(BaseModel):
    """Standard error response model."""
    detail: str
    status_code: int
    error_type: Optional[str] = None


# Dependency
async def get_ipinfo_service(db: AsyncSession = Depends(get_db)) -> IPInfoService:
    """Get IPInfo service instance.

    Args:
        db: Database session from dependency injection

    Returns:
        IPInfoService instance
    """
    return IPInfoService(db)


# Endpoints
@router.get(
    "/{ip_address}",
    response_model=IPInfoResponse,
    summary="Get IP geolocation info",
    response_description="IP geolocation data",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid IP address"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_ip_info(
    ip_address: str,
    use_cache: bool = Query(
        default=True,
        description="Whether to use cached results"
    ),
    domain_id: Optional[int] = Query(
        default=None,
        description="Optional domain ID for association"
    ),
    service: IPInfoService = Depends(get_ipinfo_service)
) -> IPInfoResponse:
    """Get geolocation information for a single IP address.

    - **ip_address**: IPv4 or IPv6 address to look up
    - **use_cache**: Use cached results if available (default: true)
    - **domain_id**: Optional domain ID to associate with this IP

    Returns comprehensive geolocation data including:
    - City, region, and country
    - Latitude and longitude coordinates
    - Organization/ISP information
    - Timezone
    """
    try:
        async with service:
            result = await service.get_ip_info(
                ip_address=ip_address,
                use_cache=use_cache,
                domain_id=domain_id
            )
            return IPInfoResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=e.message,
            headers={"Retry-After": str(e.details.get("retry_after", 60))}
        )
    except IPInfoError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )


@router.post(
    "/batch",
    response_model=BatchIPResponse,
    summary="Batch IP geolocation lookup",
    response_description="Batch IP geolocation results",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def batch_ip_lookup(
    request: BatchIPRequest,
    service: IPInfoService = Depends(get_ipinfo_service)
) -> BatchIPResponse:
    """Look up geolocation information for multiple IP addresses.

    - **ip_addresses**: List of IPv4 or IPv6 addresses (max 1000)
    - **use_cache**: Use cached results if available (default: true)
    - **domain_id**: Optional domain ID to associate with these IPs

    Uses batch API when available, otherwise makes concurrent requests.
    Cached results are returned immediately without API calls.
    """
    try:
        async with service:
            # Get initial cache count
            cached_count = 0
            if request.use_cache:
                for ip in request.ip_addresses:
                    cached = await service._get_cached_ip_info(ip)
                    if cached:
                        cached_count += 1

            results = await service.get_batch_ip_info(
                ip_addresses=request.ip_addresses,
                use_cache=request.use_cache,
                domain_id=request.domain_id
            )

            return BatchIPResponse(
                results=[IPInfoResponse(**r) for r in results],
                total=len(results),
                cached=cached_count,
                fetched=len(results) - cached_count
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=e.message,
            headers={"Retry-After": str(e.details.get("retry_after", 60))}
        )
    except IPInfoError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )


@router.get(
    "/domain/{domain_id}/geo",
    response_model=GeographicDistributionResponse,
    summary="Get geographic distribution for domain",
    response_description="Geographic distribution analysis",
    responses={
        404: {"model": ErrorResponse, "description": "Domain not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_geographic_distribution(
    domain_id: int,
    service: IPInfoService = Depends(get_ipinfo_service)
) -> GeographicDistributionResponse:
    """Get geographic distribution of IPs for a domain.

    - **domain_id**: Database ID of the domain to analyze

    Returns geographic breakdown including:
    - IP counts by country, region, and city
    - Primary country and region
    - Total IPs analyzed
    """
    try:
        async with service:
            result = await service.get_geographic_distribution(domain_id)
            return GeographicDistributionResponse(**result)

    except IPInfoError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )


@router.get(
    "/competitor/{competitor_id}/regions",
    response_model=RegionalAnalysisResponse,
    summary="Analyze competitor regional presence",
    response_description="Regional presence analysis",
    responses={
        404: {"model": ErrorResponse, "description": "Competitor not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def analyze_regional_presence(
    competitor_id: int,
    service: IPInfoService = Depends(get_ipinfo_service)
) -> RegionalAnalysisResponse:
    """Analyze regional market presence for a competitor.

    - **competitor_id**: Database ID of the competitor to analyze

    Provides insights into a competitor's infrastructure geographic
    distribution for market analysis, including:
    - Overall presence score (0-100)
    - List of regions with IP counts and percentages
    - Market coverage percentage
    - Infrastructure diversity score
    - Recommendations for market expansion
    """
    try:
        async with service:
            result = await service.analyze_regional_presence(competitor_id)
            return RegionalAnalysisResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except IPInfoError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )


@router.get(
    "/status",
    response_model=RateLimitStatusResponse,
    summary="Get API rate limit status",
    response_description="Current rate limit status"
)
async def get_rate_limit_status(
    service: IPInfoService = Depends(get_ipinfo_service)
) -> RateLimitStatusResponse:
    """Get current rate limit status for IPInfo API.

    Returns information about:
    - Requests made in current period
    - Rate limit and remaining quota
    - Time until rate limit reset
    """
    async with service:
        result = await service.get_rate_limit_status()
        return RateLimitStatusResponse(**result)


@router.get(
    "/health",
    response_model=dict,
    summary="Health check for IPInfo service",
    response_description="Service health status"
)
async def health_check(
    service: IPInfoService = Depends(get_ipinfo_service)
) -> dict:
    """Check health of IPInfo service connection.

    Tests the API connection and returns status.
    """
    async with service:
        is_healthy = await service.test_connection()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "ipinfo",
            "connected": is_healthy
        }
