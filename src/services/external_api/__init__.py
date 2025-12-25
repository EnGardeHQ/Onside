"""External API Service Package.

This package contains service adapters for external API integrations:
- GNews API: News article retrieval and competitor monitoring
- IPInfo API: IP and domain geolocation
- WhoAPI: Domain WHOIS information
"""

from src.services.external_api.gnews_service import (
    GNewsService,
    GNewsAPIError,
    GNewsRateLimitError,
    GNewsAuthenticationError,
)

from src.services.external_api.ipinfo_service import (
    IPInfoService,
    IPInfoError,
    RateLimitExceededError,
)

from src.services.external_api.whoapi_service import (
    WhoAPIService,
    WhoAPIError,
    RateLimitError as WhoAPIRateLimitError,
    DomainNotFoundError,
)

__all__ = [
    "GNewsService",
    "GNewsAPIError",
    "GNewsRateLimitError",
    "GNewsAuthenticationError",
    "IPInfoService",
    "IPInfoError",
    "RateLimitExceededError",
    "WhoAPIService",
    "WhoAPIError",
    "WhoAPIRateLimitError",
    "DomainNotFoundError",
]
