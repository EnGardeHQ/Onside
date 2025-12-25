"""Simple test script for SEOService."""
import asyncio
import logging
from src.services.seo.seo_service import SEOService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_seo_service():
    """Test the SEOService functionality."""
    logger.info("Starting SEOService test...")
    
    # Initialize the service
    seo_service = SEOService()
    
    # Test with a sample domain
    test_domain = "example.com"
    
    try:
        # Test get_competing_domains
        logger.info(f"Getting competing domains for {test_domain}...")
        competitors = await seo_service.get_competing_domains(test_domain)
        logger.info(f"Found {len(competitors)} competitors")
        for i, comp in enumerate(competitors[:3], 1):  # Show first 3 competitors
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
