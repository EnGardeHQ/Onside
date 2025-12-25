"""
Integration tests for Google Search Console service.
These tests make real API calls to Google's servers.
"""
import os
import sys
import logging
import pytest
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Skip these tests if we don't have the required credentials
pytestmark = pytest.mark.skipif(
    not all([
        os.getenv('PAGESPEED_CLIENT_ID'),
        os.getenv('Google Web CLIENT_SECRET'),
        os.getenv('GOOGLE_REFRESH_TOKEN')
    ]),
    reason="Missing required Google OAuth2 credentials"
)

class TestGoogleSearchConsoleIntegration:
    """Integration tests for Google Search Console service."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        from src.services.seo.google_search_console import GoogleSearchConsoleService
        self.service = GoogleSearchConsoleService()
        self.test_site = os.getenv('GOOGLE_SEARCH_CONSOLE_SITE', 'sc-domain:example.com')
        
        # Skip if we don't have a test site configured
        if not self.test_site:
            pytest.skip("No test site configured. Set GOOGLE_SEARCH_CONSOLE_SITE environment variable.")
    
    def test_authentication(self):
        """Test that we can authenticate with the Google Search Console API."""
        assert self.service.service is not None
        logger.info("Successfully authenticated with Google Search Console API")
    
    def test_get_search_analytics(self):
        """Test fetching search analytics data."""
        # Test with default parameters
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        logger.info(f"Fetching search analytics for {self.test_site} from {start_date} to {end_date}")
        
        results = self.service.get_search_analytics(
            site_url=self.test_site,
            start_date=start_date,
            end_date=end_date,
            dimensions=['query', 'page'],
            row_limit=10
        )
        
        logger.info(f"Retrieved {len(results)} rows of search analytics data")
        if results:
            logger.info(f"Sample result: {results[0]}")
        
        # We don't assert specific values since the data depends on the actual site
        assert isinstance(results, list)
    
    def test_get_search_analytics_with_filters(self):
        """Test fetching search analytics with specific filters."""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')  # Last 7 days
        
        logger.info(f"Fetching filtered search analytics for {self.test_site} from {start_date} to {end_date}")
        
        results = self.service.get_search_analytics(
            site_url=self.test_site,
            start_date=start_date,
            end_date=end_date,
            dimensions=['query', 'page', 'country', 'device'],
            row_limit=5
        )
        
        logger.info(f"Retrieved {len(results)} rows of filtered search analytics data")
        if results:
            logger.info(f"Sample filtered result: {results[0]}")
        
        assert isinstance(results, list)
