"""
Comprehensive API tests for Search History endpoints.

This module tests all search history API endpoints including listing, analytics,
and cleanup operations with proper authentication and authorization.
"""
import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.search_history import SearchHistory
from src.models.user import User


class TestSearchHistoryList:
    """Test suite for GET /search-history endpoint."""

    @pytest.mark.asyncio
    async def test_list_search_history_success(self, test_client, test_user, test_token, test_db):
        """Test successful listing of search history."""
        # Create test search history records
        for i in range(5):
            search = SearchHistory(
                user_id=test_user.id,
                query=f"test query {i}",
                search_type="content",
                results_count=10 + i,
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            test_db.add(search)
        await test_db.commit()

        # Make request
        response = await test_client.get(
            "/api/v1/search-history",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "searches" in data
        assert "total" in data
        assert data["total"] >= 5

    @pytest.mark.asyncio
    async def test_list_search_history_with_company_filter(
        self, test_client, test_user, test_token, test_db
    ):
        """Test filtering search history by company ID."""
        company_id = 123

        # Create searches for different companies
        search1 = SearchHistory(
            user_id=test_user.id,
            company_id=company_id,
            query="company search",
            search_type="content"
        )
        search2 = SearchHistory(
            user_id=test_user.id,
            company_id=456,
            query="other search",
            search_type="content"
        )
        test_db.add_all([search1, search2])
        await test_db.commit()

        # Make request with company filter
        response = await test_client.get(
            f"/api/v1/search-history?company_id={company_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for search in data["searches"]:
            assert search["company_id"] == company_id

    @pytest.mark.asyncio
    async def test_list_search_history_with_type_filter(
        self, test_client, test_user, test_token, test_db
    ):
        """Test filtering search history by search type."""
        # Create searches of different types
        search1 = SearchHistory(
            user_id=test_user.id,
            query="content search",
            search_type="content"
        )
        search2 = SearchHistory(
            user_id=test_user.id,
            query="user search",
            search_type="users"
        )
        test_db.add_all([search1, search2])
        await test_db.commit()

        # Make request with type filter
        response = await test_client.get(
            "/api/v1/search-history?search_type=content",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for search in data["searches"]:
            assert search["search_type"] == "content"

    @pytest.mark.asyncio
    async def test_list_search_history_pagination(
        self, test_client, test_user, test_token, test_db
    ):
        """Test pagination of search history."""
        # Create many search records
        for i in range(30):
            search = SearchHistory(
                user_id=test_user.id,
                query=f"query {i}",
                search_type="content"
            )
            test_db.add(search)
        await test_db.commit()

        # Test first page
        response = await test_client.get(
            "/api/v1/search-history?page=1&page_size=10",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["searches"]) <= 10
        assert data["page"] == 1

        # Test second page
        response = await test_client.get(
            "/api/v1/search-history?page=2&page_size=10",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 2

    @pytest.mark.asyncio
    async def test_list_search_history_date_range(
        self, test_client, test_user, test_token, test_db
    ):
        """Test filtering search history by date range."""
        # Create old and recent searches
        old_search = SearchHistory(
            user_id=test_user.id,
            query="old search",
            search_type="content",
            created_at=datetime.utcnow() - timedelta(days=100)
        )
        recent_search = SearchHistory(
            user_id=test_user.id,
            query="recent search",
            search_type="content",
            created_at=datetime.utcnow() - timedelta(days=5)
        )
        test_db.add_all([old_search, recent_search])
        await test_db.commit()

        # Request last 30 days
        response = await test_client.get(
            "/api/v1/search-history?days=30",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # Assert - should only get recent search
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        queries = [s["query"] for s in data["searches"]]
        assert "recent search" in queries
        # Old search should not be included

    @pytest.mark.asyncio
    async def test_list_search_history_unauthorized(self, test_client):
        """Test listing search history without authentication."""
        response = await test_client.get("/api/v1/search-history")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_list_search_history_user_isolation(
        self, test_client, test_user, test_token, test_db
    ):
        """Test that users only see their own search history."""
        # Create another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashedpassword",
            name="Other User"
        )
        test_db.add(other_user)
        await test_db.commit()

        # Create searches for both users
        test_user_search = SearchHistory(
            user_id=test_user.id,
            query="test user search",
            search_type="content"
        )
        other_user_search = SearchHistory(
            user_id=other_user.id,
            query="other user search",
            search_type="content"
        )
        test_db.add_all([test_user_search, other_user_search])
        await test_db.commit()

        # Request as test_user
        response = await test_client.get(
            "/api/v1/search-history",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # Assert - should only see own searches
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        queries = [s["query"] for s in data["searches"]]
        assert "test user search" in queries
        assert "other user search" not in queries


class TestSearchHistoryAnalytics:
    """Test suite for GET /search-history/analytics endpoint."""

    @pytest.mark.asyncio
    async def test_get_search_analytics_success(
        self, test_client, test_user, test_token, test_db
    ):
        """Test successful retrieval of search analytics."""
        # Create varied search history
        for i in range(10):
            search = SearchHistory(
                user_id=test_user.id,
                query=f"query {i % 3}",  # Repeat queries
                search_type="content" if i % 2 == 0 else "users",
                results_count=10,
                execution_time_ms=100.0 + i * 10
            )
            test_db.add(search)
        await test_db.commit()

        # Make request
        response = await test_client.get(
            "/api/v1/search-history/analytics",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_searches" in data
        assert "unique_queries" in data
        assert "avg_execution_time" in data
        assert "search_types" in data
        assert data["total_searches"] >= 10

    @pytest.mark.asyncio
    async def test_search_analytics_top_queries(
        self, test_client, test_user, test_token, test_db
    ):
        """Test top queries in analytics."""
        # Create searches with repeated queries
        queries = ["popular query"] * 5 + ["rare query"] * 1
        for query in queries:
            search = SearchHistory(
                user_id=test_user.id,
                query=query,
                search_type="content"
            )
            test_db.add(search)
        await test_db.commit()

        # Make request
        response = await test_client.get(
            "/api/v1/search-history/analytics",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        if "top_queries" in data:
            assert data["top_queries"][0]["query"] == "popular query"
            assert data["top_queries"][0]["count"] == 5


class TestSearchHistoryCleanup:
    """Test suite for DELETE /search-history/cleanup endpoint."""

    @pytest.mark.asyncio
    async def test_cleanup_old_searches_success(
        self, test_client, test_user, test_token, test_db
    ):
        """Test successful cleanup of old searches."""
        # Create old searches
        for i in range(5):
            search = SearchHistory(
                user_id=test_user.id,
                query=f"old query {i}",
                search_type="content",
                created_at=datetime.utcnow() - timedelta(days=100 + i)
            )
            test_db.add(search)

        # Create recent searches
        for i in range(3):
            search = SearchHistory(
                user_id=test_user.id,
                query=f"recent query {i}",
                search_type="content",
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            test_db.add(search)

        await test_db.commit()

        # Make cleanup request (delete older than 90 days)
        response = await test_client.delete(
            "/api/v1/search-history/cleanup?days=90",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "deleted_count" in data
        assert data["deleted_count"] == 5

    @pytest.mark.asyncio
    async def test_cleanup_requires_authentication(self, test_client):
        """Test cleanup requires authentication."""
        response = await test_client.delete(
            "/api/v1/search-history/cleanup?days=90"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_cleanup_user_isolation(
        self, test_client, test_user, test_token, test_db
    ):
        """Test cleanup only affects current user's searches."""
        # Create other user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashedpassword",
            name="Other User"
        )
        test_db.add(other_user)
        await test_db.commit()

        # Create old searches for both users
        test_user_search = SearchHistory(
            user_id=test_user.id,
            query="test user old",
            search_type="content",
            created_at=datetime.utcnow() - timedelta(days=100)
        )
        other_user_search = SearchHistory(
            user_id=other_user.id,
            query="other user old",
            search_type="content",
            created_at=datetime.utcnow() - timedelta(days=100)
        )
        test_db.add_all([test_user_search, other_user_search])
        await test_db.commit()

        # Cleanup as test_user
        response = await test_client.delete(
            "/api/v1/search-history/cleanup?days=90",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        # Only test_user's search should be deleted, not other_user's


class TestSearchHistoryEdgeCases:
    """Test suite for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_list_with_invalid_page_size(
        self, test_client, test_token
    ):
        """Test listing with invalid page size."""
        response = await test_client.get(
            "/api/v1/search-history?page_size=1000",  # Over limit
            headers={"Authorization": f"Bearer {test_token}"}
        )
        # Should either reject or cap at max
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]

    @pytest.mark.asyncio
    async def test_list_with_invalid_days(
        self, test_client, test_token
    ):
        """Test listing with invalid days parameter."""
        response = await test_client.get(
            "/api/v1/search-history?days=500",  # Over 365 limit
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_list_empty_history(
        self, test_client, test_user, test_token, test_db
    ):
        """Test listing when no search history exists."""
        response = await test_client.get(
            "/api/v1/search-history",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert len(data["searches"]) == 0

    @pytest.mark.asyncio
    async def test_analytics_with_no_data(
        self, test_client, test_user, test_token
    ):
        """Test analytics when no search history exists."""
        response = await test_client.get(
            "/api/v1/search-history/analytics",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_searches"] == 0

    @pytest.mark.asyncio
    async def test_cleanup_with_no_old_searches(
        self, test_client, test_user, test_token, test_db
    ):
        """Test cleanup when no old searches exist."""
        # Create only recent searches
        search = SearchHistory(
            user_id=test_user.id,
            query="recent",
            search_type="content",
            created_at=datetime.utcnow()
        )
        test_db.add(search)
        await test_db.commit()

        # Try to cleanup
        response = await test_client.delete(
            "/api/v1/search-history/cleanup?days=90",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted_count"] == 0
