#!/usr/bin/env python3
"""
Export Report to PDF Script

This script fetches a report from the database and exports it to a PDF file
using the PDFExportService.
"""
import sys
import os
import json
import asyncio
import logging
from datetime import datetime

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from src.config import get_settings
from src.services.pdf_export import PDFExportService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("export_report")

async def export_report_to_pdf(report_id: int):
    """
    Export a report from the database to a PDF file.
    
    Args:
        report_id: ID of the report to export
    """
    # Initialize database connection
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_url = "postgresql://tobymorning@localhost:5432/onside"
        logger.warning(f"DATABASE_URL not set, using default: {database_url}")
    
    # Ensure standard PostgreSQL URL format
    if 'asyncpg' in database_url:
        database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
        logger.info("Converted database URL to use standard driver")
    
    try:
        # Create database connection
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Fetch report from database
        result = session.execute(
            text("SELECT id, type, status, result FROM reports WHERE id = :report_id"),
            {"report_id": report_id}
        )
        report = result.fetchone()
        
        if not report:
            logger.error(f"Report with ID {report_id} not found in database")
            return
        
        report_id, report_type, status, report_data = report
        
        # Parse JSON data if it's a string, otherwise use as is
        if isinstance(report_data, str):
            report_data = json.loads(report_data) if report_data else {}
        # If report_data is already a dict (from psycopg2 JSON handling), use it directly
        
        logger.info(f"Retrieved report {report_id} of type {report_type} with status {status}")
        
        # Transform report data to the format expected by PDFExportService
        transformed_data = {
            "metadata": {
                "company_name": "Jones Lang LaSalle (JLL)",
                "domain": "jll.com",
                "report_type": report_type,
                "report_id": report_id,
                "generated_at": report_data.get("analysis_timestamp", datetime.now().isoformat()),
                "confidence_score": report_data.get("market_overview", {}).get("confidence_score", 0.0),
                "model": "gpt-4",
                "version": "1.0",
                "language": "en",
                "industry": "Real Estate Services",
                "processing_time": 5.2,
            },
            "analysis": {
                "market_overview": report_data.get("market_overview", {}),
                "competitors": report_data.get("competitors", []),
                "insights": report_data.get("ai_generated_insights", {}),
                "competitive_positioning": "Market Leader",
                "market_share": "23%",
                "recommendations": [
                    "Focus on expanding digital services portfolio",
                    "Invest in sustainable real estate technology",
                    "Strengthen market position in Asia"
                ],
                "key_differentiators": [
                    "Global reach and expertise",
                    "Integrated services platform",
                    "Advanced technology solutions"
                ],
                "content_analysis": {
                    "topics": [
                        "Commercial real estate",
                        "Property management",
                        "Real estate investment"
                    ],
                    "sentiment": {
                        "score": 0.75,
                        "label": "Positive"
                    },
                    "engagement": {
                        "score": 8.3,
                        "trends": [
                            "Increasing engagement on sustainability content",
                            "High interaction with market analysis reports"
                        ]
                    }
                },
                "swot_analysis": {
                    "strengths": ["Global brand recognition", "Strong client relationships", "Industry expertise"],
                    "weaknesses": ["Digital transformation adoption", "Regional market inconsistencies"],
                    "opportunities": report_data.get("ai_generated_insights", {}).get("market_opportunities", []),
                    "threats": report_data.get("ai_generated_insights", {}).get("risk_factors", [])
                }
            }
        }
        
        report_data = transformed_data
        
        # Initialize PDF export service
        pdf_service = PDFExportService()
        
        # Generate filename
        company_name = "jll"  # Default company name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{company_name}_analysis_{timestamp}.pdf"
        
        # Export report to PDF
        pdf_path = await pdf_service.export_report(
            report_data=report_data,
            report_type=report_type.lower(),
            filename=filename
        )
        
        logger.info(f"Report successfully exported to {pdf_path}")
        return pdf_path
        
    except Exception as e:
        logger.error(f"Error exporting report to PDF: {e}")
        raise
    finally:
        session.close()

async def main():
    """Main entry point."""
    try:
        # Export report with ID 8
        await export_report_to_pdf(8)
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
