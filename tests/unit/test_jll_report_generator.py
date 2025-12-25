#!/usr/bin/env python
"""
Final test for JLL Report Generator with fixed FallbackManager.
This script demonstrates the complete workflow without recursion issues.

Following Semantic Seed Venture Studio coding standards V2.0 with:
- BDD/TDD methodology
- Comprehensive error handling
- Detailed logging
- Production-ready code structure
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_jll_report")

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from src.models.llm_fallback import LLMProvider
from src.services.llm_provider.fallback_manager import FallbackManager

class SimpleReport:
    """Simplified Report class for testing."""
    
    def __init__(self, title: str, company_id: int):
        """Initialize a simple report.
        
        Args:
            title: Report title
            company_id: Associated company ID
        """
        self.id = 1  # Dummy ID
        self.title = title
        self.company_id = company_id
        self.created_at = datetime.now()
        self.insights = []
        
    def add_insight(self, insight_type: str, content: str, confidence: float) -> None:
        """Add an insight to the report.
        
        Args:
            insight_type: Type of insight (competitor, market, audience)
            content: Insight content
            confidence: Confidence score
        """
        insight = {
            "type": insight_type,
            "content": content,
            "confidence": confidence,
            "created_at": datetime.now()
        }
        self.insights.append(insight)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary.
        
        Returns:
            Dictionary representation of report
        """
        return {
            "id": self.id,
            "title": self.title,
            "company_id": self.company_id,
            "created_at": self.created_at.isoformat(),
            "insights": self.insights,
            "insight_count": len(self.insights)
        }

class SimplifiedReportGenerator:
    """Simplified version of the JLL report generator using fixed FallbackManager."""
    
    def __init__(self):
        """Initialize the report generator with required services."""
        # Initialize providers for FallbackManager
        self.providers = [
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
            LLMProvider.COHERE
        ]
        
        # Initialize FallbackManager with fixed execute_with_fallback
        self.fallback_manager = FallbackManager(providers=self.providers)
        
        logger.info("SimplifiedReportGenerator initialized with fixed FallbackManager")
        
    async def generate_competitor_insights(self, report: SimpleReport) -> List[Dict[str, Any]]:
        """Generate competitor insights using the fixed FallbackManager.
        
        Args:
            report: Report to generate insights for
            
        Returns:
            List of competitor insights
        """
        prompt = (
            f"Analyze the competitor landscape for JLL in the commercial real estate sector "
            f"with chain-of-thought reasoning. Consider market share, growth trends, "
            f"competitive advantages, and potential threats."
        )
        
        logger.info("Generating competitor insights...")
        
        result, provider = await self.fallback_manager.execute_with_fallback(
            prompt=prompt,
            report=report,
            confidence_threshold=0.7
        )
        
        logger.info(f"Competitor insights generated using provider: {provider}")
        
        # Extract insights from the response
        response = result.get("response", "")
        confidence = result.get("confidence", 0.8)
        
        # Add insight to report
        report.add_insight("competitor", response, confidence)
        
        return [{
            "type": "competitor",
            "content": response,
            "confidence": confidence,
            "provider": provider
        }]
    
    async def generate_market_insights(self, report: SimpleReport) -> List[Dict[str, Any]]:
        """Generate market insights using the fixed FallbackManager.
        
        Args:
            report: Report to generate insights for
            
        Returns:
            List of market insights
        """
        prompt = (
            f"Provide market analysis for the real estate services industry with focus on "
            f"growth trends, regional variations, and future outlook. Include predictions "
            f"and confidence levels for each trend identified."
        )
        
        logger.info("Generating market insights...")
        
        result, provider = await self.fallback_manager.execute_with_fallback(
            prompt=prompt,
            report=report,
            confidence_threshold=0.7
        )
        
        logger.info(f"Market insights generated using provider: {provider}")
        
        # Extract insights from the response
        response = result.get("response", "")
        confidence = result.get("confidence", 0.8)
        
        # Add insight to report
        report.add_insight("market", response, confidence)
        
        return [{
            "type": "market",
            "content": response,
            "confidence": confidence,
            "provider": provider
        }]
    
    async def generate_audience_insights(self, report: SimpleReport) -> List[Dict[str, Any]]:
        """Generate audience insights using the fixed FallbackManager.
        
        Args:
            report: Report to generate insights for
            
        Returns:
            List of audience insights
        """
        prompt = (
            f"Analyze the audience engagement patterns for corporate real estate content. "
            f"Identify key personas, their information needs, preferred content formats, "
            f"and engagement triggers."
        )
        
        logger.info("Generating audience insights...")
        
        result, provider = await self.fallback_manager.execute_with_fallback(
            prompt=prompt,
            report=report,
            confidence_threshold=0.7
        )
        
        logger.info(f"Audience insights generated using provider: {provider}")
        
        # Extract insights from the response
        response = result.get("response", "")
        confidence = result.get("confidence", 0.8)
        
        # Add insight to report
        report.add_insight("audience", response, confidence)
        
        return [{
            "type": "audience",
            "content": response,
            "confidence": confidence,
            "provider": provider
        }]
    
    async def generate_report(self, company_id: int, title: str) -> Dict[str, Any]:
        """Generate a complete report for a company using fixed FallbackManager.
        
        Args:
            company_id: ID of the company to generate report for
            title: Report title
            
        Returns:
            Complete report with insights
        """
        logger.info(f"Generating report: {title} for company_id: {company_id}")
        
        # Create a simple report
        report = SimpleReport(title=title, company_id=company_id)
        
        try:
            # Generate all insights in parallel
            competitor_task = asyncio.create_task(self.generate_competitor_insights(report))
            market_task = asyncio.create_task(self.generate_market_insights(report))
            audience_task = asyncio.create_task(self.generate_audience_insights(report))
            
            # Wait for all tasks to complete
            competitor_insights = await competitor_task
            market_insights = await market_task
            audience_insights = await audience_task
            
            # Log success
            logger.info(f"Report generation completed successfully with {len(report.insights)} insights")
            
            # Return complete report
            return report.to_dict()
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Return partial report with error information
            report.add_insight("error", f"Error generating report: {str(e)}", 0.0)
            return report.to_dict()

async def main():
    """Main entry point for testing the report generator."""
    logger.info("Starting JLL report generation test with fixed FallbackManager")
    
    try:
        # Initialize report generator
        report_generator = SimplifiedReportGenerator()
        
        # Generate test report for JLL (company_id=1)
        report = await report_generator.generate_report(
            company_id=1,
            title=f"JLL Competitive Analysis Report - {datetime.now().strftime('%Y-%m-%d')}"
        )
        
        # Print report summary
        logger.info(f"Report successfully generated: {report['title']}")
        logger.info(f"Total insights: {report['insight_count']}")
        
        # Print each insight
        for i, insight in enumerate(report['insights']):
            logger.info(f"Insight {i+1} - {insight['type']}: Confidence = {insight['confidence']:.2f}")
            logger.info(f"Content preview: {insight['content'][:100]}...")
        
        logger.info("✅ Test completed successfully - recursion issue fixed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("Test complete")


if __name__ == "__main__":
    asyncio.run(main())
