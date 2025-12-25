"""
Competitor News API endpoints for OnSide application.

This module provides endpoints for competitor news analysis including
sentiment analysis, topic extraction, trends, and cross-competitor comparison.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Config
# Import from database package (not src/database.py module)
from src.database import get_db
from src.schemas.competitor_news import (
    CompetitorNewsResponse,
    NewsSentimentAnalysisResponse,
    NewsTrendsResponse,
    NewsComparisonResponse,
    NewsRefreshRequest,
    NewsRefreshResponse,
    NewsArticleResponse,
    NewsSentimentScore,
    SentimentCategory,
    TopicFrequency,
    SourceDiversity,
    CompetitorNewsComparisonItem,
    NewsVolumeDataPoint,
)
from src.services.analytics.enhanced_competitor_analysis import (
    EnhancedCompetitorAnalysisService
)
from src.repositories.gnews_repository import GNewsRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/competitors", tags=["competitor-news"])


def get_config() -> Config:
    """Get application configuration."""
    return Config()


def get_enhanced_analysis_service(
    config: Config = Depends(get_config)
) -> EnhancedCompetitorAnalysisService:
    """Get enhanced competitor analysis service instance."""
    return EnhancedCompetitorAnalysisService(config)


@router.get(
    "/{competitor_id}/news",
    response_model=CompetitorNewsResponse,
    summary="Get competitor news articles",
    description="Retrieve news articles for a specific competitor with optional sentiment analysis."
)
async def get_competitor_news(
    competitor_id: int,
    days_back: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Number of days to look back for news articles"
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of articles to return"
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Offset for pagination"
    ),
    include_sentiment: bool = Query(
        default=True,
        description="Include sentiment analysis for each article"
    ),
    source: Optional[str] = Query(
        default=None,
        description="Filter articles by news source"
    ),
    db: AsyncSession = Depends(get_db),
    service: EnhancedCompetitorAnalysisService = Depends(get_enhanced_analysis_service)
) -> CompetitorNewsResponse:
    """Get news articles for a specific competitor.

    Retrieves news articles associated with the specified competitor,
    with optional sentiment analysis and filtering capabilities.

    Args:
        competitor_id: ID of the competitor
        days_back: Number of days to look back (1-365)
        limit: Maximum articles to return (1-500)
        offset: Pagination offset
        include_sentiment: Whether to include sentiment analysis
        source: Filter by news source name
        db: Database session
        service: Enhanced analysis service

    Returns:
        CompetitorNewsResponse with articles and metadata

    Raises:
        HTTPException: 404 if competitor not found, 500 on internal error
    """
    try:
        # Get enriched data which includes articles
        enriched_data = await service.enrich_with_news(
            session=db,
            competitor_id=competitor_id,
            days_back=days_back
        )

        # Get articles from repository for full data
        gnews_repo = GNewsRepository(db)
        from datetime import datetime, timedelta
        start_date = datetime.utcnow() - timedelta(days=days_back)

        articles = await gnews_repo.get_articles_by_competitor(
            competitor_id=competitor_id,
            start_date=start_date,
            limit=limit + offset  # Get enough for pagination
        )

        # Apply source filter if specified
        if source:
            articles = [a for a in articles if a.source_name.lower() == source.lower()]

        # Apply pagination
        articles = articles[offset:offset + limit]

        # Convert to response format
        article_responses = []
        for article in articles:
            sentiment = None
            if include_sentiment:
                # Get sentiment from enriched data or calculate
                text = f"{article.title} {article.description or ''}"
                from textblob import TextBlob
                blob = TextBlob(text)
                score = blob.sentiment.polarity

                sentiment = NewsSentimentScore(
                    score=round(score, 4),
                    category=_categorize_sentiment(score),
                    confidence=round(abs(score) * 0.5 + 0.5, 4)
                )

            article_responses.append(
                NewsArticleResponse(
                    id=article.id,
                    article_id=article.article_id,
                    title=article.title,
                    description=article.description,
                    url=article.url,
                    image_url=article.image_url,
                    published_at=article.published_at,
                    source_name=article.source_name,
                    source_url=article.source_url,
                    query_term=article.query_term,
                    language=article.language,
                    country=article.country,
                    sentiment=sentiment
                )
            )

        return CompetitorNewsResponse(
            competitor_id=competitor_id,
            competitor_name=enriched_data.get("competitor_name", ""),
            total_articles=enriched_data.get("news_coverage", {}).get("total_articles", 0),
            articles=article_responses,
            date_range={
                "start": start_date,
                "end": datetime.utcnow()
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting competitor news: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving competitor news"
        )


@router.get(
    "/{competitor_id}/news/sentiment",
    response_model=NewsSentimentAnalysisResponse,
    summary="Analyze news sentiment for competitor",
    description="Get detailed sentiment analysis of news coverage for a competitor."
)
async def get_news_sentiment_analysis(
    competitor_id: int,
    days_back: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Number of days to analyze"
    ),
    db: AsyncSession = Depends(get_db),
    service: EnhancedCompetitorAnalysisService = Depends(get_enhanced_analysis_service)
) -> NewsSentimentAnalysisResponse:
    """Analyze sentiment of news coverage for a competitor.

    Performs comprehensive sentiment analysis on news articles,
    including distribution, trends, and identification of key
    positive and negative articles.

    Args:
        competitor_id: ID of the competitor
        days_back: Number of days to analyze (1-365)
        db: Database session
        service: Enhanced analysis service

    Returns:
        NewsSentimentAnalysisResponse with detailed sentiment analysis

    Raises:
        HTTPException: 404 if competitor not found, 500 on internal error
    """
    try:
        result = await service.analyze_news_sentiment(
            session=db,
            competitor_id=competitor_id,
            days_back=days_back
        )

        # Convert to response model
        return NewsSentimentAnalysisResponse(
            competitor_id=result["competitor_id"],
            competitor_name=result["competitor_name"],
            analysis_period=_parse_date_range(result.get("analysis_period", {})),
            overall_sentiment=NewsSentimentScore(
                score=result["overall_sentiment"]["score"],
                category=SentimentCategory(result["overall_sentiment"]["category"]),
                confidence=result["overall_sentiment"]["confidence"]
            ),
            article_count=result["article_count"],
            sentiment_distribution=result.get("sentiment_distribution", {}),
            top_positive_articles=[
                _convert_article_response(a) for a in result.get("top_positive_articles", [])
            ],
            top_negative_articles=[
                _convert_article_response(a) for a in result.get("top_negative_articles", [])
            ],
            sentiment_trend=result.get("sentiment_trend", []),
            key_topics=[
                TopicFrequency(
                    topic=t["topic"],
                    count=t["count"],
                    percentage=t.get("percentage", 0.0)
                )
                for t in result.get("key_topics", [])
            ]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error analyzing news sentiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while analyzing news sentiment"
        )


@router.get(
    "/{competitor_id}/news/trends",
    response_model=NewsTrendsResponse,
    summary="Get news trends for competitor",
    description="Analyze news coverage trends including volume, topics, and source diversity."
)
async def get_news_trends(
    competitor_id: int,
    days_back: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Number of days to analyze"
    ),
    db: AsyncSession = Depends(get_db),
    service: EnhancedCompetitorAnalysisService = Depends(get_enhanced_analysis_service)
) -> NewsTrendsResponse:
    """Get news coverage trends for a competitor.

    Analyzes patterns in news coverage including volume trends,
    trending topics, emerging topics, and source diversity.

    Args:
        competitor_id: ID of the competitor
        days_back: Number of days to analyze (1-365)
        db: Database session
        service: Enhanced analysis service

    Returns:
        NewsTrendsResponse with trend analysis

    Raises:
        HTTPException: 404 if competitor not found, 500 on internal error
    """
    try:
        result = await service.get_news_trends(
            session=db,
            competitor_id=competitor_id,
            days_back=days_back
        )

        # Convert to response model
        return NewsTrendsResponse(
            competitor_id=result["competitor_id"],
            competitor_name=result["competitor_name"],
            analysis_period=_parse_date_range(result.get("analysis_period", {})),
            total_articles=result["total_articles"],
            volume_trend=[
                NewsVolumeDataPoint(
                    date=_parse_date(d["date"]),
                    article_count=d["article_count"],
                    average_sentiment=d.get("average_sentiment")
                )
                for d in result.get("volume_trend", [])
            ],
            volume_change_percentage=result.get("volume_change_percentage", 0.0),
            trending_topics=[
                TopicFrequency(
                    topic=t["topic"],
                    count=t["count"],
                    percentage=t.get("percentage", 0.0)
                )
                for t in result.get("trending_topics", [])
            ],
            emerging_topics=[
                TopicFrequency(
                    topic=t["topic"],
                    count=t["count"],
                    percentage=t.get("percentage", 0.0)
                )
                for t in result.get("emerging_topics", [])
            ],
            source_diversity=[
                SourceDiversity(
                    source_name=s["source_name"],
                    article_count=s["article_count"],
                    percentage=s.get("percentage", 0.0),
                    average_sentiment=s.get("average_sentiment")
                )
                for s in result.get("source_diversity", [])
            ],
            peak_coverage_dates=result.get("peak_coverage_dates", [])
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting news trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while analyzing news trends"
        )


@router.post(
    "/{competitor_id}/news/refresh",
    response_model=NewsRefreshResponse,
    summary="Refresh competitor news data",
    description="Trigger a refresh of news data for a competitor from external sources."
)
async def refresh_competitor_news(
    competitor_id: int,
    request: Optional[NewsRefreshRequest] = None,
    db: AsyncSession = Depends(get_db),
    service: EnhancedCompetitorAnalysisService = Depends(get_enhanced_analysis_service)
) -> NewsRefreshResponse:
    """Refresh news data for a competitor.

    Triggers fetching of new articles from external news sources
    and optionally analyzes sentiment for the new articles.

    Args:
        competitor_id: ID of the competitor
        request: Optional refresh configuration
        db: Database session
        service: Enhanced analysis service

    Returns:
        NewsRefreshResponse with refresh operation results

    Raises:
        HTTPException: 404 if competitor not found, 500 on internal error
    """
    try:
        # Use defaults if no request body provided
        days_back = request.days_back if request else 30
        analyze_sentiment = request.include_sentiment if request else True

        result = await service.refresh_competitor_news(
            session=db,
            competitor_id=competitor_id,
            days_back=days_back,
            analyze_sentiment=analyze_sentiment
        )

        return NewsRefreshResponse(
            competitor_id=result["competitor_id"],
            competitor_name=result["competitor_name"],
            articles_fetched=result.get("articles_fetched", 0),
            articles_updated=result.get("articles_updated", 0),
            total_articles=result.get("total_articles", 0),
            fetch_date_range={
                "start": _parse_date(result["fetch_date_range"]["start"]),
                "end": _parse_date(result["fetch_date_range"]["end"])
            },
            status=result.get("status", "success"),
            errors=result.get("errors", [])
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error refreshing competitor news: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while refreshing competitor news"
        )


@router.get(
    "/news/compare",
    response_model=NewsComparisonResponse,
    summary="Compare news coverage across competitors",
    description="Compare news coverage, sentiment, and topics across multiple competitors."
)
async def compare_competitor_news(
    competitor_ids: str = Query(
        ...,
        description="Comma-separated list of competitor IDs to compare"
    ),
    days_back: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Number of days to analyze"
    ),
    db: AsyncSession = Depends(get_db),
    service: EnhancedCompetitorAnalysisService = Depends(get_enhanced_analysis_service)
) -> NewsComparisonResponse:
    """Compare news coverage across multiple competitors.

    Analyzes and compares news coverage, sentiment, share of voice,
    and topics across specified competitors.

    Args:
        competitor_ids: Comma-separated competitor IDs
        days_back: Number of days to analyze (1-365)
        db: Database session
        service: Enhanced analysis service

    Returns:
        NewsComparisonResponse with comparative analysis

    Raises:
        HTTPException: 400 for invalid IDs, 404 if no competitors found, 500 on error
    """
    try:
        # Parse competitor IDs
        try:
            ids = [int(id.strip()) for id in competitor_ids.split(",") if id.strip()]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid competitor IDs. Please provide comma-separated integers."
            )

        if not ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one competitor ID is required"
            )

        result = await service.compare_news_coverage(
            session=db,
            competitor_ids=ids,
            days_back=days_back
        )

        # Convert to response model
        return NewsComparisonResponse(
            analysis_period=_parse_date_range(result.get("analysis_period", {})),
            total_articles=result["total_articles"],
            competitors=[
                CompetitorNewsComparisonItem(
                    competitor_id=c["competitor_id"],
                    competitor_name=c["competitor_name"],
                    article_count=c["article_count"],
                    share_of_voice=c.get("share_of_voice", 0.0),
                    average_sentiment=c["average_sentiment"],
                    sentiment_category=SentimentCategory(c["sentiment_category"]),
                    top_sources=c.get("top_sources", []),
                    top_topics=c.get("top_topics", [])
                )
                for c in result.get("competitors", [])
            ],
            coverage_leader=result.get("coverage_leader"),
            sentiment_leader=result.get("sentiment_leader"),
            insights=result.get("insights", [])
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing competitor news: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while comparing competitor news"
        )


# Helper functions

def _categorize_sentiment(score: float) -> SentimentCategory:
    """Categorize a sentiment score."""
    if score > 0.1:
        return SentimentCategory.POSITIVE
    elif score < -0.1:
        return SentimentCategory.NEGATIVE
    return SentimentCategory.NEUTRAL


def _parse_date(date_value) -> "datetime":
    """Parse date from various formats."""
    from datetime import datetime

    if isinstance(date_value, datetime):
        return date_value
    if isinstance(date_value, str):
        try:
            return datetime.fromisoformat(date_value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.utcnow()
    return datetime.utcnow()


def _parse_date_range(date_range: dict) -> dict:
    """Parse date range dictionary."""
    from datetime import datetime

    return {
        "start": _parse_date(date_range.get("start")) if date_range.get("start") else None,
        "end": _parse_date(date_range.get("end")) if date_range.get("end") else None
    }


def _convert_article_response(article_dict: dict) -> NewsArticleResponse:
    """Convert article dictionary to response model."""
    sentiment = None
    if article_dict.get("sentiment"):
        sentiment = NewsSentimentScore(
            score=article_dict["sentiment"]["score"],
            category=SentimentCategory(article_dict["sentiment"]["category"]),
            confidence=article_dict["sentiment"]["confidence"]
        )

    return NewsArticleResponse(
        id=article_dict["id"],
        article_id=article_dict["article_id"],
        title=article_dict["title"],
        description=article_dict.get("description"),
        url=article_dict["url"],
        image_url=article_dict.get("image_url"),
        published_at=_parse_date(article_dict["published_at"]),
        source_name=article_dict["source_name"],
        source_url=article_dict.get("source_url"),
        query_term=article_dict.get("query_term"),
        language=article_dict.get("language"),
        country=article_dict.get("country"),
        sentiment=sentiment
    )
