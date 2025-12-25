"""WhoAPI API Endpoints.

This module provides REST API endpoints for domain intelligence operations
using the WhoAPI service adapter.

Endpoints:
- GET /api/v1/whoapi/whois/{domain} - WHOIS lookup
- GET /api/v1/whoapi/ssl/{domain} - SSL certificate info
- GET /api/v1/whoapi/dns/{domain} - DNS records
- GET /api/v1/whoapi/tech/{domain} - Technology stack detection
- GET /api/v1/whoapi/age/{domain} - Domain age calculation
- GET /api/v1/whoapi/availability/{domain} - Domain availability check
- GET /api/v1/whoapi/expiring - Domains expiring soon
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.services.external_api.whoapi_service import (
    WhoAPIService,
    WhoAPIError,
    RateLimitError,
    DomainNotFoundError,
    WhoisData,
    SSLInfo,
    DNSInfo,
    TechStackInfo,
    DomainAge,
    DomainAvailability,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class WhoisResponse(BaseModel):
    """Response model for WHOIS lookup."""

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Dict[str, Any]] = Field(
        None, description="WHOIS data"
    )
    error: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "domain_name": "example.com",
                    "registrar": "Example Registrar, Inc.",
                    "registration_date": "2020-01-15T00:00:00",
                    "expiration_date": "2025-01-15T00:00:00",
                    "nameservers": ["ns1.example.com", "ns2.example.com"],
                    "status": ["clientTransferProhibited"],
                    "dnssec": True,
                    "registrant_org": "Example Organization",
                    "registrant_country": "US",
                },
                "error": None,
            }
        }


class SSLResponse(BaseModel):
    """Response model for SSL certificate info."""

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Dict[str, Any]] = Field(
        None, description="SSL certificate data"
    )
    error: Optional[str] = Field(None, description="Error message if failed")


class DNSResponse(BaseModel):
    """Response model for DNS records."""

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Dict[str, Any]] = Field(
        None, description="DNS records data"
    )
    error: Optional[str] = Field(None, description="Error message if failed")


class TechStackResponse(BaseModel):
    """Response model for technology stack analysis."""

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Dict[str, Any]] = Field(
        None, description="Technology stack data"
    )
    error: Optional[str] = Field(None, description="Error message if failed")


class DomainAgeResponse(BaseModel):
    """Response model for domain age calculation."""

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Dict[str, Any]] = Field(
        None, description="Domain age data"
    )
    error: Optional[str] = Field(None, description="Error message if failed")


class DomainAvailabilityResponse(BaseModel):
    """Response model for domain availability check."""

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Dict[str, Any]] = Field(
        None, description="Domain availability data"
    )
    error: Optional[str] = Field(None, description="Error message if failed")


class ExpiringDomainsResponse(BaseModel):
    """Response model for expiring domains list."""

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of expiring domains"
    )
    count: int = Field(0, description="Number of expiring domains")
    error: Optional[str] = Field(None, description="Error message if failed")


def get_whoapi_service(db: AsyncSession = Depends(get_db)) -> WhoAPIService:
    """Dependency to get WhoAPI service instance.

    Args:
        db: Database session from dependency injection.

    Returns:
        WhoAPIService instance with database session.
    """
    return WhoAPIService(db=db)


@router.get(
    "/whois/{domain}",
    response_model=WhoisResponse,
    summary="Get WHOIS information",
    description="Retrieve WHOIS registration data for a domain including registrar, dates, and contact info.",
    responses={
        200: {"description": "WHOIS data retrieved successfully"},
        404: {"description": "Domain not found"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
async def get_whois(
    domain: str,
    service: WhoAPIService = Depends(get_whoapi_service),
) -> WhoisResponse:
    """Get WHOIS information for a domain.

    Args:
        domain: The domain to look up (e.g., "example.com").
        service: WhoAPI service instance.

    Returns:
        WhoisResponse with WHOIS data.

    Raises:
        HTTPException: If the request fails.
    """
    try:
        async with service:
            whois_data = await service.get_whois_info(domain)
            return WhoisResponse(
                success=True,
                data=whois_data.dict(),
                error=None,
            )
    except DomainNotFoundError as e:
        logger.warning(f"Domain not found: {domain}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded for WHOIS lookup: {domain}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )
    except WhoAPIError as e:
        logger.error(f"WhoAPI error for {domain}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error for WHOIS lookup: {domain}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get(
    "/ssl/{domain}",
    response_model=SSLResponse,
    summary="Get SSL certificate information",
    description="Retrieve SSL certificate details for a domain including issuer, validity, and expiry.",
    responses={
        200: {"description": "SSL data retrieved successfully"},
        404: {"description": "Domain not found or no SSL"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
async def get_ssl(
    domain: str,
    service: WhoAPIService = Depends(get_whoapi_service),
) -> SSLResponse:
    """Get SSL certificate information for a domain.

    Args:
        domain: The domain to check (e.g., "example.com").
        service: WhoAPI service instance.

    Returns:
        SSLResponse with SSL certificate data.
    """
    try:
        async with service:
            ssl_info = await service.get_ssl_info(domain)
            return SSLResponse(
                success=True,
                data=ssl_info.dict(),
                error=None,
            )
    except DomainNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )
    except WhoAPIError as e:
        logger.error(f"WhoAPI error for SSL {domain}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error for SSL lookup: {domain}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get(
    "/dns/{domain}",
    response_model=DNSResponse,
    summary="Get DNS records",
    description="Retrieve DNS records for a domain including A, AAAA, MX, NS, TXT, and CNAME records.",
    responses={
        200: {"description": "DNS data retrieved successfully"},
        404: {"description": "Domain not found"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
async def get_dns(
    domain: str,
    service: WhoAPIService = Depends(get_whoapi_service),
) -> DNSResponse:
    """Get DNS records for a domain.

    Args:
        domain: The domain to query (e.g., "example.com").
        service: WhoAPI service instance.

    Returns:
        DNSResponse with DNS records.
    """
    try:
        async with service:
            dns_info = await service.get_dns_records(domain)
            return DNSResponse(
                success=True,
                data=dns_info.dict(),
                error=None,
            )
    except DomainNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )
    except WhoAPIError as e:
        logger.error(f"WhoAPI error for DNS {domain}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error for DNS lookup: {domain}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get(
    "/tech/{domain}",
    response_model=TechStackResponse,
    summary="Analyze technology stack",
    description="Detect technologies used by a domain including CMS, frameworks, analytics, and hosting.",
    responses={
        200: {"description": "Tech stack data retrieved successfully"},
        404: {"description": "Domain not found"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
async def get_tech_stack(
    domain: str,
    service: WhoAPIService = Depends(get_whoapi_service),
) -> TechStackResponse:
    """Analyze technology stack for a domain.

    Args:
        domain: The domain to analyze (e.g., "example.com").
        service: WhoAPI service instance.

    Returns:
        TechStackResponse with detected technologies.
    """
    try:
        async with service:
            tech_info = await service.analyze_tech_stack(domain)
            return TechStackResponse(
                success=True,
                data=tech_info.dict(),
                error=None,
            )
    except DomainNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )
    except WhoAPIError as e:
        logger.error(f"WhoAPI error for tech stack {domain}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error for tech stack analysis: {domain}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get(
    "/age/{domain}",
    response_model=DomainAgeResponse,
    summary="Get domain age",
    description="Calculate the age of a domain based on its registration date.",
    responses={
        200: {"description": "Domain age data retrieved successfully"},
        404: {"description": "Domain not found"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
async def get_domain_age(
    domain: str,
    service: WhoAPIService = Depends(get_whoapi_service),
) -> DomainAgeResponse:
    """Get domain age for a domain.

    Args:
        domain: The domain to check (e.g., "example.com").
        service: WhoAPI service instance.

    Returns:
        DomainAgeResponse with age information.
    """
    try:
        async with service:
            age_info = await service.get_domain_age(domain)
            return DomainAgeResponse(
                success=True,
                data=age_info.dict(),
                error=None,
            )
    except DomainNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )
    except WhoAPIError as e:
        logger.error(f"WhoAPI error for domain age {domain}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error for domain age: {domain}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get(
    "/availability/{domain}",
    response_model=DomainAvailabilityResponse,
    summary="Check domain availability",
    description="Check if a domain is available for registration.",
    responses={
        200: {"description": "Availability data retrieved successfully"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
async def check_availability(
    domain: str,
    service: WhoAPIService = Depends(get_whoapi_service),
) -> DomainAvailabilityResponse:
    """Check domain availability.

    Args:
        domain: The domain to check (e.g., "example.com").
        service: WhoAPI service instance.

    Returns:
        DomainAvailabilityResponse with availability status.
    """
    try:
        async with service:
            availability = await service.check_domain_availability(domain)
            return DomainAvailabilityResponse(
                success=True,
                data=availability.dict(),
                error=None,
            )
    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )
    except WhoAPIError as e:
        logger.error(f"WhoAPI error for availability {domain}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error for availability check: {domain}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get(
    "/expiring",
    response_model=ExpiringDomainsResponse,
    summary="Get expiring domains",
    description="Get a list of tracked domains that are expiring within the specified number of days.",
    responses={
        200: {"description": "Expiring domains list retrieved successfully"},
        500: {"description": "Internal server error"},
    },
)
async def get_expiring_domains(
    days: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Number of days to look ahead for expiring domains",
    ),
    service: WhoAPIService = Depends(get_whoapi_service),
) -> ExpiringDomainsResponse:
    """Get domains expiring within the specified number of days.

    This endpoint returns domains from the local database that have
    been previously looked up and are expiring soon.

    Args:
        days: Number of days to look ahead (1-365).
        service: WhoAPI service instance.

    Returns:
        ExpiringDomainsResponse with list of expiring domains.
    """
    try:
        expiring = await service.get_expiring_domains(days=days)
        return ExpiringDomainsResponse(
            success=True,
            data=expiring,
            count=len(expiring),
            error=None,
        )
    except Exception as e:
        logger.exception(f"Unexpected error getting expiring domains")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get(
    "/health",
    summary="Health check",
    description="Check if the WhoAPI service is configured and accessible.",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unavailable"},
    },
)
async def health_check(
    service: WhoAPIService = Depends(get_whoapi_service),
) -> Dict[str, Any]:
    """Check WhoAPI service health.

    Args:
        service: WhoAPI service instance.

    Returns:
        Health status information.
    """
    try:
        async with service:
            is_connected = await service.test_connection()
            rate_limit_status = await service.get_rate_limit_status()

            if is_connected:
                return {
                    "status": "healthy",
                    "service": "whoapi",
                    "connected": True,
                    "rate_limit": rate_limit_status,
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="WhoAPI service is not responding",
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}",
        )
