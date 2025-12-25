"""
Test script for Google Search Console integration.

This script tests the GoogleSearchConsoleService with a refresh token.
"""
import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_google_search_console(site_url: str):
    """Test the Google Search Console integration.
    
    Args:
        site_url: The URL of the site to test (must be verified in Search Console)
    """
    try:
        # Import here to catch import errors
        from src.services.seo.google_search_console_refresh import GoogleSearchConsoleService, GoogleSearchConsoleError
        
        logger.info("Initializing Google Search Console service...")
        service = GoogleSearchConsoleService()
        
        # Test listing sites (verifies authentication)
        logger.info("Listing available sites...")
        sites = service.list_sites()
        logger.info(f"Available sites: {[s['siteUrl'] for s in sites]}")
        
        # Test search analytics
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Last 7 days
        
        logger.info(f"Fetching search analytics for {site_url}...")
        results = service.get_search_analytics(
            site_url=site_url,
            start_date=start_date,
            end_date=end_date,
            dimensions=['query', 'page'],
            row_limit=10
        )
        
        logger.info(f"Retrieved {len(results)} rows of data")
        if results:
            logger.info("Sample result:")
            for i, row in enumerate(results[:3]):  # Show first 3 results
                logger.info(f"{i+1}. Query: {row.get('query', 'N/A')}")
                logger.info(f"   Page: {row.get('page', 'N/A')}")
                logger.info(f"   Clicks: {row.get('clicks', 0)}, Impressions: {row.get('impressions', 0)}")
        
        logger.info("✅ Google Search Console integration test completed successfully!")
        
    except ImportError as e:
        logger.error(f"Import error: {str(e)}")
        logger.error("Make sure you have installed the required dependencies:")
        logger.error("pip install --upgrade google-auth-oauthlib google-auth-httplib2 google-api-python-client python-dotenv")
        sys.exit(1)
    except GoogleSearchConsoleError as e:
        logger.error(f"Google Search Console error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Google Search Console integration')
    parser.add_argument('site_url', help='The URL of the site to test (must be verified in Search Console)')
    args = parser.parse_args()
    
    test_google_search_console(args.site_url)
