"""Mock HTTP responses for web scraping tests.

Provides mock HTML responses for testing web scraping functionality
without making actual HTTP requests.
"""
from typing import Dict, Any, Optional
import asyncio
from unittest.mock import AsyncMock, Mock


class MockHTTPResponse:
    """Mock HTTP response object."""

    def __init__(
        self,
        status: int = 200,
        text: str = "",
        headers: Optional[Dict[str, str]] = None
    ):
        """Initialize mock response.

        Args:
            status: HTTP status code
            text: Response body text
            headers: Response headers
        """
        self.status = status
        self._text = text
        self.headers = headers or {
            'content-type': 'text/html; charset=utf-8',
            'server': 'MockServer/1.0'
        }

    async def text(self) -> str:
        """Get response text."""
        return self._text

    async def json(self) -> Dict[str, Any]:
        """Get response as JSON."""
        import json
        return json.loads(self._text)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass


class MockHTTPSession:
    """Mock aiohttp ClientSession for testing."""

    def __init__(self, responses: Optional[Dict[str, str]] = None):
        """Initialize mock session.

        Args:
            responses: Dict mapping URLs to HTML responses
        """
        self.responses = responses or {}
        self.request_history = []
        self.call_count = 0

    def get(self, url: str, **kwargs) -> MockHTTPResponse:
        """Mock GET request.

        Args:
            url: Request URL
            **kwargs: Additional request parameters

        Returns:
            MockHTTPResponse
        """
        self.call_count += 1
        self.request_history.append({
            'method': 'GET',
            'url': url,
            'kwargs': kwargs
        })

        # Return configured response or default
        if url in self.responses:
            return MockHTTPResponse(
                status=200,
                text=self.responses[url]
            )
        else:
            return MockHTTPResponse(
                status=404,
                text='<html><body><h1>404 Not Found</h1></body></html>'
            )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass

    def reset(self):
        """Reset request history and call count."""
        self.request_history = []
        self.call_count = 0


class MockHTTPSessionWithErrors:
    """Mock HTTP session that raises errors."""

    def __init__(self, error_type: str = 'timeout'):
        """Initialize mock session with errors.

        Args:
            error_type: Type of error to raise (timeout, connection, forbidden)
        """
        self.error_type = error_type

    def get(self, url: str, **kwargs):
        """Raise mock error.

        Raises:
            Exception: Simulated HTTP error
        """
        if self.error_type == 'timeout':
            import asyncio
            raise asyncio.TimeoutError('Request timeout')
        elif self.error_type == 'connection':
            raise ConnectionError('Connection refused')
        elif self.error_type == 'forbidden':
            return MockHTTPResponse(
                status=403,
                text='<html><body><h1>403 Forbidden</h1></body></html>'
            )
        else:
            raise Exception(f'Unknown error: {self.error_type}')

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass


def create_mock_html_page(
    title: str,
    headings: list,
    content: str,
    meta_description: str = ""
) -> str:
    """Create mock HTML page.

    Args:
        title: Page title
        headings: List of heading texts
        content: Page content
        meta_description: Meta description

    Returns:
        HTML string
    """
    meta_tag = f'<meta name="description" content="{meta_description}">' if meta_description else ''

    headings_html = '\n'.join([f'<h{min(i+1, 6)}>{h}</h{min(i+1, 6)}>' for i, h in enumerate(headings)])

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <title>{title}</title>
    {meta_tag}
</head>
<body>
    {headings_html}
    <p>{content}</p>
</body>
</html>
"""


def create_mock_robots_txt(
    allowed_paths: list = None,
    disallowed_paths: list = None,
    crawl_delay: int = 0
) -> str:
    """Create mock robots.txt content.

    Args:
        allowed_paths: List of allowed paths
        disallowed_paths: List of disallowed paths
        crawl_delay: Crawl delay in seconds

    Returns:
        robots.txt content
    """
    allowed = allowed_paths or []
    disallowed = disallowed_paths or []

    lines = ['User-agent: *']

    for path in disallowed:
        lines.append(f'Disallow: {path}')

    for path in allowed:
        lines.append(f'Allow: {path}')

    if crawl_delay > 0:
        lines.append(f'Crawl-delay: {crawl_delay}')

    return '\n'.join(lines)
