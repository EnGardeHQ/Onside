"""Repository package for OnSide application.

This package contains repository classes that provide data access layer
operations for the application's domain models. Each repository handles
database operations for a specific entity or group of related entities.
"""

# Core entity repositories
from src.repositories.company_repository import CompanyRepository
from src.repositories.competitor_repository import CompetitorRepository
from src.repositories.competitor_metrics_repository import CompetitorMetricsRepository
from src.repositories.domain_repository import DomainRepository

# External API data repositories
from src.repositories.gnews_repository import GNewsRepository
from src.repositories.ipinfo_repository import IPInfoRepository
from src.repositories.whoapi_repository import WhoAPIRepository
from src.repositories.api_usage_repository import APIUsageRepository

__all__ = [
    # Core repositories
    "CompanyRepository",
    "CompetitorRepository",
    "CompetitorMetricsRepository",
    "DomainRepository",
    # External API repositories
    "GNewsRepository",
    "IPInfoRepository",
    "WhoAPIRepository",
    "APIUsageRepository",
]
