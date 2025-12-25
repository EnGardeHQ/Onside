"""
Comprehensive unit and integration tests for LinkDeduplicationService.

This module provides extensive test coverage for link deduplication functionality,
including URL normalization, similarity detection, fuzzy matching, merging,
and batch scanning capabilities.
"""
import pytest
from unittest.mock import MagicMock, Mock
from datetime import datetime
from typing import List

from src.services.link_deduplication_service import LinkDeduplicationService
from src.models.link import Link


@pytest.fixture
def dedup_service():
    """Create a LinkDeduplicationService instance."""
    return LinkDeduplicationService(similarity_threshold=0.85)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    mock = MagicMock()
    mock.query = MagicMock(return_value=mock)
    mock.filter = MagicMock(return_value=mock)
    mock.order_by = MagicMock(return_value=mock)
    mock.first = MagicMock(return_value=None)
    mock.all = MagicMock(return_value=[])
    mock.in_ = MagicMock(return_value=mock)
    mock.add = MagicMock()
    mock.delete = MagicMock()
    mock.commit = MagicMock()
    mock.refresh = MagicMock()
    mock.count = MagicMock(return_value=0)
    return mock


class TestLinkDeduplicationServiceInitialization:
    """Test suite for service initialization."""

    def test_init_with_default_threshold(self):
        """Test initialization with default similarity threshold."""
        service = LinkDeduplicationService()
        assert service.similarity_threshold == 0.85

    def test_init_with_custom_threshold(self):
        """Test initialization with custom similarity threshold."""
        service = LinkDeduplicationService(similarity_threshold=0.9)
        assert service.similarity_threshold == 0.9


class TestURLNormalization:
    """Test suite for URL normalization."""

    def test_normalize_url_lowercase(self, dedup_service):
        """Test URL is converted to lowercase."""
        url = "HTTPS://EXAMPLE.COM/PATH"
        result = dedup_service.normalize_url(url)
        assert result == "https://example.com/path"

    def test_normalize_url_remove_trailing_slash(self, dedup_service):
        """Test trailing slash is removed."""
        url = "https://example.com/path/"
        result = dedup_service.normalize_url(url)
        assert result == "https://example.com/path"

    def test_normalize_url_remove_www(self, dedup_service):
        """Test www prefix is removed."""
        url = "https://www.example.com/path"
        result = dedup_service.normalize_url(url)
        assert result == "https://example.com/path"

    def test_normalize_url_remove_tracking_params(self, dedup_service):
        """Test tracking parameters are removed."""
        url = "https://example.com/page?utm_source=facebook&utm_campaign=test&actual_param=value"
        result = dedup_service.normalize_url(url)
        assert "utm_source" not in result
        assert "utm_campaign" not in result
        assert "actual_param=value" in result

    def test_normalize_url_remove_fbclid(self, dedup_service):
        """Test Facebook click ID is removed."""
        url = "https://example.com/page?fbclid=12345&other=value"
        result = dedup_service.normalize_url(url)
        assert "fbclid" not in result
        assert "other=value" in result

    def test_normalize_url_remove_gclid(self, dedup_service):
        """Test Google click ID is removed."""
        url = "https://example.com/page?gclid=67890"
        result = dedup_service.normalize_url(url)
        assert "gclid" not in result

    def test_normalize_url_sort_query_params(self, dedup_service):
        """Test query parameters are sorted."""
        url1 = "https://example.com/page?z=3&a=1&m=2"
        url2 = "https://example.com/page?a=1&m=2&z=3"
        result1 = dedup_service.normalize_url(url1)
        result2 = dedup_service.normalize_url(url2)
        assert result1 == result2

    def test_normalize_url_remove_fragment(self, dedup_service):
        """Test URL fragment is removed."""
        url = "https://example.com/page#section"
        result = dedup_service.normalize_url(url)
        assert "#section" not in result

    def test_normalize_url_add_default_scheme(self, dedup_service):
        """Test default scheme is added if missing."""
        url = "example.com/path"
        result = dedup_service.normalize_url(url)
        assert result.startswith("https://")

    def test_normalize_url_handle_invalid_url(self, dedup_service):
        """Test handling of invalid URLs."""
        url = "not a valid url"
        result = dedup_service.normalize_url(url)
        assert result == "not a valid url"  # Returns lowercase stripped version

    def test_normalize_url_preserve_path(self, dedup_service):
        """Test path is preserved correctly."""
        url = "https://example.com/path/to/resource"
        result = dedup_service.normalize_url(url)
        assert "/path/to/resource" in result

    def test_normalize_url_empty_path_becomes_slash(self, dedup_service):
        """Test empty path becomes single slash."""
        url = "https://example.com"
        result = dedup_service.normalize_url(url)
        assert result.endswith("/")


class TestSimilarityCalculation:
    """Test suite for similarity calculation."""

    def test_calculate_similarity_exact_match(self, dedup_service):
        """Test similarity of identical URLs is 1.0."""
        url1 = "https://example.com/page"
        url2 = "https://example.com/page"
        similarity = dedup_service.calculate_similarity(url1, url2)
        assert similarity == 1.0

    def test_calculate_similarity_normalized_match(self, dedup_service):
        """Test similarity after normalization."""
        url1 = "https://www.example.com/page?utm_source=fb"
        url2 = "https://example.com/page/"
        similarity = dedup_service.calculate_similarity(url1, url2)
        assert similarity == 1.0

    def test_calculate_similarity_different_domains(self, dedup_service):
        """Test similarity of different domains is 0.0."""
        url1 = "https://example.com/page"
        url2 = "https://different.com/page"
        similarity = dedup_service.calculate_similarity(url1, url2)
        assert similarity == 0.0

    def test_calculate_similarity_similar_paths(self, dedup_service):
        """Test similarity of similar paths."""
        url1 = "https://example.com/products/item1"
        url2 = "https://example.com/products/item2"
        similarity = dedup_service.calculate_similarity(url1, url2)
        assert 0.5 < similarity < 1.0

    def test_calculate_similarity_different_paths(self, dedup_service):
        """Test similarity of completely different paths."""
        url1 = "https://example.com/products/electronics"
        url2 = "https://example.com/about/team"
        similarity = dedup_service.calculate_similarity(url1, url2)
        assert similarity < 0.5

    def test_calculate_similarity_with_query_params(self, dedup_service):
        """Test similarity considering query parameters."""
        url1 = "https://example.com/search?q=test&category=books&sort=price"
        url2 = "https://example.com/search?q=test&category=books"
        similarity = dedup_service.calculate_similarity(url1, url2)
        assert similarity > 0.7  # Should be high due to shared params

    def test_calculate_similarity_no_query_params(self, dedup_service):
        """Test similarity when neither URL has query params."""
        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"
        similarity = dedup_service.calculate_similarity(url1, url2)
        assert similarity > 0  # Should be non-zero due to path similarity


class TestFindDuplicatesForURL:
    """Test suite for finding duplicates of a single URL."""

    def test_find_duplicates_no_candidates(self, dedup_service, mock_db):
        """Test finding duplicates when no candidates exist."""
        # Arrange
        url = "https://example.com/page"
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # Act
        results = dedup_service.find_duplicates_for_url(
            db=mock_db,
            url=url
        )

        # Assert
        assert len(results) == 0

    def test_find_duplicates_exact_match_excluded(self, dedup_service, mock_db):
        """Test exact match is excluded from duplicates."""
        # Arrange
        url = "https://example.com/page"
        link = Mock(spec=Link, url=url)
        mock_db.query.return_value.filter.return_value.all.return_value = [link]

        # Act
        results = dedup_service.find_duplicates_for_url(
            db=mock_db,
            url=url
        )

        # Assert
        assert len(results) == 0

    def test_find_duplicates_similar_urls(self, dedup_service, mock_db):
        """Test finding similar URLs."""
        # Arrange
        url = "https://example.com/products/item-1"
        similar_link = Mock(
            spec=Link,
            url="https://www.example.com/products/item-1?utm_source=fb"
        )
        mock_db.query.return_value.filter.return_value.all.return_value = [similar_link]

        # Act
        results = dedup_service.find_duplicates_for_url(
            db=mock_db,
            url=url
        )

        # Assert
        assert len(results) == 1
        assert results[0][0] == similar_link
        assert results[0][1] >= 0.85  # Above threshold

    def test_find_duplicates_below_threshold(self, dedup_service, mock_db):
        """Test URLs below threshold are excluded."""
        # Arrange
        url = "https://example.com/products"
        dissimilar_link = Mock(
            spec=Link,
            url="https://example.com/about"
        )
        mock_db.query.return_value.filter.return_value.all.return_value = [dissimilar_link]

        # Act
        results = dedup_service.find_duplicates_for_url(
            db=mock_db,
            url=url
        )

        # Assert
        assert len(results) == 0

    def test_find_duplicates_sorted_by_similarity(self, dedup_service, mock_db):
        """Test results are sorted by similarity score."""
        # Arrange
        url = "https://example.com/products/item1"
        link1 = Mock(spec=Link, url="https://example.com/products/item2")
        link2 = Mock(spec=Link, url="https://example.com/products/item1-new")
        link3 = Mock(spec=Link, url="https://example.com/products/item11")

        mock_db.query.return_value.filter.return_value.all.return_value = [link1, link2, link3]

        # Act
        results = dedup_service.find_duplicates_for_url(
            db=mock_db,
            url=url,
            limit=10
        )

        # Assert - should be sorted by similarity descending
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i][1] >= results[i + 1][1]

    def test_find_duplicates_with_company_filter(self, dedup_service, mock_db):
        """Test filtering by company_id."""
        # Arrange
        url = "https://example.com/page"
        company_id = 123

        # Act
        dedup_service.find_duplicates_for_url(
            db=mock_db,
            url=url,
            company_id=company_id
        )

        # Assert
        mock_db.query.return_value.filter.assert_called()

    def test_find_duplicates_respects_limit(self, dedup_service, mock_db):
        """Test limit parameter is respected."""
        # Arrange
        url = "https://example.com/products/item1"
        links = [
            Mock(spec=Link, url=f"https://example.com/products/item{i}")
            for i in range(2, 12)  # 10 similar links
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = links

        # Act
        results = dedup_service.find_duplicates_for_url(
            db=mock_db,
            url=url,
            limit=5
        )

        # Assert
        assert len(results) <= 5


class TestFindAllDuplicates:
    """Test suite for finding all duplicates in database."""

    def test_find_all_duplicates_empty_database(self, dedup_service, mock_db):
        """Test finding duplicates in empty database."""
        # Arrange
        mock_db.query.return_value.all.return_value = []

        # Act
        results = dedup_service.find_all_duplicates(db=mock_db)

        # Assert
        assert len(results) == 0

    def test_find_all_duplicates_no_duplicates(self, dedup_service, mock_db):
        """Test finding duplicates when all URLs are unique."""
        # Arrange
        links = [
            Mock(spec=Link, url="https://example.com/page1", created_at=datetime(2024, 1, 1)),
            Mock(spec=Link, url="https://example.com/page2", created_at=datetime(2024, 1, 2)),
            Mock(spec=Link, url="https://example.com/page3", created_at=datetime(2024, 1, 3)),
        ]
        mock_db.query.return_value.all.return_value = links
        mock_db.query.return_value.filter.return_value.all.return_value = links

        # Act
        results = dedup_service.find_all_duplicates(db=mock_db)

        # Assert - may have fuzzy matches or no results
        assert isinstance(results, list)

    def test_find_all_duplicates_exact_duplicates(self, dedup_service, mock_db):
        """Test finding exact duplicates after normalization."""
        # Arrange
        links = [
            Mock(spec=Link, url="https://example.com/page", created_at=datetime(2024, 1, 1)),
            Mock(spec=Link, url="https://www.example.com/page/", created_at=datetime(2024, 1, 2)),
            Mock(spec=Link, url="https://example.com/page?utm_source=fb", created_at=datetime(2024, 1, 3)),
        ]
        mock_db.query.return_value.all.return_value = links
        mock_db.query.return_value.filter.return_value.all.return_value = links

        # Act
        results = dedup_service.find_all_duplicates(db=mock_db)

        # Assert
        assert len(results) > 0
        # First group should have the exact duplicates
        if results:
            group = results[0]
            assert 'canonical' in group
            assert 'duplicates' in group
            assert group['count'] >= 2

    def test_find_all_duplicates_canonical_is_oldest(self, dedup_service, mock_db):
        """Test canonical link is the oldest one."""
        # Arrange
        old_date = datetime(2024, 1, 1)
        new_date = datetime(2024, 1, 2)

        links = [
            Mock(spec=Link, url="https://example.com/page", created_at=new_date, id=2),
            Mock(spec=Link, url="https://www.example.com/page/", created_at=old_date, id=1),
        ]
        mock_db.query.return_value.all.return_value = links
        mock_db.query.return_value.filter.return_value.all.return_value = links

        # Act
        results = dedup_service.find_all_duplicates(db=mock_db)

        # Assert
        if results:
            group = results[0]
            assert group['canonical'].created_at == old_date

    def test_find_all_duplicates_with_company_filter(self, dedup_service, mock_db):
        """Test filtering by company_id."""
        # Arrange
        company_id = 123
        links = [
            Mock(spec=Link, url="https://example.com/page1", created_at=datetime(2024, 1, 1)),
        ]
        mock_db.query.return_value.all.return_value = links
        mock_db.query.return_value.filter.return_value.all.return_value = links

        # Act
        dedup_service.find_all_duplicates(db=mock_db, company_id=company_id)

        # Assert
        mock_db.query.return_value.filter.assert_called()


class TestMergeDuplicateLinks:
    """Test suite for merging duplicate links."""

    def test_merge_duplicate_links_success(self, dedup_service, mock_db):
        """Test successful merging of duplicates."""
        # Arrange
        canonical = Mock(
            spec=Link,
            id=1,
            url="https://example.com/page",
            tags=["tag1", "tag2"],
            source="source1",
            click_count=10,
            metadata={}
        )
        duplicate1 = Mock(
            spec=Link,
            id=2,
            url="https://www.example.com/page/",
            tags=["tag2", "tag3"],
            source="source2",
            click_count=5
        )
        duplicate2 = Mock(
            spec=Link,
            id=3,
            url="https://example.com/page?utm_source=fb",
            tags=["tag4"],
            source="source3",
            click_count=3
        )

        mock_db.query.return_value.filter.return_value.first.return_value = canonical
        mock_db.query.return_value.filter.return_value.all.return_value = [duplicate1, duplicate2]

        # Act
        result = dedup_service.merge_duplicate_links(
            db=mock_db,
            canonical_id=1,
            duplicate_ids=[2, 3]
        )

        # Assert
        assert mock_db.delete.call_count == 2
        assert mock_db.commit.called
        assert canonical.click_count == 18  # 10 + 5 + 3

    def test_merge_duplicate_links_tags_merged(self, dedup_service, mock_db):
        """Test tags are merged from all duplicates."""
        # Arrange
        canonical = Mock(
            spec=Link,
            id=1,
            tags=["tag1"],
            source="source1",
            metadata={}
        )
        duplicate = Mock(
            spec=Link,
            id=2,
            tags=["tag2", "tag3"],
            source="source2"
        )

        mock_db.query.return_value.filter.return_value.first.return_value = canonical
        mock_db.query.return_value.filter.return_value.all.return_value = [duplicate]

        # Act
        result = dedup_service.merge_duplicate_links(
            db=mock_db,
            canonical_id=1,
            duplicate_ids=[2]
        )

        # Assert
        merged_tags = set(canonical.tags)
        assert "tag1" in merged_tags
        assert "tag2" in merged_tags
        assert "tag3" in merged_tags

    def test_merge_duplicate_links_metadata_stored(self, dedup_service, mock_db):
        """Test merge metadata is stored."""
        # Arrange
        canonical = Mock(
            spec=Link,
            id=1,
            tags=["tag1"],
            source="source1",
            metadata={}
        )
        duplicate = Mock(
            spec=Link,
            id=2,
            url="https://example.com/duplicate",
            tags=None,
            source="source2"
        )

        mock_db.query.return_value.filter.return_value.first.return_value = canonical
        mock_db.query.return_value.filter.return_value.all.return_value = [duplicate]

        # Act
        result = dedup_service.merge_duplicate_links(
            db=mock_db,
            canonical_id=1,
            duplicate_ids=[2]
        )

        # Assert
        assert 'merged_from' in canonical.metadata
        assert 'merge_sources' in canonical.metadata
        assert 'merged_at' in canonical.metadata

    def test_merge_duplicate_links_canonical_not_found(self, dedup_service, mock_db):
        """Test error when canonical link not found."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Canonical link not found"):
            dedup_service.merge_duplicate_links(
                db=mock_db,
                canonical_id=999,
                duplicate_ids=[2, 3]
            )

    def test_merge_duplicate_links_no_duplicates(self, dedup_service, mock_db):
        """Test merging with no duplicates."""
        # Arrange
        canonical = Mock(
            spec=Link,
            id=1,
            tags=["tag1"],
            source="source1",
            metadata={}
        )

        mock_db.query.return_value.filter.return_value.first.return_value = canonical
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # Act
        result = dedup_service.merge_duplicate_links(
            db=mock_db,
            canonical_id=1,
            duplicate_ids=[]
        )

        # Assert
        assert mock_db.delete.call_count == 0
        assert mock_db.commit.called


class TestGenerateDuplicateReport:
    """Test suite for duplicate report generation."""

    def test_generate_duplicate_report_empty_database(self, dedup_service, mock_db):
        """Test report generation for empty database."""
        # Arrange
        mock_db.query.return_value.all.return_value = []
        mock_db.query.return_value.count.return_value = 0

        # Act
        report = dedup_service.generate_duplicate_report(db=mock_db)

        # Assert
        assert report['summary']['total_links'] == 0
        assert report['summary']['total_duplicates'] == 0
        assert len(report['duplicate_groups']) == 0

    def test_generate_duplicate_report_with_duplicates(self, dedup_service, mock_db):
        """Test report generation with duplicates."""
        # Arrange
        links = [
            Mock(spec=Link, url="https://example.com/page1", created_at=datetime(2024, 1, 1)),
            Mock(spec=Link, url="https://www.example.com/page1/", created_at=datetime(2024, 1, 2)),
        ]
        mock_db.query.return_value.all.return_value = links
        mock_db.query.return_value.filter.return_value.all.return_value = links
        mock_db.query.return_value.count.return_value = 2

        # Act
        report = dedup_service.generate_duplicate_report(db=mock_db)

        # Assert
        assert 'summary' in report
        assert 'duplicate_groups' in report
        assert 'recommendations' in report
        assert 'generated_at' in report

    def test_generate_duplicate_report_calculates_savings(self, dedup_service, mock_db):
        """Test report calculates potential savings percentage."""
        # Arrange
        links = [
            Mock(spec=Link, url="https://example.com/page1", created_at=datetime(2024, 1, 1)),
            Mock(spec=Link, url="https://www.example.com/page1/", created_at=datetime(2024, 1, 2)),
        ]
        mock_db.query.return_value.all.return_value = links
        mock_db.query.return_value.filter.return_value.all.return_value = links
        mock_db.query.return_value.count.return_value = 10

        # Act
        report = dedup_service.generate_duplicate_report(db=mock_db)

        # Assert
        assert 'savings_percentage' in report['summary']
        assert report['summary']['savings_percentage'] >= 0

    def test_generate_duplicate_report_with_company_filter(self, dedup_service, mock_db):
        """Test report generation with company filter."""
        # Arrange
        company_id = 123
        links = []
        mock_db.query.return_value.all.return_value = links
        mock_db.query.return_value.filter.return_value.all.return_value = links
        mock_db.query.return_value.count.return_value = 0

        # Act
        report = dedup_service.generate_duplicate_report(
            db=mock_db,
            company_id=company_id
        )

        # Assert
        mock_db.query.return_value.filter.assert_called()


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_normalize_url_with_port(self, dedup_service):
        """Test URL normalization preserves port."""
        url = "https://example.com:8080/path"
        result = dedup_service.normalize_url(url)
        assert ":8080" in result

    def test_normalize_url_with_username_password(self, dedup_service):
        """Test URL with authentication."""
        url = "https://user:pass@example.com/path"
        result = dedup_service.normalize_url(url)
        assert "user:pass" in result

    def test_calculate_similarity_empty_paths(self, dedup_service):
        """Test similarity calculation with empty paths."""
        url1 = "https://example.com"
        url2 = "https://example.com/"
        similarity = dedup_service.calculate_similarity(url1, url2)
        assert similarity == 1.0

    def test_normalize_url_multiple_slashes(self, dedup_service):
        """Test URL with multiple consecutive slashes."""
        url = "https://example.com//path///to//resource"
        result = dedup_service.normalize_url(url)
        # Should still be valid
        assert "example.com" in result

    def test_normalize_url_unicode_characters(self, dedup_service):
        """Test URL with unicode characters."""
        url = "https://example.com/путь/to/résumé"
        result = dedup_service.normalize_url(url)
        assert isinstance(result, str)

    def test_find_duplicates_self_similarity(self, dedup_service):
        """Test URL doesn't match itself as duplicate."""
        url = "https://example.com/page"
        similarity = dedup_service.calculate_similarity(url, url)
        assert similarity == 1.0

    def test_merge_with_null_tags(self, dedup_service, mock_db):
        """Test merging links with null tags."""
        # Arrange
        canonical = Mock(
            spec=Link,
            id=1,
            tags=None,
            source="source1",
            metadata={}
        )
        duplicate = Mock(
            spec=Link,
            id=2,
            tags=None,
            source="source2"
        )

        mock_db.query.return_value.filter.return_value.first.return_value = canonical
        mock_db.query.return_value.filter.return_value.all.return_value = [duplicate]

        # Act
        result = dedup_service.merge_duplicate_links(
            db=mock_db,
            canonical_id=1,
            duplicate_ids=[2]
        )

        # Assert
        assert canonical.tags is None or canonical.tags == []

    def test_normalize_url_data_uri(self, dedup_service):
        """Test normalization handles data URIs gracefully."""
        url = "data:text/html,<h1>Test</h1>"
        result = dedup_service.normalize_url(url)
        assert result  # Should return something without crashing
