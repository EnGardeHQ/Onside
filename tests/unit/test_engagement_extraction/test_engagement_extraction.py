"""Tests for the EngagementExtractionService."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
import numpy as np

from src.services.engagement_extraction.engagement_extraction import EngagementExtractionService

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db

@pytest.fixture
def engagement_service(mock_db):
    """Create an EngagementExtractionService with a mock database session."""
    return EngagementExtractionService(mock_db)

class TestEngagementExtractionService:
    """Tests for the EngagementExtractionService."""

    @patch('src.services.engagement_extraction.engagement_extraction.select')
    async def test_extract_engagement_metrics(self, mock_select, engagement_service, mock_db):
        """Test extracting engagement metrics for a link."""
        # Mock link
        mock_link = MagicMock()
        mock_link.id = 1
        mock_link.url = "https://example.com"
        mock_link.engagement_score = None
        
        # Mock snapshot
        mock_snapshot = MagicMock()
        mock_snapshot.id = 1
        mock_snapshot.link_id = 1
        mock_snapshot.html_content = """
        <html>
        <body>
            <div class="social">
                <span class="likes">42 likes</span>
                <span class="shares">10 shares</span>
                <span class="comments">5 comments</span>
            </div>
        </body>
        </html>
        """
        mock_snapshot.engagement_metrics = {
            "likes": 42,
            "shares": 10,
            "comments": 5
        }
        
        # Mock _get_link method
        engagement_service._get_link = AsyncMock(return_value=mock_link)
        
        # Mock _get_latest_snapshot method
        engagement_service._get_latest_snapshot = AsyncMock(return_value=mock_snapshot)
        
        # Mock _store_engagement_metrics method
        engagement_service._store_engagement_metrics = AsyncMock()
        
        # Call the method
        result = await engagement_service.extract_engagement_metrics(1)
        
        # Check result
        assert result is not None
        assert "metrics" in result
        assert "score" in result
        assert result["metrics"]["likes"] == 42
        assert result["metrics"]["shares"] == 10
        assert result["metrics"]["comments"] == 5
        
        # Verify that the link engagement score was updated
        assert mock_link.engagement_score is not None
        
        # Verify that the database was committed
        assert mock_db.commit.await_count == 1
        
        # Verify that _store_engagement_metrics was called
        engagement_service._store_engagement_metrics.assert_awaited_once_with(1, mock_snapshot.engagement_metrics)

    @patch('src.services.engagement_extraction.engagement_extraction.select')
    async def test_extract_engagement_for_links(self, mock_select, engagement_service):
        """Test extracting engagement metrics for multiple links."""
        # Mock extract_engagement_for_link method
        mock_link1 = MagicMock()
        mock_link1.id = 1
        mock_link1.engagement_score = 75.0
        
        mock_link2 = MagicMock()
        mock_link2.id = 2
        mock_link2.engagement_score = 85.0
        
        mock_error = {"error": "No snapshot found"}
        
        engagement_service.extract_engagement_for_link = AsyncMock(side_effect=[
            (mock_link1, None),
            (None, mock_error),
            (mock_link2, None)
        ])
        
        # Call the method
        links, errors = await engagement_service.extract_engagement_for_links([1, 2, 3])
        
        # Check results
        assert len(links) == 2
        assert len(errors) == 1
        assert links[0].id == 1
        assert links[1].id == 2
        assert errors[0]["error"] == "No snapshot found"
        assert errors[0]["link_id"] == 2
        
        # Verify that extract_engagement_for_link was called for each link ID
        assert engagement_service.extract_engagement_for_link.await_count == 3

    @patch('src.services.engagement_extraction.engagement_extraction.select')
    async def test_extract_engagement_for_domain(self, mock_select, engagement_service):
        """Test extracting engagement metrics for all links of a domain."""
        # Mock domain
        mock_domain = MagicMock()
        mock_domain.id = 1
        mock_domain.domain_name = "example.com"
        
        # Mock links
        mock_link1 = MagicMock()
        mock_link1.id = 1
        
        mock_link2 = MagicMock()
        mock_link2.id = 2
        
        # Mock _get_domain method
        engagement_service._get_domain = AsyncMock(return_value=mock_domain)
        
        # Mock _get_links_for_domain method
        engagement_service._get_links_for_domain = AsyncMock(return_value=[mock_link1, mock_link2])
        
        # Mock extract_engagement_for_links method
        processed_link1 = MagicMock()
        processed_link1.id = 1
        processed_link1.engagement_score = 75.0
        
        processed_link2 = MagicMock()
        processed_link2.id = 2
        processed_link2.engagement_score = 85.0
        
        engagement_service.extract_engagement_for_links = AsyncMock(return_value=(
            [processed_link1, processed_link2],
            []
        ))
        
        # Call the method
        result = await engagement_service.extract_engagement_for_domain(1)
        
        # Check result
        assert result["success"] is True
        assert result["links_processed"] == 2
        assert result["successful"] == 2
        assert result["failed"] == 0
        assert result["average_engagement_score"] == 80.0  # (75 + 85) / 2
        assert len(result["links"]) == 2
        assert len(result["errors"]) == 0
        
        # Verify that extract_engagement_for_links was called with the correct link IDs
        engagement_service.extract_engagement_for_links.assert_awaited_once_with([1, 2])

    @patch('src.services.engagement_extraction.engagement_extraction.select')
    async def test_extract_engagement_for_link(self, mock_select, engagement_service, mock_db):
        """Test extracting engagement metrics for a link."""
        # Mock link
        mock_link = MagicMock()
        mock_link.id = 1
        mock_link.url = "https://example.com"
        mock_link.engagement_score = None
        
        # Mock snapshot
        mock_snapshot = MagicMock()
        mock_snapshot.id = 1
        mock_snapshot.link_id = 1
        mock_snapshot.html_content = """
        <html>
        <body>
            <div class="social">
                <span class="likes">42 likes</span>
                <span class="shares">10 shares</span>
                <span class="comments">5 comments</span>
            </div>
        </body>
        </html>
        """
        
        # Mock _get_link method
        engagement_service._get_link = AsyncMock(return_value=mock_link)
        
        # Mock _get_latest_snapshot method
        engagement_service._get_latest_snapshot = AsyncMock(return_value=mock_snapshot)
        
        # Mock _extract_metrics method
        engagement_service._extract_metrics = MagicMock(return_value={
            "likes": 42,
            "shares": 10,
            "comments": 5
        })
        
        # Call the method
        link, error = await engagement_service.extract_engagement_for_link(1)
        
        # Check results
        assert link is not None
        assert error is None
        assert link.id == 1
        assert link.engagement_score is not None
        
        # Verify that the database was committed
        assert mock_db.commit.await_count == 1
        
        # Verify that _extract_metrics was called with the snapshot HTML content
        engagement_service._extract_metrics.assert_called_once_with(mock_snapshot.html_content)

    def test_extract_social_signals(self, engagement_service):
        """Test extracting social signals from HTML content."""
        html_content = """
        <html>
        <body>
            <div class="social">
                <span class="likes">42 likes</span>
                <span class="shares">10 shares</span>
                <span class="comments">5 comments</span>
            </div>
        </body>
        </html>
        """
        
        total_signals = engagement_service._extract_social_signals(html_content)
        
        # The method should extract 42 + 10 + 5 = 57 signals
        assert total_signals == 57

    def test_extract_metrics(self, engagement_service):
        """Test extracting engagement metrics from HTML content."""
        html_content = """
        <html>
        <body>
            <div class="social">
                <span class="likes">42 likes</span>
                <span class="shares">10 shares</span>
                <span class="comments">5 comments</span>
                <span class="reactions">15 reactions</span>
            </div>
        </body>
        </html>
        """
        
        metrics = engagement_service._extract_metrics(html_content)
        
        assert metrics["likes"] == 42
        assert metrics["shares"] == 10
        assert metrics["comments"] == 5
        assert metrics["reactions"] == 15

    def test_calculate_engagement_score(self, engagement_service):
        """Test calculating an engagement score from metrics."""
        metrics = {
            "shares": 10,
            "likes": 42,
            "comments": 5,
            "views": 100
        }
        
        score = engagement_service._calculate_engagement_score(metrics)
        
        # The score should be between 0 and 100
        assert 0 <= score <= 100
        
        # Test with empty metrics
        empty_score = engagement_service._calculate_engagement_score({})
        assert empty_score == 0.0
        
        # Test with partial metrics
        partial_metrics = {
            "shares": 10,
            "likes": 42
        }
        partial_score = engagement_service._calculate_engagement_score(partial_metrics)
        assert 0 <= partial_score <= 100
        
        # Test with comment_elements instead of comments
        alt_metrics = {
            "shares": 10,
            "likes": 42,
            "comment_elements": 5,
            "views": 100
        }
        alt_score = engagement_service._calculate_engagement_score(alt_metrics)
        assert alt_score == score  # Should be the same as the original score
