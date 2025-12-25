"""Direct test for SEMrush and SERP API services without importing the full SEOService."""
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

async def test_semrush_direct(domain: str):
    """Test SEMrush API directly."""
    try:
        from src.services.seo.semrush_service import SemrushService
        
        api_key = os.getenv('SEMRUSH_API_KEY')
        if not api_key:
            logger.warning("SEMRUSH_API_KEY not found in environment variables")
            return False
            
        logger.info(f"Testing SEMrush API with domain: {domain}")
        semrush = SemrushService(api_key=api_key)
        
        # Test competitor analysis
        logger.info("Fetching competing domains...")
        competitors = await semrush.get_competing_domains(domain)
        logger.info(f"Found {len(competitors)} competitors")
        
        if not competitors:
            logger.warning("No competitors found - check API key and domain")
            return False
            
        # Log top 5 competitors
        for i, comp in enumerate(competitors[:5], 1):
            logger.info(f"  {i}. {comp.get('domain', 'N/A')} - Score: {comp.get('overlap_score', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"SEMrush test failed: {str(e)}", exc_info=True)
        return False

async def test_serp_direct(domain: str):
    """Test SERP API directly."""
    try:
        from src.services.seo.serp_service import SerpService
        
        api_key = os.getenv('SERPAPI_API_KEY')
        if not api_key:
            logger.warning("SERPAPI_API_KEY not found in environment variables")
            return False
            
        query = f"site:{domain}"
        logger.info(f"Testing SERP API with query: {query}")
        
        serp = SerpService(api_key=api_key)
        
        # Test search
        logger.info("Performing search...")
        results = await serp.search(query)
        
        if not results or 'organic_results' not in results:
            logger.error("Invalid response from SERP API")
            return False
            
        logger.info(f"Found {len(results['organic_results'])} organic results")
        
        # Log top 5 results
        logger.info("Top 5 results:")
        for i, result in enumerate(results['organic_results'][:5], 1):
            title = result.get('title', 'No title')
            link = result.get('link', 'No URL')
            logger.info(f"  {i}. {title} - {link}")
        
        return True
        
    except Exception as e:
        logger.error(f"SERP API test failed: {str(e)}", exc_info=True)
        return False

async def main():
    """Run direct integration tests."""
    # Test with a well-known domain
    test_domain = "example.com"
    
    logger.info("=" * 80)
    logger.info(f"Starting Direct SEO Service Tests for {test_domain}")
    logger.info("=" * 80)
    
    # Test SEMrush
    logger.info("\n[1/2] Testing SEMrush Direct Integration...")
    semrush_success = await test_semrush_direct(test_domain)
    logger.info(f"✓ SEMrush test {'succeeded' if semrush_success else 'failed'}")
    
    # Test SERP API
    logger.info("\n[2/2] Testing SERP API Direct Integration...")
    serp_success = await test_serp_direct(test_domain)
    logger.info(f"✓ SERP API test {'succeeded' if serp_success else 'failed'}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Direct Integration Test Summary:")
    logger.info(f"- SEMrush: {'✓ PASS' if semrush_success else '✗ FAIL'}")
    logger.info(f"- SERP API: {'✓ PASS' if serp_success else '✗ FAIL'}")
    logger.info("=" * 80)
    
    if semrush_success and serp_success:
        logger.info("All direct SEO service tests completed successfully!")
    else:
        logger.warning("Some direct SEO service tests failed. Check logs for details.")

if __name__ == "__main__":
    asyncio.run(main())
