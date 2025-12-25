"""
Test script for report generation with PDF export.

This script demonstrates the enhanced report generation capabilities
with Sprint 4 AI/ML features and PDF export.
"""
import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path

import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from services.report_generator import ReportGeneratorService
from services.pdf_export import PDFExportService
from models.report import Report, ReportType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_competitor_report():
    """Generate and export a competitor analysis report."""
    report_generator = ReportGeneratorService()
    pdf_export = PDFExportService(export_dir="exports")
    
    # Create test report
    report = Report(
        type=ReportType.COMPETITOR,
        parameters={
            "competitor_ids": [1, 2],  # Example competitor IDs
            "metrics": ["engagement", "growth", "sentiment"],
            "timeframe": {
                "start": datetime.now() - timedelta(days=30),
                "end": datetime.now()
            },
            "with_chain_of_thought": True
        }
    )
    
    try:
        # Generate report
        result = await report_generator._generate_competitor_report(report)
        print("\n=== Competitor Report Generated ===")
        print(f"Confidence Score: {result['metadata']['confidence_score']:.2f}")
        print(f"Chain of Thought: {result['metadata']['chain_of_thought'][:200]}...")
        
        # Export to PDF
        pdf_path = await pdf_export.export_report(result, "competitor")
        print(f"\nPDF exported to: {pdf_path}")
        
        # Print key insights
        print("\nKey Insights:")
        for insight in result["analysis"]["recommendations"][:3]:
            print(f"- {insight}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

async def test_market_report():
    """Generate and export a market analysis report."""
    report_generator = ReportGeneratorService()
    pdf_export = PDFExportService(export_dir="exports")
    
    # Create test report
    report = Report(
        type=ReportType.MARKET,
        parameters={
            "sectors": ["technology", "finance"],
            "timeframe": {
                "start": datetime.now() - timedelta(days=30),
                "end": datetime.now()
            },
            "with_chain_of_thought": True
        }
    )
    
    try:
        # Generate report
        result = await report_generator._generate_market_report(report)
        print("\n=== Market Report Generated ===")
        print(f"Confidence Score: {result['metadata']['confidence_score']:.2f}")
        print(f"Chain of Thought: {result['metadata']['chain_of_thought'][:200]}...")
        
        # Export to PDF
        pdf_path = await pdf_export.export_report(result, "market")
        print(f"\nPDF exported to: {pdf_path}")
        
        # Print predictions
        print("\nMarket Predictions:")
        for pred in result["analysis"]["market_predictions"][:3]:
            print(f"- {pred}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

async def test_audience_report():
    """Generate and export an audience analysis report."""
    report_generator = ReportGeneratorService()
    pdf_export = PDFExportService(export_dir="exports")
    
    # Create test report
    report = Report(
        type=ReportType.AUDIENCE,
        parameters={
            "company_id": 1,
            "segments": ["active_users", "churned"],
            "timeframe": {
                "start": datetime.now() - timedelta(days=30),
                "end": datetime.now()
            },
            "metrics": ["views", "likes", "shares", "comments"],
            "with_chain_of_thought": True
        }
    )
    
    try:
        # Generate report
        result = await report_generator._generate_audience_report(report)
        print("\n=== Audience Report Generated ===")
        print(f"Confidence Score: {result['metadata']['confidence_score']:.2f}")
        print(f"Chain of Thought: {result['metadata']['chain_of_thought'][:200]}...")
        
        # Export to PDF
        pdf_path = await pdf_export.export_report(result, "audience")
        print(f"\nPDF exported to: {pdf_path}")
        
        # Print personas
        print("\nAudience Personas:")
        for persona in result["analysis"]["audience_personas"][:3]:
            print(f"- {persona}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    """Run all report generation tests."""
    # Create exports directory
    Path("exports").mkdir(exist_ok=True)
    
    print("Testing Enhanced Report Generation with PDF Export...")
    print("Using GPT-4 for AI/ML insights")
    
    await test_competitor_report()
    await test_market_report()
    await test_audience_report()

if __name__ == "__main__":
    asyncio.run(main())
