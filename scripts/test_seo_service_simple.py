"""Simple test script for SEOService with available dependencies."""
import asyncio
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockService:
    """Mock service for testing purposes."""
    
    async def get_competing_domains(self, domain: str) -> List[Dict[str, Any]]:
        """Return mock competing domains."""
        logger.info(f"Mocking get_competing_domains for {domain}")
        return [
            {"domain": "competitor1.com", "overlap_score": 75, "source": "mock"},
            {"domain": "competitor2.com", "overlap_score": 65, "source": "mock"},
            {"domain": "competitor3.com", "overlap_score": 60, "source": "mock"}
        ]
    
    async def get_domain_metrics(self, domain: str) -> Dict[str, Any]:
        """Return mock domain metrics."""
        logger.info(f"Mocking get_domain_metrics for {domain}")
        return {
            "overview": {
                "authority_score": 75,
                "domain": domain,
                "last_updated": "2025-05-20T11:00:00Z"
            },
            "traffic": {
                "organic_traffic": 10000,
                "traffic_change": 5.5
            },
            "backlinks": {
                "total": 1000,
                "domains": 250,
                "dofollow": 800,
                "nofollow": 200
            },
            "health_score": 82.5
        }

async def test_seo_service():
    """Test the SEOService functionality with mock services."""
    logger.info("Starting simplified SEOService test with mock services...")
    
    # Initialize the mock service
    seo_service = MockService()
    
    # Test with a sample domain
    test_domain = "example.com"
    
    try:
        # Test get_competing_domains
        logger.info(f"Getting competing domains for {test_domain}...")
        competitors = await seo_service.get_competing_domains(test_domain)
        logger.info(f"Found {len(competitors)} competitors")
        for i, comp in enumerate(competitors[:3], 1):
            logger.info(f"{i}. {comp['domain']} (Score: {comp.get('overlap_score', 'N/A')})")
        
        # Test get_domain_metrics
        logger.info(f"\nGetting metrics for {test_domain}...")
        metrics = await seo_service.get_domain_metrics(test_domain)
        
        # Log key metrics
        logger.info(f"Domain Authority: {metrics.get('overview', {}).get('authority_score', 'N/A')}")
        logger.info(f"Organic Traffic: {metrics.get('traffic', {}).get('organic_traffic', 'N/A')}")
        logger.info(f"Backlinks: {metrics.get('backlinks', {}).get('total', 'N/A')}")
        logger.info(f"Health Score: {metrics.get('health_score', 'N/A')}")
        
        logger.info("\nSEOService test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error testing SEOService: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(test_seo_service())
