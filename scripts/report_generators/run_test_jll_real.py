"""
Real-world test for JLL Analysis Workflow.

This script performs a test run of the full JLL analysis workflow using the actual database 
and real services, following Semantic Seed BDD/TDD standards.

The test will:
1. Verify database connection and JLL company existence
2. Create a test campaign for JLL
3. Identify competitors
4. Generate a comprehensive report with Sprint 4 AI/ML capabilities
5. Export a PDF with visualizations

Following Semantic Seed BDD/TDD standards with real database connectivity.
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import logging
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure we have an exports directory
Path("exports").mkdir(exist_ok=True)

# Import analyze_jll module for database connection and other functionality
from sqlalchemy import text
from analyze_jll import create_db_session

# Import service modules
from src.services.campaign.campaign_service import CampaignService
from src.services.pdf_export import PDFExportService
from src.services.web_scraper.web_scraper import WebScraperService
from src.services.link_search.link_search import LinkSearchService
from src.services.engagement_extraction.engagement_extraction import EngagementExtractionService
from src.workflow.scraping_workflow import scrape_company_data

async def run_real_jll_test():
    """
    Run a real-world test of the JLL analysis workflow using actual database.
    No mocks are used in this test to ensure proper BDD/TDD verification.
    """
    logger.info("Starting real-world JLL analysis workflow test")
    
    try:
        # Step 1: Verify database connection and JLL company existence
        logger.info("Step 1: Verifying database connection and JLL company existence")
        async with create_db_session() as db:
            # Check for JLL company
            jll_query = "SELECT id, name, website FROM companies WHERE name ILIKE '%JLL%' OR name ILIKE '%Jones Lang LaSalle%' LIMIT 1"
            jll_company = await db.fetch_one(jll_query)
            
            if not jll_company:
                logger.error("JLL company not found in database. Please add it first.")
                return None
            
            logger.info(f"Found JLL company: {jll_company['name']} (ID: {jll_company['id']})")
            jll_id = jll_company['id']
        
        # Step 2: Create campaign
        logger.info("Step 2: Creating test campaign for JLL")
        async with create_db_session() as db:
            campaign_service = CampaignService(db)
            campaign_result = await campaign_service.create_campaign(
                name=f"JLL Analysis Test - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                primary_company_id=jll_id,
                description="Test campaign for JLL analysis workflow verification"
            )
            
            if not campaign_result["success"]:
                logger.error(f"Failed to create campaign: {campaign_result.get('error', 'Unknown error')}")
                return None
            
            campaign_id = campaign_result["campaign"]["id"]
            logger.info(f"Created campaign with ID {campaign_id}")
        
        # Step 3: Identify competitors
        logger.info("Step 3: Identifying competitors")
        async with create_db_session() as db:
            campaign_service = CampaignService(db)
            competitors = await campaign_service.identify_competitors(
                campaign_id=campaign_id,
                max_competitors=3  # Limit for testing
            )
            
            if not competitors:
                logger.warning("No competitors identified")
            else:
                logger.info(f"Identified {len(competitors)} competitors:")
                for competitor in competitors:
                    logger.info(f"  - {competitor['name']} (relevance: {competitor['relevance_score']:.2f})")
        
        # Step 4: Run limited scraping (optional for faster testing)
        run_scraping = True  # Set to True to include scraping in the test
        
        if run_scraping:
            logger.info("Step 4: Running web scraping for content")
            async with create_db_session() as db:
                web_scraper = WebScraperService(db)
                link_search = LinkSearchService(db)
                engagement_extraction = EngagementExtractionService(db)
                
                try:
                    # Scrape JLL data (with limits for testing)
                    scrape_results = await scrape_company_data(
                        web_scraper, 
                        link_search,
                        engagement_extraction,
                        company_id=jll_id,
                        max_links=2  # Limit for testing
                    )
                    
                    if scrape_results["success"]:
                        logger.info(f"Successfully scraped {scrape_results.get('links_scraped', 0)} links")
                    else:
                        logger.warning(f"Scraping had issues: {scrape_results.get('message', 'Unknown issue')}")
                    
                except Exception as e:
                    logger.error(f"Error during scraping: {str(e)}")
        else:
            logger.info("Step 4: Skipping web scraping (disabled for faster testing)")
        
        # Step 5: Generate test report with AI/ML capabilities
        logger.info("Step 5: Generating report with AI/ML analysis")
        
        try:
            from analyze_jll import generate_jll_report
            
            report_result = await generate_jll_report(
                company_id=jll_id,
                company_name=jll_company['name'],
                report_name=f"JLL Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                max_competitors=3
            )
            
            if report_result and 'pdf_path' in report_result:
                pdf_path = report_result['pdf_path']
                logger.info(f"Successfully generated report with PDF at: {pdf_path}")
                
                # Verify PDF exists
                if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                    logger.info(f"PDF file exists with size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
                    return pdf_path
                else:
                    logger.error("PDF file not found or empty")
                    return None
            else:
                logger.error("Failed to generate report")
                return None
                
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
            
    except Exception as e:
        logger.error(f"Error in JLL analysis workflow test: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    logger.info("=== Starting JLL Analysis Real-World Test ===")
    result = asyncio.run(run_real_jll_test())
    
    if result:
        logger.info(f"=== JLL Analysis Test: COMPLETED SUCCESSFULLY ===\nReport at: {result}")
        sys.exit(0)
    else:
        logger.error("=== JLL Analysis Test: FAILED ===")
        sys.exit(1)
