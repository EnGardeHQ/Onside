"""Tests for the LinkSearchService."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

from src.services.link_search.link_search import LinkSearchService

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db

@pytest.fixture
def link_search_service(mock_db):
    """Create a LinkSearchService with a mock database session."""
    return LinkSearchService(mock_db)

class TestLinkSearchService:
    """Tests for the LinkSearchService."""

    @patch('src.services.link_search.link_search.select')
    async def test_search_links_for_domain(self, mock_select, link_search_service, mock_db):
        """Test searching for links associated with a domain."""
        # Mock domain
        mock_domain = MagicMock()
        mock_domain.id = 1
        mock_domain.domain_name = "example.com"
        
        # Mock _get_domain method
        link_search_service._get_domain = AsyncMock(return_value=mock_domain)
        
        # Mock _get_link_by_url method to simulate no existing links
        link_search_service._get_link_by_url = AsyncMock(return_value=None)
        
        # Mock search results
        mock_search_results = [
            {
                "title": "Example Page 1",
                "link": "https://example.com/page1",
                "snippet": "This is an example page 1.",
                "search_score": 9
            },
            {
                "title": "Example Page 2",
                "link": "https://example.com/page2",
                "snippet": "This is an example page 2.",
                "search_score": 8
            }
        ]
        
        # Mock _search_for_domain method
        link_search_service._search_for_domain = AsyncMock(return_value=mock_search_results)
        
        # Call the method
        links, errors = await link_search_service.search_links_for_domain(1, max_results=2)
        
        # Check results
        assert len(links) == 2
        assert len(errors) == 0
        
        # Verify that links were added to the database
        assert mock_db.add.call_count == 2
        assert mock_db.commit.await_count == 1
        
        # Check link properties
        for i, link in enumerate(links):
            assert link.url == f"https://example.com/page{i+1}"
            assert link.domain_id == 1
            assert link.title == f"Example Page {i+1}"
            assert link.meta["snippet"] == f"This is an example page {i+1}."
            assert link.meta["search_score"] == 9 - i
            assert link.meta["source"] == "domain_search"

    @patch('src.services.link_search.link_search.select')
    async def test_search_links_for_domain_with_keywords(self, mock_select, link_search_service, mock_db):
        """Test searching for links within a domain using specific keywords."""
        # Mock domain
        mock_domain = MagicMock()
        mock_domain.id = 1
        mock_domain.domain_name = "example.com"
        
        # Mock _get_domain method
        link_search_service._get_domain = AsyncMock(return_value=mock_domain)
        
        # Mock _get_link_by_url method to simulate no existing links
        link_search_service._get_link_by_url = AsyncMock(return_value=None)
        
        # Mock search results
        keywords = ["test", "example"]
        mock_search_results = [
            {
                "title": "Example Page 1 - test",
                "link": "https://example.com/test/page1",
                "snippet": "This is an example page about test.",
                "search_score": 9
            },
            {
                "title": "Example Page 2 - example",
                "link": "https://example.com/example/page2",
                "snippet": "This is an example page about example.",
                "search_score": 8
            }
        ]
        
        # Mock _search_for_domain_with_keywords method
        link_search_service._search_for_domain_with_keywords = AsyncMock(return_value=mock_search_results)
        
        # Call the method
        links, errors = await link_search_service.search_links_for_domain(1, max_results=2, keywords=keywords)
        
        # Check results
        assert len(links) == 2
        assert len(errors) == 0
        
        # Verify that links were added to the database
        assert mock_db.add.call_count == 2
        assert mock_db.commit.await_count == 1
        
        # Check link properties
        assert links[0].meta["source"] == "keyword_search"
        assert links[0].meta["keywords"] == keywords

    @patch('src.services.link_search.link_search.select')
    async def test_search_links_for_company(self, mock_select, link_search_service, mock_db):
        """Test searching for links across all domains of a company."""
        # Mock company
        mock_company = MagicMock()
        mock_company.id = 1
        mock_company.name = "Example Company"
        
        # Mock domains
        mock_domain1 = MagicMock()
        mock_domain1.id = 1
        mock_domain1.domain_name = "example.com"
        
        mock_domain2 = MagicMock()
        mock_domain2.id = 2
        mock_domain2.domain_name = "example.org"
        
        # Mock _get_company method
        link_search_service._get_company = AsyncMock(return_value=mock_company)
        
        # Mock _get_domains_for_company method
        link_search_service._get_domains_for_company = AsyncMock(return_value=[mock_domain1, mock_domain2])
        
        # Mock search_links_for_domain method
        mock_link1 = MagicMock()
        mock_link1.id = 1
        mock_link1.url = "https://example.com/page1"
        
        mock_link2 = MagicMock()
        mock_link2.id = 2
        mock_link2.url = "https://example.org/page1"
        
        link_search_service.search_links_for_domain = AsyncMock(side_effect=[
            ([mock_link1], []),
            ([mock_link2], [])
        ])
        
        # Call the method
        links, errors = await link_search_service.search_links_for_company(1, max_results=2)
        
        # Check results
        assert len(links) == 2
        assert len(errors) == 0
        
        # Verify that search_links_for_domain was called for each domain
        assert link_search_service.search_links_for_domain.await_count == 2
        
        # Check that the links from both domains are included
        assert links[0].id == 1
        assert links[1].id == 2

    @patch('src.services.link_search.link_search.select')
    async def test_search_links_by_keywords(self, mock_select, link_search_service, mock_db):
        """Test searching for links within a domain using specific keywords."""
        # Mock search_links_for_domain method
        mock_link = MagicMock()
        mock_link.id = 1
        mock_link.url = "https://example.com/test/page1"
        
        link_search_service.search_links_for_domain = AsyncMock(return_value=([mock_link], []))
        
        # Call the method
        links, errors = await link_search_service.search_links_by_keywords(1, keywords=["test", "example"])
        
        # Check results
        assert len(links) == 1
        assert len(errors) == 0
        
        # Verify that search_links_for_domain was called with the keywords
        link_search_service.search_links_for_domain.assert_awaited_once_with(
            domain_id=1,
            max_results=50,
            keywords=["test", "example"]
        )

    async def test_search_links_by_keywords_empty(self, link_search_service):
        """Test searching with empty keywords."""
        # Call the method with empty keywords
        links, errors = await link_search_service.search_links_by_keywords(1, keywords=[])
        
        # Check results
        assert len(links) == 0
        assert len(errors) == 1
        assert errors[0]["error"] == "No keywords provided"
        
    def test_mock_search_results(self, link_search_service):
        """Test the mock search results generation."""
        # Call the method
        mock_results = link_search_service._mock_search_results("example.com", max_results=3)
        
        # Check results
        assert len(mock_results) == 3
        
        for i, result in enumerate(mock_results, 1):
            assert result["title"] == f"Example Page {i}"
            assert result["link"] == f"https://example.com/page{i}"
            assert result["snippet"] == f"This is an example page {i}."
            assert result["search_score"] == 10 - i
            
    def test_mock_search_results_with_keywords(self, link_search_service):
        """Test the mock search results with keywords generation."""
        # Call the method
        keywords = ["test", "example"]
        mock_results = link_search_service._mock_search_results_with_keywords("example.com", keywords, max_results=3)
        
        # Check results
        assert len(mock_results) == 3
        
        for i, result in enumerate(mock_results, 1):
            keyword = keywords[i % len(keywords)]
            assert result["title"] == f"Example Page {i} - {keyword}"
            assert result["link"] == f"https://example.com/{keyword}/page{i}"
            assert result["snippet"] == f"This is an example page about {keyword}."
            assert result["search_score"] == 10 - i
