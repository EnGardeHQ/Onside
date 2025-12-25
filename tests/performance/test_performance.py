#!/usr/bin/env python
"""
Performance Test for JLL Report Generator
Following Semantic Seed BDD/TDD Coding Standards V2.0

This script tests the performance of the optimized JLL report generator
by comparing the time required to generate reports with and without
the new concurrent processing optimizations.
"""

import asyncio
import time
import logging
from datetime import datetime
from complete_jll_report import JLLReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JLL_Performance_Test")

async def main():
    """Main test function that measures performance metrics."""
    logger.info("Starting performance test for JLL Report Generator")
    
    # Initialize the report generator
    report_generator = JLLReportGenerator()
    await report_generator.setup_services()
    
    # Test parameters
    company_name = "JLL"
    logger.info(f"Testing report generation for company: {company_name}")
    
    # Measure performance
    start_time = time.time()
    result = await report_generator.generate_report(company_name)
    end_time = time.time()
    
    # Calculate and log performance metrics
    execution_time = end_time - start_time
    logger.info(f"Report generation completed in {execution_time:.2f} seconds")
    
    # Extract performance metrics from the report data
    if "metadata" in result and "performance_metrics" in result["metadata"]:
        performance_metrics = result["metadata"]["performance_metrics"]
        logger.info(f"Performance metrics: {performance_metrics}")
    
    # Extract generation time from report metadata if available
    if "metadata" in result and "generation_time_seconds" in result["metadata"]:
        generation_time = result["metadata"]["generation_time_seconds"]
        logger.info(f"Reported generation time: {generation_time:.2f} seconds")
    
    # Log a summary of the report components
    logger.info("Report Components Generated:")
    if "insights" in result:
        for insight_type, insight_data in result["insights"].items():
            confidence = insight_data.get("confidence_score", "N/A")
            logger.info(f"- {insight_type.capitalize()} insights (confidence: {confidence})")
    
    if "competitors" in result:
        logger.info(f"- Competitor analysis for {len(result['competitors'])} competitors")
    
    if "pdf_path" in result:
        logger.info(f"- PDF report generated: {result['pdf_path']}")
    
    logger.info("Performance test completed successfully")
    return result

if __name__ == "__main__":
    asyncio.run(main())
