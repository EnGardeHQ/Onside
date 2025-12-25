"""Models package for OnSide application.

Following Semantic Seed coding standards with proper BDD/TDD methodology,
this package contains SQLAlchemy ORM models for our verified PostgreSQL schema.
"""
# Import Base directly to avoid circular imports
from src.database import Base

# Import models directly - order matters for SQLAlchemy relationships
# Domain and Company models come first since they're referenced by others
from src.models.domain import Domain
from src.models.company import Company
from src.models.link import Link, LinkSnapshot
from src.models.competitor import Competitor
from src.models.competitor_content import CompetitorContent
from src.models.competitor_metrics import CompetitorMetrics, MetricType, DataSource
from src.models.ai import AIInsight, InsightType
from src.models.content import Content, ContentEngagementHistory
from src.models.trend import TrendAnalysis
from src.models.engagement import EngagementMetrics
from src.models.report import Report, ReportStatus, ReportType
from src.models.external_api import (
    GNewsArticle,
    IPInfoRecord,
    WhoisRecord,
    APIUsageRecord,
)
from src.models.brand_analysis import (
    BrandAnalysisJob,
    DiscoveredKeyword,
    IdentifiedCompetitor,
    ContentOpportunity,
    AnalysisStatus,
    KeywordSource,
    CompetitorCategory,
    GapType,
    ContentPriority,
)

# Import user model separately to avoid circular imports
# User model will be imported directly where needed

__all__ = [
    "Base",
    "AIInsight",
    "InsightType",
    "Content",
    "ContentEngagementHistory",
    "TrendAnalysis",
    "EngagementMetrics",
    "Link",
    "LinkSnapshot",
    "Domain",
    "Company",
    "Competitor",
    "CompetitorContent",
    "CompetitorMetrics",
    "MetricType",
    "DataSource",
    "Report",
    "ReportStatus",
    "ReportType",
    "GNewsArticle",
    "IPInfoRecord",
    "WhoisRecord",
    "APIUsageRecord",
    "BrandAnalysisJob",
    "DiscoveredKeyword",
    "IdentifiedCompetitor",
    "ContentOpportunity",
    "AnalysisStatus",
    "KeywordSource",
    "CompetitorCategory",
    "GapType",
    "ContentPriority",
]
