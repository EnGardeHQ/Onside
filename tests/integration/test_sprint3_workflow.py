"""Integration tests for Sprint 3 workflow.

This test file verifies the end-to-end workflow of the Link Search, Web Scraper, and
Engagement Extraction services working together.
"""
import pytest
import asyncio
import re
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from enum import Enum

# Define a mock CompanyType enum for testing
class MockCompanyType(str, Enum):
    """Mock company type enumeration for testing."""
    COMPETITOR = "competitor"
    PARTNER = "partner"
    CLIENT = "client"
    PROSPECT = "prospect"
    OTHER = "other"

# Patch the CompanyType enum before any imports
with patch("src.models.company.CompanyType", MockCompanyType):
    # Mock models before importing services
    mock_link = MagicMock()
    mock_link.__table__ = MagicMock()
    mock_link.__table__.name = "links"
    mock_link.__mapper__ = MagicMock()
    mock_link.__mapper__.relationships = {}
    mock_link._sa_instance_state = MagicMock()
    mock_link._sa_instance_state.persist_selectable = MagicMock()
    mock_link._sa_instance_state.class_ = mock_link

    mock_tag = MagicMock()
    mock_tag.__table__ = MagicMock()
    mock_tag.__table__.name = "tags"
    mock_tag.__mapper__ = MagicMock()
    mock_tag.__mapper__.relationships = {}
    mock_tag._sa_instance_state = MagicMock()
    mock_tag._sa_instance_state.persist_selectable = MagicMock()
    mock_tag._sa_instance_state.class_ = mock_tag

    # Mock the models before importing services
    with patch("src.models.link.Link", mock_link), \
         patch("src.models.tag.Tag", mock_tag):
        # Import services after mocking models
        from src.services.link_search.link_search import LinkSearchService
        from src.services.web_scraper.web_scraper import WebScraperService
        from src.services.engagement_extraction.engagement_extraction import EngagementExtractionService


def create_mock_link(id=1, url="https://example.com/page1", domain_id=1, title="Example Page", meta=None, tags=None):
    """Helper function to create a mock link with SQLAlchemy attributes."""
    mock_link = MagicMock()
    mock_link.id = id
    mock_link.url = url
    mock_link.domain_id = domain_id
    mock_link.title = title
    mock_link.meta = meta or {
        'snippet': 'This is an example page.',
        'search_score': 10,
        'source': 'domain_search'
    }
    mock_link.last_scraped = None
    mock_link.published_date = None
    mock_link.tags = tags or []
    mock_link._sa_instance_state = MagicMock()
    mock_link._sa_instance_state.persist_selectable = MagicMock()
    mock_link._sa_instance_state.class_ = mock_link
    return mock_link


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest.fixture
def link_search_service(mock_db):
    """Create a LinkSearchService with a mock database."""
    service = LinkSearchService(mock_db)
    # Mock internal methods
    service._get_domain = AsyncMock()
    service._get_company = AsyncMock()
    service._search_for_domain = AsyncMock()
    service._get_link_by_url = AsyncMock()
    return service


@pytest.fixture
def web_scraper_service(mock_db):
    """Create a WebScraperService with a mock database."""
    service = WebScraperService(mock_db)
    # Mock internal methods
    service._get_link = AsyncMock()
    service._fetch_url = AsyncMock()
    service._take_screenshot = AsyncMock()
    return service


@pytest.fixture
def engagement_service(mock_db):
    """Create an EngagementExtractionService with a mock database."""
    service = EngagementExtractionService(mock_db)
    # Mock internal methods
    service._get_link = AsyncMock()
    service._get_latest_snapshot = AsyncMock()
    service._store_engagement_metrics = AsyncMock()
    service.extract_metrics = AsyncMock()
    service.update_link_engagement_score = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_end_to_end_workflow(link_search_service, web_scraper_service, engagement_service, mock_db):
    """Test end-to-end workflow for a single link."""
    # Mock domain
    domain = MagicMock()
    domain.id = 1
    domain.domain_name = "example.com"

    # Mock link
    mock_link = create_mock_link()

    # Mock snapshot
    mock_snapshot = MagicMock()
    mock_snapshot.id = 1
    mock_snapshot.link_id = 1
    mock_snapshot.html_content = "<html><body>Example Page</body></html>"
    mock_snapshot.meta = {
        'word_count': 100,
        'meta_tags': {
            'description': 'Example description',
            'og:title': 'Example Page',
            'og:description': 'Example description',
            'article:published_time': '2023-01-01T00:00:00Z'
        }
    }
    mock_snapshot.text_content = "Example Page content"
    mock_snapshot.engagement_metrics = {
        'share_buttons': 2,
        'comment_elements': 3,
        'comments': 10,
        'shares': 5,
        'likes': 20,
        'views': 100
    }
    mock_snapshot.created_at = datetime.now(timezone.utc)

    # Mock database operations
    mock_db.add = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    # Set up mock return values
    link_search_service._get_domain.return_value = domain
    link_search_service._search_for_domain.return_value = [{
        'title': 'Example Page',
        'link': 'https://example.com/page1',
        'snippet': 'This is an example page.',
        'search_score': 10
    }]
    link_search_service._get_link_by_url.return_value = None
    
    web_scraper_service._get_link.return_value = mock_link
    web_scraper_service._fetch_url.return_value = ("<html><body>Example Page</body></html>", None)
    web_scraper_service._take_screenshot.return_value = "/path/to/screenshot.png"
    
    engagement_service._get_link.return_value = mock_link
    engagement_service._get_latest_snapshot.return_value = mock_snapshot
    engagement_service.extract_metrics.return_value = {
        'likes': 20,
        'shares': 5,
        'comments': 10
    }
    engagement_service.update_link_engagement_score.return_value = 0.75

    # Step 1: Search for links - mock the search_links_for_domain method
    with patch.object(link_search_service, 'search_links_for_domain', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = ([mock_link], None)
        
        links, errors = await link_search_service.search_links_for_domain(domain_id=1)
        assert len(links) == 1
        assert not errors

        # Step 2: Scrape link - mock the scrape_link method
        with patch.object(web_scraper_service, 'scrape_link', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = (mock_snapshot, None)
            
            snapshot, error = await web_scraper_service.scrape_link(link_id=1)
            assert snapshot is not None
            assert error is None

            # Step 3: Extract engagement metrics - mock the extract_engagement_for_link method
            with patch.object(engagement_service, 'extract_engagement_for_link', new_callable=AsyncMock) as mock_extract:
                mock_extract.return_value = ({
                    'link_id': 1,
                    'social_signals': {
                        'likes': 20,
                        'shares': 5,
                        'comments': 10
                    },
                    'engagement_score': 0.75
                }, None)
                
                metrics, error = await engagement_service.extract_engagement_for_link(link_id=1)
                assert metrics is not None
                assert error is None
                assert metrics['engagement_score'] == 0.75


@pytest.mark.asyncio
async def test_batch_processing(link_search_service, web_scraper_service, engagement_service, mock_db):
    """Test batch processing of links through the entire workflow."""
    # Mock domain
    domain = MagicMock()
    domain.id = 1
    domain.domain_name = "example.com"

    # Mock links
    mock_links = []
    for i in range(5):
        mock_link = create_mock_link(
            id=i + 1,
            url=f"https://example.com/page{i+1}",
            title=f"Example Page {i+1}",
            meta={
                'snippet': f'This is example page {i+1}.',
                'search_score': 10 - i,
                'source': 'domain_search'
            }
        )
        mock_links.append(mock_link)

    # Mock snapshots
    mock_snapshots = []
    for i in range(5):
        mock_snapshot = MagicMock()
        mock_snapshot.id = i + 1
        mock_snapshot.link_id = i + 1
        mock_snapshot.html_content = f"<html><body>Example Page {i+1}</body></html>"
        mock_snapshot.meta = {
            'word_count': 100 + i * 10,
            'meta_tags': {
                'description': f'Example description {i+1}',
                'og:title': f'Example Page {i+1}',
                'og:description': f'Example description {i+1}',
                'article:published_time': '2023-01-01T00:00:00Z'
            }
        }
        mock_snapshot.text_content = f"Example Page {i+1} content"
        mock_snapshot.engagement_metrics = {
            'share_buttons': 2,
            'comment_elements': 3,
            'comments': 10 + i,
            'shares': 5 + i,
            'likes': 20 + i * 2,
            'views': 100 + i * 10
        }
        mock_snapshot.created_at = datetime.now(timezone.utc)
        mock_snapshots.append(mock_snapshot)

    # Mock database operations
    mock_db.add = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    # Set up mock return values
    link_search_service._get_domain.return_value = domain
    
    # Step 1: Search for links - mock the search_links_for_domain method
    with patch.object(link_search_service, 'search_links_for_domain', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = (mock_links, None)
        
        links, errors = await link_search_service.search_links_for_domain(domain_id=1)
        assert len(links) == 5
        assert not errors

        # Step 2: Scrape links - mock the scrape_links_batch method
        with patch.object(web_scraper_service, 'scrape_links_batch', new_callable=AsyncMock) as mock_scrape_batch:
            # Create a dictionary of results
            scrape_results = {}
            for i, link in enumerate(mock_links):
                scrape_results[link.id] = {
                    'success': True,
                    'snapshot_id': i + 1,
                    'metadata': mock_snapshots[i].meta
                }
            
            mock_scrape_batch.return_value = scrape_results
            
            link_ids = [link.id for link in links]
            results = await web_scraper_service.scrape_links_batch(link_ids=link_ids)
            assert len(results) == 5
            assert all(result['success'] for result in results.values())

            # Step 3: Extract engagement metrics - mock the extract_engagement_for_links method
            with patch.object(engagement_service, 'extract_engagement_for_links', new_callable=AsyncMock) as mock_extract_batch:
                # Create successful links and errors
                successful_links = []
                for i, link in enumerate(mock_links):
                    successful_links.append({
                        'link_id': link.id,
                        'social_signals': {
                            'likes': 20 + i * 2,
                            'shares': 5 + i,
                            'comments': 10 + i
                        },
                        'engagement_score': 0.75 - i * 0.05
                    })
                
                mock_extract_batch.return_value = (successful_links, [])
                
                successful, errors = await engagement_service.extract_engagement_for_links(link_ids=link_ids)
                assert len(successful) == 5
                assert len(errors) == 0
                assert all('engagement_score' in result for result in successful)


@pytest.mark.asyncio
async def test_error_handling(link_search_service, web_scraper_service, engagement_service, mock_db):
    """Test error handling in the workflow."""
    # Step 1: Test domain not found in link search
    link_search_service._get_domain.return_value = None
    
    with patch.object(link_search_service, 'search_links_for_domain', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = (None, {"error": "Domain with ID 999 not found"})
        
        links, error = await link_search_service.search_links_for_domain(domain_id=999)
        assert links is None
        assert error is not None
        assert "not found" in error["error"]

    # Step 2: Test link not found in web scraper
    web_scraper_service._get_link.return_value = None
    
    with patch.object(web_scraper_service, 'scrape_link', new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = (None, {"error": "Link with ID 999 not found"})
        
        link, result = await web_scraper_service.scrape_link(link_id=999)
        assert link is None
        assert "not found" in result["error"]

    # Step 3: Test snapshot not found in engagement extraction
    engagement_service._get_link.return_value = create_mock_link(id=3)
    engagement_service._get_latest_snapshot.return_value = None
    
    with patch.object(engagement_service, 'extract_engagement_for_link', new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = (None, {"error": "No snapshot found for link with ID 3"})
        
        metrics, error = await engagement_service.extract_engagement_for_link(link_id=3)
        assert metrics is None
        assert "No snapshot found" in error["error"]
