"""
Shared fixtures for service testing.

This module provides reusable fixtures for testing services,
including mock database sessions, HTTP clients, and common test data.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, Mock
from datetime import datetime, timedelta
from typing import Dict, Any, List


@pytest.fixture
def mock_db_session():
    """Create a mock database session for service testing.

    Returns a mock with common SQLAlchemy session methods.
    """
    mock = MagicMock()
    mock.query = MagicMock(return_value=mock)
    mock.filter = MagicMock(return_value=mock)
    mock.filter_by = MagicMock(return_value=mock)
    mock.order_by = MagicMock(return_value=mock)
    mock.first = MagicMock(return_value=None)
    mock.all = MagicMock(return_value=[])
    mock.limit = MagicMock(return_value=mock)
    mock.offset = MagicMock(return_value=mock)
    mock.count = MagicMock(return_value=0)
    mock.add = MagicMock()
    mock.delete = MagicMock()
    mock.commit = MagicMock()
    mock.rollback = MagicMock()
    mock.refresh = MagicMock()
    mock.flush = MagicMock()
    mock.close = MagicMock()
    return mock


@pytest_asyncio.fixture
async def mock_async_http_client():
    """Create a mock async HTTP client.

    Returns a mock AsyncClient with common methods for API testing.
    """
    mock = AsyncMock()
    mock.get = AsyncMock()
    mock.post = AsyncMock()
    mock.put = AsyncMock()
    mock.patch = AsyncMock()
    mock.delete = AsyncMock()
    mock.aclose = AsyncMock()
    return mock


@pytest.fixture
def sample_scraped_content_data() -> Dict[str, Any]:
    """Provide sample scraped content data for testing."""
    return {
        'id': 1,
        'url': 'https://example.com/page',
        'domain': 'example.com',
        'company_id': 123,
        'version': 1,
        'html_content': '<html><body><h1>Test Page</h1></body></html>',
        'text_content': 'Test Page Content',
        'title': 'Test Page',
        'meta_description': 'A test page description',
        'meta_keywords': 'test, page, keywords',
        'screenshot_url': '/storage/screenshots/example.com/test.png',
        'content_hash': 'abc123def456',
        'status_code': 200,
        'scrape_duration_ms': 1500.0,
        'created_at': datetime.utcnow()
    }


@pytest.fixture
def sample_link_data() -> Dict[str, Any]:
    """Provide sample link data for testing."""
    return {
        'id': 1,
        'url': 'https://example.com/article',
        'domain_id': 1,
        'title': 'Sample Article',
        'description': 'This is a sample article description',
        'discovered_at': datetime.utcnow(),
        'last_checked': datetime.utcnow(),
        'status_code': 200,
        'is_active': True,
        'meta_data': {'source': 'crawler', 'relevance': 0.95}
    }


@pytest.fixture
def sample_search_history_data() -> Dict[str, Any]:
    """Provide sample search history data for testing."""
    return {
        'id': 1,
        'user_id': 100,
        'company_id': 123,
        'query': 'test search query',
        'search_type': 'content',
        'filters': {'status': 'active', 'date_range': '7d'},
        'results_count': 42,
        'execution_time_ms': 250.5,
        'language': 'en',
        'ip_address': '192.168.1.1',
        'user_agent': 'Mozilla/5.0',
        'created_at': datetime.utcnow()
    }


@pytest.fixture
def sample_youtube_video_data() -> Dict[str, Any]:
    """Provide sample YouTube video data for testing."""
    return {
        'videoId': 'test_video_123',
        'title': 'Test Video Title',
        'description': 'This is a test video description',
        'channelId': 'channel_123',
        'channelTitle': 'Test Channel',
        'publishedAt': '2024-01-15T10:30:00Z',
        'thumbnails': {
            'default': {'url': 'https://i.ytimg.com/vi/test_video_123/default.jpg'}
        },
        'tags': ['test', 'video', 'tutorial'],
        'categoryId': '22',
        'duration': 'PT10M30S',
        'statistics': {
            'viewCount': 10000,
            'likeCount': 500,
            'commentCount': 100,
            'engagementRate': 6.0
        }
    }


@pytest.fixture
def sample_google_search_result() -> Dict[str, Any]:
    """Provide sample Google search result for testing."""
    return {
        'title': 'Test Search Result',
        'link': 'https://example.com/result',
        'snippet': 'This is a test search result snippet',
        'displayLink': 'example.com',
        'formattedUrl': 'https://example.com/result',
        'htmlSnippet': '<b>Test</b> search result',
        'htmlTitle': '<b>Test</b> Search Result',
        'pagemap': {
            'metatags': [{'description': 'Meta description'}]
        }
    }


@pytest.fixture
def sample_report_schedule_data() -> Dict[str, Any]:
    """Provide sample report schedule data for testing."""
    return {
        'id': 1,
        'name': 'Weekly Performance Report',
        'report_type': 'performance',
        'user_id': 100,
        'company_id': 123,
        'cron_expression': '0 9 * * 1',
        'timezone': 'America/New_York',
        'is_active': True,
        'email_recipients': ['user@example.com', 'manager@example.com'],
        'report_config': {
            'metrics': ['views', 'engagement', 'conversion'],
            'period': '7d',
            'format': 'pdf'
        },
        'last_run_at': datetime.utcnow() - timedelta(days=7),
        'next_run_at': datetime.utcnow() + timedelta(days=7),
        'created_at': datetime.utcnow()
    }


@pytest.fixture
def sample_content_change_data() -> Dict[str, Any]:
    """Provide sample content change data for testing."""
    return {
        'id': 1,
        'url': 'https://example.com/page',
        'old_version_id': 1,
        'new_version_id': 2,
        'change_type': 'minor',
        'change_summary': '10 additions, 5 deletions',
        'change_percentage': 15.5,
        'diff_data': {
            'additions': 10,
            'deletions': 5,
            'similarity': 0.845,
            'old_length': 1000,
            'new_length': 1050
        },
        'detected_at': datetime.utcnow()
    }


@pytest.fixture
def mock_storage_service():
    """Create a mock storage service for testing."""
    mock = AsyncMock()
    mock.upload_file = AsyncMock(return_value="/storage/test_file.png")
    mock.download_file = AsyncMock(return_value=b"file_content")
    mock.delete_file = AsyncMock(return_value=True)
    mock.list_files = AsyncMock(return_value=[])
    mock.get_file_url = MagicMock(return_value="https://storage.example.com/file.png")
    return mock


@pytest.fixture
def mock_playwright_page():
    """Create a mock Playwright page for web scraping tests."""
    page = AsyncMock()
    page.goto = AsyncMock(return_value=AsyncMock(status=200))
    page.content = AsyncMock(return_value="<html><body><h1>Test</h1></body></html>")
    page.title = AsyncMock(return_value="Test Page")
    page.evaluate = AsyncMock(return_value="Test content")
    page.screenshot = AsyncMock(return_value=b"screenshot_data")
    page.wait_for_selector = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.close = AsyncMock()
    return page


@pytest.fixture
def mock_playwright_browser(mock_playwright_page):
    """Create a mock Playwright browser for web scraping tests."""
    browser = AsyncMock()
    browser.new_page = AsyncMock(return_value=mock_playwright_page)
    browser.new_context = AsyncMock()
    browser.close = AsyncMock()
    return browser


@pytest.fixture
def create_mock_http_response():
    """Factory fixture to create mock HTTP responses.

    Returns a function that creates a mock response with customizable data.
    """
    def _create_response(
        status_code: int = 200,
        json_data: Dict[str, Any] = None,
        text: str = "",
        headers: Dict[str, str] = None
    ):
        response = AsyncMock()
        response.status_code = status_code
        response.json = AsyncMock(return_value=json_data or {})
        response.text = text
        response.headers = headers or {}
        response.raise_for_status = MagicMock()

        if status_code >= 400:
            import httpx
            response.raise_for_status.side_effect = httpx.HTTPStatusError(
                f"Error {status_code}",
                request=Mock(),
                response=response
            )

        return response

    return _create_response


@pytest.fixture
def create_mock_db_query_result():
    """Factory fixture to create mock database query results.

    Returns a function that creates a mock query with customizable results.
    """
    def _create_query(
        first_result: Any = None,
        all_results: List[Any] = None,
        count_result: int = 0
    ):
        mock = MagicMock()
        mock.query = MagicMock(return_value=mock)
        mock.filter = MagicMock(return_value=mock)
        mock.filter_by = MagicMock(return_value=mock)
        mock.order_by = MagicMock(return_value=mock)
        mock.limit = MagicMock(return_value=mock)
        mock.offset = MagicMock(return_value=mock)
        mock.first = MagicMock(return_value=first_result)
        mock.all = MagicMock(return_value=all_results or [])
        mock.count = MagicMock(return_value=count_result)
        return mock

    return _create_query


@pytest.fixture
def freeze_time():
    """Fixture to freeze time for testing time-dependent functionality.

    Usage:
        def test_something(freeze_time):
            frozen_time = freeze_time(datetime(2024, 1, 15, 10, 30))
            # Test code here
    """
    def _freeze(target_datetime: datetime):
        """Freeze time to a specific datetime."""
        from unittest.mock import patch
        return patch('datetime.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = target_datetime
            mock_datetime.now.return_value = target_datetime
            return target_datetime

    return _freeze


@pytest.fixture
def sample_pagination_params() -> Dict[str, Any]:
    """Provide sample pagination parameters."""
    return {
        'page': 1,
        'limit': 20,
        'offset': 0,
        'sort': 'created_at',
        'order': 'desc'
    }


@pytest.fixture
def sample_filter_params() -> Dict[str, Any]:
    """Provide sample filter parameters."""
    return {
        'name__contains': 'test',
        'status__in': 'active,pending',
        'created_at__gte': '2024-01-01',
        'is_active': 'true'
    }


@pytest.fixture
def mock_celery_task():
    """Create a mock Celery task for testing async jobs."""
    task = MagicMock()
    task.delay = MagicMock(return_value=MagicMock(id='task-123'))
    task.apply_async = MagicMock(return_value=MagicMock(id='task-456'))
    task.AsyncResult = MagicMock()
    return task


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Provide sample user data for testing."""
    return {
        'id': 100,
        'email': 'test@example.com',
        'username': 'testuser',
        'name': 'Test User',
        'role': 'user',
        'is_active': True,
        'is_admin': False,
        'created_at': datetime.utcnow()
    }


@pytest.fixture
def sample_company_data() -> Dict[str, Any]:
    """Provide sample company data for testing."""
    return {
        'id': 123,
        'name': 'Test Company Inc',
        'domain': 'testcompany.com',
        'industry': 'Technology',
        'size': '50-200',
        'is_active': True,
        'settings': {
            'timezone': 'America/New_York',
            'language': 'en',
            'features': ['analytics', 'reports', 'api']
        },
        'created_at': datetime.utcnow()
    }
