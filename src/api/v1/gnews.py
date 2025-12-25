"""GNews API endpoints for OnSide application.

This module provides REST API endpoints for interacting with the GNews service,
enabling news search, competitor news retrieval, and headline access.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.services.external_api.gnews_service import (
    GNewsService,
    GNewsAPIError,
    GNewsRateLimitError,
    GNewsAuthenticationError,
)

router = APIRouter()


# ----- Pydantic Schemas -----

class ArticleResponse(BaseModel):
    """Response schema for a news article."""

    id: Optional[int] = Field(None, description="Database ID")
    article_id: str = Field(..., description="Unique article identifier")
    title: str = Field(..., description="Article headline")
    description: Optional[str] = Field(None, description="Article summary")
    content: Optional[str] = Field(None, description="Full article content")
    url: str = Field(..., description="Link to original article")
    image_url: Optional[str] = Field(None, description="Featured image URL")
    published_at: Optional[str] = Field(None, description="Publication date (ISO format)")
    source_name: str = Field(..., description="News source name")
    source_url: Optional[str] = Field(None, description="News source website")
    query_term: Optional[str] = Field(None, description="Search query used")
    language: Optional[str] = Field(None, description="Article language code")
    country: Optional[str] = Field(None, description="Article country code")
    competitor_id: Optional[int] = Field(None, description="Associated competitor ID")

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


class NewsSearchResponse(BaseModel):
    """Response schema for news search results."""

    articles: List[ArticleResponse] = Field(..., description="List of articles")
    total: int = Field(..., description="Total number of articles returned")
    query: str = Field(..., description="Search query used")


class HeadlinesResponse(BaseModel):
    """Response schema for top headlines."""

    articles: List[ArticleResponse] = Field(..., description="List of headline articles")
    total: int = Field(..., description="Total number of headlines")
    category: str = Field(..., description="News category")
    country: str = Field(..., description="Country code")


class SentimentResult(BaseModel):
    """Sentiment analysis result for a single article."""

    article_id: Optional[str] = Field(None, description="Article identifier")
    title: Optional[str] = Field(None, description="Article title")
    sentiment: str = Field(..., description="Sentiment: positive, negative, or neutral")
    score: float = Field(..., description="Sentiment score (-1 to 1)")


class SentimentAnalysisResponse(BaseModel):
    """Response schema for sentiment analysis."""

    overall_sentiment: str = Field(..., description="Overall sentiment")
    sentiment_score: float = Field(..., description="Average sentiment score")
    positive_count: int = Field(..., description="Number of positive articles")
    negative_count: int = Field(..., description="Number of negative articles")
    neutral_count: int = Field(..., description="Number of neutral articles")
    article_sentiments: List[SentimentResult] = Field(
        ..., description="Per-article sentiment"
    )


class UsageStatusResponse(BaseModel):
    """Response schema for API usage status."""

    api_name: str = Field(..., description="API name")
    request_count: int = Field(..., description="Requests made in current period")
    quota_limit: Optional[int] = Field(None, description="Maximum allowed requests")
    quota_remaining: Optional[int] = Field(None, description="Remaining requests")
    usage_percentage: Optional[float] = Field(None, description="Percentage of quota used")
    is_exceeded: bool = Field(..., description="Whether quota is exceeded")
    period_start: Optional[str] = Field(None, description="Period start date")
    period_end: Optional[str] = Field(None, description="Period end date")


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")


# ----- Dependency -----

async def get_gnews_service(
    db: AsyncSession = Depends(get_db)
) -> GNewsService:
    """Dependency to get GNewsService instance.

    Args:
        db: Database session from dependency injection

    Returns:
        GNewsService instance
    """
    return GNewsService(db)


# ----- Endpoints -----

@router.get(
    "/search",
    response_model=NewsSearchResponse,
    summary="Search news articles",
    description="Search for news articles using keywords. Supports filtering by language, "
                "country, date range, and sorting options.",
    responses={
        200: {"description": "Successful search"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def search_news(
    q: str = Query(
        ...,
        min_length=1,
        max_length=500,
        description="Search query string"
    ),
    max_results: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of results (1-100)"
    ),
    language: str = Query(
        "en",
        min_length=2,
        max_length=5,
        description="Language code (e.g., 'en', 'es', 'fr')"
    ),
    country: Optional[str] = Query(
        None,
        min_length=2,
        max_length=2,
        description="Country code (e.g., 'us', 'gb')"
    ),
    from_date: Optional[datetime] = Query(
        None,
        description="Filter articles from this date (ISO format)"
    ),
    to_date: Optional[datetime] = Query(
        None,
        description="Filter articles to this date (ISO format)"
    ),
    sort_by: str = Query(
        "relevance",
        pattern="^(relevance|publishedAt)$",
        description="Sort by 'relevance' or 'publishedAt'"
    ),
    service: GNewsService = Depends(get_gnews_service)
) -> NewsSearchResponse:
    """Search for news articles.

    - **q**: Search query (required)
    - **max_results**: Maximum results to return (default: 10)
    - **language**: Filter by language code (default: "en")
    - **country**: Filter by country code (optional)
    - **from_date**: Filter articles after this date (optional)
    - **to_date**: Filter articles before this date (optional)
    - **sort_by**: Sort order - "relevance" or "publishedAt"
    """
    try:
        async with service:
            articles = await service.search_news(
                query=q,
                max_results=max_results,
                language=language,
                country=country,
                from_date=from_date,
                to_date=to_date,
                sort_by=sort_by
            )

            return NewsSearchResponse(
                articles=[ArticleResponse(**article) for article in articles],
                total=len(articles),
                query=q
            )

    except GNewsAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    except GNewsRateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=e.message,
            headers={"Retry-After": str(e.retry_after or 3600)}
        )
    except GNewsAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get(
    "/competitor/{competitor_id}",
    response_model=NewsSearchResponse,
    summary="Get competitor news",
    description="Retrieve news articles related to a specific competitor. "
                "Searches using the competitor's name and domain.",
    responses={
        200: {"description": "Successful retrieval"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        404: {"model": ErrorResponse, "description": "Competitor not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_competitor_news(
    competitor_id: int,
    days_back: int = Query(
        7,
        ge=1,
        le=30,
        description="Number of days to look back"
    ),
    max_results: int = Query(
        20,
        ge=1,
        le=100,
        description="Maximum number of results"
    ),
    service: GNewsService = Depends(get_gnews_service)
) -> NewsSearchResponse:
    """Get news articles for a competitor.

    - **competitor_id**: Database ID of the competitor
    - **days_back**: Number of days to search (default: 7, max: 30)
    - **max_results**: Maximum results to return (default: 20)
    """
    try:
        async with service:
            articles = await service.get_competitor_news(
                competitor_id=competitor_id,
                days_back=days_back,
                max_results=max_results
            )

            return NewsSearchResponse(
                articles=[ArticleResponse(**article) for article in articles],
                total=len(articles),
                query=f"competitor:{competitor_id}"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except GNewsAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    except GNewsRateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=e.message,
            headers={"Retry-After": str(e.retry_after or 3600)}
        )
    except GNewsAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get(
    "/headlines",
    response_model=HeadlinesResponse,
    summary="Get top headlines",
    description="Retrieve top news headlines by category and country.",
    responses={
        200: {"description": "Successful retrieval"},
        400: {"model": ErrorResponse, "description": "Invalid category"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_top_headlines(
    category: str = Query(
        "general",
        description="News category: general, world, nation, business, technology, "
                    "entertainment, sports, science, health"
    ),
    country: str = Query(
        "us",
        min_length=2,
        max_length=2,
        description="Country code (e.g., 'us', 'gb', 'ca')"
    ),
    max_results: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of results"
    ),
    language: str = Query(
        "en",
        min_length=2,
        max_length=5,
        description="Language code"
    ),
    service: GNewsService = Depends(get_gnews_service)
) -> HeadlinesResponse:
    """Get top news headlines.

    - **category**: News category (default: "general")
    - **country**: Country code (default: "us")
    - **max_results**: Maximum results (default: 10)
    - **language**: Language code (default: "en")
    """
    try:
        async with service:
            articles = await service.get_top_headlines(
                category=category,
                country=country,
                max_results=max_results,
                language=language
            )

            return HeadlinesResponse(
                articles=[ArticleResponse(**article) for article in articles],
                total=len(articles),
                category=category,
                country=country
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except GNewsAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    except GNewsRateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=e.message,
            headers={"Retry-After": str(e.retry_after or 3600)}
        )
    except GNewsAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post(
    "/analyze-sentiment",
    response_model=SentimentAnalysisResponse,
    summary="Analyze news sentiment",
    description="Perform sentiment analysis on a list of news articles.",
    responses={
        200: {"description": "Successful analysis"},
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def analyze_sentiment(
    articles: List[ArticleResponse],
    service: GNewsService = Depends(get_gnews_service)
) -> SentimentAnalysisResponse:
    """Analyze sentiment of news articles.

    Accepts a list of articles and returns sentiment analysis including
    overall sentiment, individual article scores, and summary statistics.
    """
    try:
        async with service:
            # Convert Pydantic models to dicts
            article_dicts = [article.model_dump() for article in articles]
            result = await service.analyze_news_sentiment(article_dicts)

            return SentimentAnalysisResponse(
                overall_sentiment=result["overall_sentiment"],
                sentiment_score=result["sentiment_score"],
                positive_count=result["positive_count"],
                negative_count=result["negative_count"],
                neutral_count=result["neutral_count"],
                article_sentiments=[
                    SentimentResult(**s) for s in result["article_sentiments"]
                ]
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment analysis failed: {str(e)}"
        )


@router.get(
    "/usage",
    response_model=UsageStatusResponse,
    summary="Get API usage status",
    description="Get current GNews API usage statistics and quota status.",
    responses={
        200: {"description": "Usage status retrieved"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_usage_status(
    service: GNewsService = Depends(get_gnews_service)
) -> UsageStatusResponse:
    """Get current API usage status.

    Returns request count, quota information, and remaining allowance
    for the current billing period.
    """
    try:
        async with service:
            status = await service.get_usage_status()
            return UsageStatusResponse(**status)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage status: {str(e)}"
        )
