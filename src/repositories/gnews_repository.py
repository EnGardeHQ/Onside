"""GNews Repository Module.

This module provides database operations for GNews article entities.
Handles storage, retrieval, and cleanup of news articles from the GNews API.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.external_api import GNewsArticle


class GNewsRepository:
    """Repository for GNews article database operations.

    Provides methods for storing and retrieving news articles
    fetched from the GNews API for competitor monitoring.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def create_article(self, article: GNewsArticle) -> GNewsArticle:
        """Store a news article in the database.

        Args:
            article: GNewsArticle instance to store

        Returns:
            Created GNewsArticle with populated ID
        """
        self.db.add(article)
        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def create_articles_batch(
        self, articles: List[GNewsArticle]
    ) -> List[GNewsArticle]:
        """Batch insert multiple news articles.

        Args:
            articles: List of GNewsArticle instances to store

        Returns:
            List of created GNewsArticle instances with populated IDs
        """
        if not articles:
            return []

        self.db.add_all(articles)
        await self.db.commit()

        for article in articles:
            await self.db.refresh(article)

        return articles

    async def get_by_id(self, article_id: int) -> Optional[GNewsArticle]:
        """Get an article by its database ID.

        Args:
            article_id: Database ID of the article

        Returns:
            GNewsArticle if found, None otherwise
        """
        result = await self.db.execute(
            select(GNewsArticle).where(GNewsArticle.id == article_id)
        )
        return result.scalar_one_or_none()

    async def get_by_article_id(self, article_id: str) -> Optional[GNewsArticle]:
        """Get an article by its GNews API article ID.

        Args:
            article_id: GNews API article identifier

        Returns:
            GNewsArticle if found, None otherwise
        """
        result = await self.db.execute(
            select(GNewsArticle).where(GNewsArticle.article_id == article_id)
        )
        return result.scalar_one_or_none()

    async def get_articles_by_competitor(
        self,
        competitor_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[GNewsArticle]:
        """Get articles associated with a specific competitor.

        Args:
            competitor_id: ID of the competitor
            start_date: Optional start of date range filter
            end_date: Optional end of date range filter
            limit: Maximum number of articles to return

        Returns:
            List of GNewsArticle instances matching the criteria
        """
        query = select(GNewsArticle).where(
            GNewsArticle.competitor_id == competitor_id
        )

        if start_date:
            query = query.where(GNewsArticle.published_at >= start_date)
        if end_date:
            query = query.where(GNewsArticle.published_at <= end_date)

        query = query.order_by(GNewsArticle.published_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_articles_by_query(
        self,
        query_term: str,
        limit: int = 100
    ) -> List[GNewsArticle]:
        """Get articles by search query term.

        Args:
            query_term: The search query used to fetch articles
            limit: Maximum number of articles to return

        Returns:
            List of GNewsArticle instances matching the query term
        """
        result = await self.db.execute(
            select(GNewsArticle)
            .where(GNewsArticle.query_term == query_term)
            .order_by(GNewsArticle.published_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_articles(
        self,
        competitor_id: int,
        limit: int = 10
    ) -> List[GNewsArticle]:
        """Get the most recent articles for a competitor.

        Args:
            competitor_id: ID of the competitor
            limit: Maximum number of articles to return (default: 10)

        Returns:
            List of most recent GNewsArticle instances
        """
        result = await self.db.execute(
            select(GNewsArticle)
            .where(GNewsArticle.competitor_id == competitor_id)
            .order_by(GNewsArticle.published_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_old_articles(self, days_old: int) -> int:
        """Delete articles older than the specified number of days.

        Args:
            days_old: Delete articles older than this many days

        Returns:
            Number of deleted articles
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        result = await self.db.execute(
            delete(GNewsArticle).where(
                GNewsArticle.published_at < cutoff_date
            )
        )
        await self.db.commit()

        return result.rowcount

    async def delete_by_id(self, article_id: int) -> bool:
        """Delete an article by its database ID.

        Args:
            article_id: Database ID of the article to delete

        Returns:
            True if article was deleted, False if not found
        """
        result = await self.db.execute(
            delete(GNewsArticle).where(GNewsArticle.id == article_id)
        )
        await self.db.commit()

        return result.rowcount > 0

    async def get_articles_by_source(
        self,
        source_name: str,
        limit: int = 100
    ) -> List[GNewsArticle]:
        """Get articles from a specific news source.

        Args:
            source_name: Name of the news source
            limit: Maximum number of articles to return

        Returns:
            List of GNewsArticle instances from the source
        """
        result = await self.db.execute(
            select(GNewsArticle)
            .where(GNewsArticle.source_name == source_name)
            .order_by(GNewsArticle.published_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_articles_by_competitor(
        self,
        competitor_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Count articles for a competitor within a date range.

        Args:
            competitor_id: ID of the competitor
            start_date: Optional start of date range
            end_date: Optional end of date range

        Returns:
            Number of articles matching the criteria
        """
        from sqlalchemy import func

        query = select(func.count(GNewsArticle.id)).where(
            GNewsArticle.competitor_id == competitor_id
        )

        if start_date:
            query = query.where(GNewsArticle.published_at >= start_date)
        if end_date:
            query = query.where(GNewsArticle.published_at <= end_date)

        result = await self.db.execute(query)
        return result.scalar() or 0
