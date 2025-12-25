"""
Pydantic models for competitor analysis requests and responses.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, HttpUrl, validator
from enum import Enum

class AnalysisType(str, Enum):
    """Types of competitor analysis that can be performed."""
    SEO = "seo"
    CONTENT = "content"
    BACKLINKS = "backlinks"
    SOCIAL = "social"
    PAID = "paid"
    KEYWORDS = "keywords"
    TRAFFIC = "traffic"
    SENTIMENT = "sentiment"
    ENGAGEMENT = "engagement"

class Timeframe(str, Enum):
    """Timeframes for analysis."""
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"
    YEAR = "365d"
    ALL = "all"

class CompetitorAnalysisRequest(BaseModel):
    """Request model for competitor analysis."""
    company_id: int = Field(..., description="ID of the company to analyze")
    competitor_ids: List[int] = Field(
        default_factory=list,
        description="List of competitor IDs to analyze (if empty, will identify automatically)"
    )
    analysis_types: List[AnalysisType] = Field(
        default_factory=lambda: [AnalysisType.SEO, AnalysisType.CONTENT, AnalysisType.KEYWORDS],
        description="Types of analysis to perform"
    )
    timeframe: Timeframe = Field(
        default=Timeframe.MONTH,
        description="Timeframe for the analysis"
    )
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "company_id": 1,
                "competitor_ids": [2, 3, 4],
                "analysis_types": ["seo", "content", "keywords"],
                "timeframe": "30d"
            }
        }

class CompetitorIdentificationResponse(BaseModel):
    """Response model for identified competitors."""
    domain: str = Field(..., description="Competitor domain")
    name: str = Field("", description="Competitor name")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0-1)")
    source: str = Field(..., description="Source of the competitor identification")
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="SEO and other metrics for the competitor"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the competitor"
    )
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "domain": "competitor.com",
                "name": "Competitor Inc.",
                "relevance_score": 0.85,
                "source": "seo_analysis",
                "metrics": {
                    "domain_authority": 65,
                    "monthly_traffic": 50000,
                    "backlinks": 12000
                },
                "metadata": {
                    "common_keywords": ["saas", "software", "business"],
                    "industry": "Technology"
                }
            }
        }

class CompetitorComparisonResponse(BaseModel):
    """Response model for competitor comparison."""
    company_id: int = Field(..., description="ID of the company being analyzed")
    company_name: str = Field(..., description="Name of the company being analyzed")
    competitors: List[Dict[str, Any]] = Field(
        ...,
        description="List of competitors with comparison metrics"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Aggregated metrics and comparison data"
    )
    summary: str = Field(
        "",
        description="Summary of the comparison"
    )
    insights: List[str] = Field(
        default_factory=list,
        description="Key insights from the comparison"
    )
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "company_id": 1,
                "company_name": "Example Inc.",
                "competitors": [
                    {
                        "id": 2,
                        "name": "Competitor A",
                        "domain": "competitor-a.com",
                        "traffic": 50000,
                        "traffic_difference": 0.25,
                        "backlinks": 12000,
                        "backlinks_difference": -0.1
                    },
                    {
                        "id": 3,
                        "name": "Competitor B",
                        "domain": "competitor-b.com",
                        "traffic": 75000,
                        "traffic_difference": 0.5,
                        "backlinks": 15000,
                        "backlinks_difference": 0.2
                    }
                ],
                "metrics": {
                    "traffic": {
                        "company": 40000,
                        "average": 62500,
                        "median": 62500,
                        "min": 50000,
                        "max": 75000
                    },
                    "backlinks": {
                        "company": 10000,
                        "average": 13500,
                        "median": 13500,
                        "min": 12000,
                        "max": 15000
                    }
                },
                "summary": "Example Inc. has lower traffic and backlinks compared to competitors.",
                "insights": [
                    "Competitor B has 50% more traffic than Example Inc.",
                    "Competitor A has 20% more backlinks than Example Inc.",
                    "Example Inc. ranks lower for key industry keywords compared to competitors."
                ]
            }
        }

class CompetitorAnalysisResponse(BaseModel):
    """Response model for comprehensive competitor analysis."""
    company_id: int = Field(..., description="ID of the company being analyzed")
    company_name: str = Field(..., description="Name of the company being analyzed")
    competitors: List[Dict[str, Any]] = Field(
        ...,
        description="List of competitors with analysis results"
    )
    summary: str = Field(
        "",
        description="Summary of the analysis"
    )
    insights: List[str] = Field(
        default_factory=list,
        description="Key insights from the analysis"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable recommendations based on the analysis"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Aggregated metrics and analysis data"
    )
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "company_id": 1,
                "company_name": "Example Inc.",
                "competitors": [
                    {
                        "id": 2,
                        "name": "Competitor A",
                        "domain": "competitor-a.com",
                        "seo_score": 85,
                        "content_quality": 78,
                        "backlink_quality": 82,
                        "social_engagement": 65,
                        "keyword_overlap": 0.45
                    },
                    {
                        "id": 3,
                        "name": "Competitor B",
                        "domain": "competitor-b.com",
                        "seo_score": 92,
                        "content_quality": 88,
                        "backlink_quality": 95,
                        "social_engagement": 78,
                        "keyword_overlap": 0.62
                    }
                ],
                "summary": "Competitive analysis reveals opportunities for improvement in SEO and content strategy.",
                "insights": [
                    "Competitor B has a significantly stronger backlink profile.",
                    "Competitor A has more comprehensive content coverage in key areas.",
                    "Both competitors outperform in social engagement metrics."
                ],
                "recommendations": [
                    "Develop a backlink acquisition strategy to improve domain authority.",
                    "Expand content coverage for high-value, low-competition keywords.",
                    "Increase social media engagement through targeted campaigns."
                ],
                "metrics": {
                    "average_seo_score": 88.5,
                    "average_content_quality": 83.0,
                    "average_backlink_quality": 88.5,
                    "average_social_engagement": 71.5,
                    "average_keyword_overlap": 0.535
                }
            }
        }
