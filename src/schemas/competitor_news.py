"""
Pydantic models for competitor news analysis requests and responses.

This module provides schemas for the enhanced competitor analysis with news integration,
including sentiment analysis, topic extraction, and news trend tracking.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class SentimentCategory(str, Enum):
    """Sentiment classification categories."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class NewsSentimentScore(BaseModel):
    """Sentiment analysis result for a news article or collection."""
    score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Sentiment score from -1 (negative) to 1 (positive)"
    )
    category: SentimentCategory = Field(
        ...,
        description="Sentiment category classification"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the sentiment analysis"
    )


class NewsArticleResponse(BaseModel):
    """Response model for a single news article."""
    id: int = Field(..., description="Article database ID")
    article_id: str = Field(..., description="Unique article identifier from GNews")
    title: str = Field(..., description="Article headline")
    description: Optional[str] = Field(None, description="Article summary")
    url: str = Field(..., description="Link to the original article")
    image_url: Optional[str] = Field(None, description="Featured image URL")
    published_at: datetime = Field(..., description="Publication date")
    source_name: str = Field(..., description="News source name")
    source_url: Optional[str] = Field(None, description="News source URL")
    query_term: Optional[str] = Field(None, description="Search term used")
    language: Optional[str] = Field(None, description="Article language code")
    country: Optional[str] = Field(None, description="Article country code")
    sentiment: Optional[NewsSentimentScore] = Field(
        None,
        description="Sentiment analysis result for this article"
    )

    class Config:
        """Pydantic config."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "article_id": "abc123",
                "title": "Company X Announces New Product Line",
                "description": "Company X unveiled their latest product suite...",
                "url": "https://news.example.com/article/123",
                "image_url": "https://news.example.com/images/123.jpg",
                "published_at": "2024-01-15T10:30:00Z",
                "source_name": "Tech News Daily",
                "source_url": "https://technewsdaily.com",
                "query_term": "Company X",
                "language": "en",
                "country": "us",
                "sentiment": {
                    "score": 0.65,
                    "category": "positive",
                    "confidence": 0.85
                }
            }
        }


class CompetitorNewsResponse(BaseModel):
    """Response model for competitor news retrieval."""
    competitor_id: int = Field(..., description="ID of the competitor")
    competitor_name: str = Field(..., description="Name of the competitor")
    total_articles: int = Field(..., description="Total number of articles found")
    articles: List[NewsArticleResponse] = Field(
        default_factory=list,
        description="List of news articles"
    )
    date_range: Dict[str, Optional[datetime]] = Field(
        default_factory=dict,
        description="Date range of retrieved articles"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "competitor_id": 1,
                "competitor_name": "Competitor Corp",
                "total_articles": 25,
                "articles": [],
                "date_range": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-31T23:59:59Z"
                }
            }
        }


class TopicFrequency(BaseModel):
    """Topic frequency data from news analysis."""
    topic: str = Field(..., description="Topic or keyword")
    count: int = Field(..., ge=0, description="Frequency count")
    percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of articles mentioning this topic"
    )


class SourceDiversity(BaseModel):
    """Source diversity analysis."""
    source_name: str = Field(..., description="News source name")
    article_count: int = Field(..., ge=0, description="Number of articles from this source")
    percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of articles from this source"
    )
    average_sentiment: Optional[float] = Field(
        None,
        ge=-1.0,
        le=1.0,
        description="Average sentiment score for articles from this source"
    )


class NewsSentimentAnalysisResponse(BaseModel):
    """Response model for competitor news sentiment analysis."""
    competitor_id: int = Field(..., description="ID of the competitor")
    competitor_name: str = Field(..., description="Name of the competitor")
    analysis_period: Dict[str, Optional[datetime]] = Field(
        ...,
        description="Analysis period date range"
    )
    overall_sentiment: NewsSentimentScore = Field(
        ...,
        description="Overall sentiment across all analyzed articles"
    )
    article_count: int = Field(..., description="Number of articles analyzed")
    sentiment_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Distribution of sentiment categories"
    )
    top_positive_articles: List[NewsArticleResponse] = Field(
        default_factory=list,
        description="Top articles with positive sentiment"
    )
    top_negative_articles: List[NewsArticleResponse] = Field(
        default_factory=list,
        description="Top articles with negative sentiment"
    )
    sentiment_trend: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Sentiment trend over time"
    )
    key_topics: List[TopicFrequency] = Field(
        default_factory=list,
        description="Key topics extracted from articles"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "competitor_id": 1,
                "competitor_name": "Competitor Corp",
                "analysis_period": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-31T23:59:59Z"
                },
                "overall_sentiment": {
                    "score": 0.35,
                    "category": "positive",
                    "confidence": 0.78
                },
                "article_count": 45,
                "sentiment_distribution": {
                    "positive": 25,
                    "neutral": 15,
                    "negative": 5
                },
                "top_positive_articles": [],
                "top_negative_articles": [],
                "sentiment_trend": [
                    {"date": "2024-01-07", "score": 0.42, "count": 12},
                    {"date": "2024-01-14", "score": 0.28, "count": 15}
                ],
                "key_topics": [
                    {"topic": "innovation", "count": 20, "percentage": 44.4},
                    {"topic": "partnership", "count": 12, "percentage": 26.7}
                ]
            }
        }


class NewsVolumeDataPoint(BaseModel):
    """Data point for news volume tracking."""
    date: datetime = Field(..., description="Date for this data point")
    article_count: int = Field(..., ge=0, description="Number of articles")
    average_sentiment: Optional[float] = Field(
        None,
        ge=-1.0,
        le=1.0,
        description="Average sentiment for this period"
    )


class NewsTrendsResponse(BaseModel):
    """Response model for competitor news trends analysis."""
    competitor_id: int = Field(..., description="ID of the competitor")
    competitor_name: str = Field(..., description="Name of the competitor")
    analysis_period: Dict[str, Optional[datetime]] = Field(
        ...,
        description="Analysis period date range"
    )
    total_articles: int = Field(..., description="Total articles in period")
    volume_trend: List[NewsVolumeDataPoint] = Field(
        default_factory=list,
        description="News volume over time"
    )
    volume_change_percentage: float = Field(
        ...,
        description="Percentage change in news volume"
    )
    trending_topics: List[TopicFrequency] = Field(
        default_factory=list,
        description="Trending topics in recent news"
    )
    emerging_topics: List[TopicFrequency] = Field(
        default_factory=list,
        description="Newly emerging topics"
    )
    source_diversity: List[SourceDiversity] = Field(
        default_factory=list,
        description="Diversity of news sources"
    )
    peak_coverage_dates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Dates with peak news coverage"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "competitor_id": 1,
                "competitor_name": "Competitor Corp",
                "analysis_period": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-31T23:59:59Z"
                },
                "total_articles": 45,
                "volume_trend": [
                    {"date": "2024-01-07T00:00:00Z", "article_count": 12, "average_sentiment": 0.42},
                    {"date": "2024-01-14T00:00:00Z", "article_count": 15, "average_sentiment": 0.28}
                ],
                "volume_change_percentage": 25.0,
                "trending_topics": [
                    {"topic": "innovation", "count": 20, "percentage": 44.4}
                ],
                "emerging_topics": [
                    {"topic": "sustainability", "count": 5, "percentage": 11.1}
                ],
                "source_diversity": [
                    {"source_name": "Tech News", "article_count": 15, "percentage": 33.3, "average_sentiment": 0.45}
                ],
                "peak_coverage_dates": [
                    {"date": "2024-01-15", "article_count": 8, "reason": "Product launch"}
                ]
            }
        }


class CompetitorNewsComparisonItem(BaseModel):
    """Comparison item for a single competitor in news coverage comparison."""
    competitor_id: int = Field(..., description="ID of the competitor")
    competitor_name: str = Field(..., description="Name of the competitor")
    article_count: int = Field(..., ge=0, description="Number of articles")
    share_of_voice: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Share of voice percentage"
    )
    average_sentiment: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Average sentiment score"
    )
    sentiment_category: SentimentCategory = Field(
        ...,
        description="Overall sentiment category"
    )
    top_sources: List[str] = Field(
        default_factory=list,
        description="Top news sources covering this competitor"
    )
    top_topics: List[str] = Field(
        default_factory=list,
        description="Top topics in news coverage"
    )


class NewsComparisonResponse(BaseModel):
    """Response model for comparing news coverage across competitors."""
    analysis_period: Dict[str, Optional[datetime]] = Field(
        ...,
        description="Analysis period date range"
    )
    total_articles: int = Field(..., description="Total articles analyzed")
    competitors: List[CompetitorNewsComparisonItem] = Field(
        default_factory=list,
        description="Comparison data for each competitor"
    )
    coverage_leader: Optional[int] = Field(
        None,
        description="Competitor ID with highest news coverage"
    )
    sentiment_leader: Optional[int] = Field(
        None,
        description="Competitor ID with highest sentiment"
    )
    insights: List[str] = Field(
        default_factory=list,
        description="Key insights from the comparison"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "analysis_period": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-31T23:59:59Z"
                },
                "total_articles": 120,
                "competitors": [
                    {
                        "competitor_id": 1,
                        "competitor_name": "Competitor A",
                        "article_count": 45,
                        "share_of_voice": 37.5,
                        "average_sentiment": 0.42,
                        "sentiment_category": "positive",
                        "top_sources": ["Tech News", "Business Daily"],
                        "top_topics": ["innovation", "growth"]
                    },
                    {
                        "competitor_id": 2,
                        "competitor_name": "Competitor B",
                        "article_count": 75,
                        "share_of_voice": 62.5,
                        "average_sentiment": 0.15,
                        "sentiment_category": "neutral",
                        "top_sources": ["Market Watch", "Industry Today"],
                        "top_topics": ["expansion", "partnership"]
                    }
                ],
                "coverage_leader": 2,
                "sentiment_leader": 1,
                "insights": [
                    "Competitor B has 67% more news coverage than Competitor A",
                    "Competitor A has significantly more positive sentiment"
                ]
            }
        }


class NewsRefreshRequest(BaseModel):
    """Request model for refreshing competitor news data."""
    days_back: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Number of days to fetch news for"
    )
    max_articles: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of articles to fetch"
    )
    include_sentiment: bool = Field(
        default=True,
        description="Whether to analyze sentiment for fetched articles"
    )
    query_terms: Optional[List[str]] = Field(
        None,
        description="Custom query terms (defaults to competitor name and domain)"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "days_back": 30,
                "max_articles": 100,
                "include_sentiment": True,
                "query_terms": ["Company Name", "company.com"]
            }
        }


class NewsRefreshResponse(BaseModel):
    """Response model for news refresh operation."""
    competitor_id: int = Field(..., description="ID of the competitor")
    competitor_name: str = Field(..., description="Name of the competitor")
    articles_fetched: int = Field(..., ge=0, description="Number of new articles fetched")
    articles_updated: int = Field(..., ge=0, description="Number of articles updated")
    total_articles: int = Field(..., ge=0, description="Total articles for competitor")
    fetch_date_range: Dict[str, datetime] = Field(
        ...,
        description="Date range of fetched articles"
    )
    status: str = Field(..., description="Status of the refresh operation")
    errors: List[str] = Field(
        default_factory=list,
        description="Any errors encountered during refresh"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "competitor_id": 1,
                "competitor_name": "Competitor Corp",
                "articles_fetched": 15,
                "articles_updated": 3,
                "total_articles": 45,
                "fetch_date_range": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-31T23:59:59Z"
                },
                "status": "success",
                "errors": []
            }
        }


class NewsQueryParams(BaseModel):
    """Query parameters for news endpoints."""
    days_back: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Number of days to look back"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of articles to return"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Offset for pagination"
    )
    source: Optional[str] = Field(
        None,
        description="Filter by news source"
    )
    include_sentiment: bool = Field(
        default=True,
        description="Include sentiment analysis in response"
    )
