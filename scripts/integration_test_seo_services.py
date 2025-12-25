"""Integration test for SEO services with real API connections."""
import asyncio
import logging
import os
from dotenv import load_dotenv
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class SEOServiceTester:
    """Test class for SEO services with real API connections."""
    
    def __init__(self):
        """Initialize the tester with real service instances."""
        from src.services.seo.semrush_service import SemrushService
        from src.services.seo.serp_service import SerpService
        
        # Initialize services with API keys from environment
        self.semrush = SemrushService(api_key=os.getenv('SEMRUSH_API_KEY', ''))
        self.serp = SerpService(api_key=os.getenv('SERPAPI_API_KEY', ''))
    
    async def test_semrush_competitors(self, domain: str):
        """Test SEMrush competitor analysis."""
        try:
            logger.info(f"Testing SEMrush competitor analysis for {domain}")
            competitors = await self.semrush.get_competing_domains(domain)
            logger.info(f"Found {len(competitors)} competitors from SEMrush")
            for i, comp in enumerate(competitors[:5], 1):
                logger.info(f"  {i}. {comp.get('domain', 'N/A')} - Score: {comp.get('overlap_score', 'N/A')}")
            return True
        except Exception as e:
            logger.error(f"SEMrush test failed: {str(e)}")
            return False
    
    async def test_serp_rankings(self, domain: str, query: str = None):
        """Test SERP API for domain rankings."""
        try:
            if not query:
                query = f"site:{domain}"
                
            logger.info(f"Testing SERP API for domain: {domain} with query: {query}")
            
            # Use the SerpService's internal method to make the API call
            results = await self.serp.search(query)
            
            if not results or 'organic_results' not in results:
                logger.warning("No organic results found in SERP response")
                return False
                
            logger.info(f"Found {len(results['organic_results'])} organic results")
            
            # Check if the domain appears in the top 100 results
            domain_rank = None
            for idx, result in enumerate(results['organic_results'][:100], 1):
                if domain.lower() in result.get('link', '').lower():
                    domain_rank = idx
                    break
            
            if domain_rank:
                logger.info(f"Domain found at position {domain_rank} in SERP results")
            else:
                logger.info("Domain not found in top 100 SERP results")
                
            # Log top 5 results
            logger.info("Top 5 SERP results:")
            for i, result in enumerate(results['organic_results'][:5], 1):
                logger.info(f"  {i}. {result.get('title', 'No title')} - {result.get('link', 'No URL')}")
                
            return True
            
        except Exception as e:
            logger.error(f"SERP API test failed: {str(e)}")
            return False

async def main():
    """Run integration tests for SEO services."""
    tester = SEOServiceTester()
    
    # Test domain - using a well-known site that should have data
    test_domain = "example.com"
    
    logger.info("=" * 80)
    logger.info(f"Starting SEO Service Integration Tests for {test_domain}")
    logger.info("=" * 80)
    
    # Test SEMrush
    logger.info("\n[1/2] Testing SEMrush Integration...")
    semrush_success = await tester.test_semrush_competitors(test_domain)
    logger.info(f"✓ SEMrush test {'succeeded' if semrush_success else 'failed'}")
    
    # Test SERP API
    logger.info("\n[2/2] Testing SERP API Integration...")
    serp_success = await tester.test_serp_rankings(test_domain)
    logger.info(f"✓ SERP API test {'succeeded' if serp_success else 'failed'}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Integration Test Summary:")
    logger.info(f"- SEMrush: {'✓ PASS' if semrush_success else '✗ FAIL'}")
    logger.info(f"- SERP API: {'✓ PASS' if serp_success else '✗ FAIL'}")
    logger.info("=" * 80)
    
    if semrush_success and serp_success:
        logger.info("All SEO service tests completed successfully!")
    else:
        logger.warning("Some SEO service tests failed. Check logs for details.")

if __name__ == "__main__":
    asyncio.run(main())
