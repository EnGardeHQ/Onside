#!/usr/bin/env python3
"""
Debug JLL Report Generator
A simplified implementation to debug and resolve the recursion issues
"""

import sys
import os
import asyncio
import datetime
import json
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Load database configuration
DATABASE = {
    "host": "localhost",
    "port": 5432,
    "database": "onside",
    "user": "tobymorning",
    "password": ""
}

# Create async engine for PostgreSQL
DB_URL = f"postgresql+asyncpg://{DATABASE['user']}:{DATABASE['password']}@{DATABASE['host']}:{DATABASE['port']}/{DATABASE['database']}"
engine = create_async_engine(DB_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_jll_company_data(session: AsyncSession):
    """Get JLL company data from the database."""
    try:
        result = await session.execute(text(
            """
            SELECT c.*
            FROM companies c
            WHERE c.name LIKE :name
            LIMIT 1
            """
        ), {"name": "%JLL%"})
        
        company = result.fetchone()
        if company:
            logger.info(f"✅ Found company: {company.name} (ID: {company.id})")
            return company
        else:
            logger.error("❌ JLL company not found")
            return None
    except Exception as e:
        logger.error(f"❌ Error retrieving company data: {str(e)}")
        return None

async def get_metrics(session: AsyncSession, company_id: int):
    """Get metrics for the company."""
    try:
        result = await session.execute(text(
            """
            SELECT metric_type, value, data_quality_score, confidence_score, metric_date
            FROM competitor_metrics
            WHERE competitor_id = :company_id
            ORDER BY metric_date DESC
            """
        ), {"company_id": company_id})
        
        metrics = result.fetchall()
        logger.info(f"✅ Retrieved {len(metrics)} metrics for company ID: {company_id}")
        return metrics
    except Exception as e:
        logger.error(f"❌ Error retrieving metrics: {str(e)}")
        return []

async def get_competitors(session: AsyncSession, company_id: int):
    """Get competitors for the company."""
    try:
        result = await session.execute(text(
            """
            SELECT comp.* 
            FROM competitors comp
            WHERE comp.company_id = :company_id
            ORDER BY comp.market_share DESC
            """
        ), {"company_id": company_id})
        
        competitors = result.fetchall()
        logger.info(f"✅ Retrieved {len(competitors)} competitors for company ID: {company_id}")
        return competitors
    except Exception as e:
        logger.error(f"❌ Error retrieving competitors: {str(e)}")
        return []

async def generate_mock_insights():
    """Generate mock insights for debugging purposes."""
    # Mock competitor analysis insights
    competitor_insights = {
        "insights": {
            "trends": "Market share trends show steady growth for JLL in commercial real estate services.",
            "opportunities": "Expansion opportunities in emerging markets and proptech integration.",
            "threats": "Increasing competition from technology-driven real estate platforms.",
            "recommendations": "Strengthen digital transformation initiatives and focus on sustainability services."
        },
        "confidence_score": 0.92,
        "data_quality_score": 0.88
    }
    
    # Mock market analysis insights
    market_analysis = {
        "insights": {
            "sector_growth": "Commercial real estate services sector shows 5.2% annual growth.",
            "key_trends": "Increasing demand for integrated facility management and ESG compliance services.",
            "market_dynamics": "Global market driven by corporate outsourcing and technology integration.",
            "predictions": "Expected 15% growth in demand for sustainability consulting over next 3 years."
        },
        "confidence_score": 0.89,
        "data_quality_score": 0.85
    }
    
    # Mock audience analysis insights
    audience_analysis = {
        "insights": {
            "demographics": "Primary audience includes corporate real estate decision-makers (58%) and facility managers (22%).",
            "engagement": "Highest engagement with sustainability content (43% higher than average).",
            "persona": "Key decision-maker persona is typically a senior executive with 15+ years experience.",
            "recommendations": "Focus content strategy on ROI case studies and sustainability benchmarking."
        },
        "confidence_score": 0.90,
        "data_quality_score": 0.87
    }
    
    return {
        "competitor_analysis": competitor_insights,
        "market_analysis": market_analysis,
        "audience_analysis": audience_analysis
    }

async def generate_pdf_report(company_data, metrics, insights):
    """Generate a mock PDF report."""
    report_file = f"JLL_Report_{datetime.datetime.now().strftime('%Y_%m_%d')}.pdf"
    
    # In a real implementation, we would use reportlab to generate a PDF
    # For debugging, we'll just save the JSON data
    report_data = {
        "company": {
            "id": company_data.id,
            "name": company_data.name,
            "industry": getattr(company_data, "industry", "Real Estate Services"),
            "description": getattr(company_data, "description", "Global commercial real estate services company")
        },
        "report_date": datetime.datetime.now().isoformat(),
        "metrics": [
            {
                "type": metric.metric_type,
                "value": metric.value,
                "quality": metric.data_quality_score,
                "confidence": metric.confidence_score,
                "date": metric.metric_date.isoformat() if hasattr(metric, "metric_date") else None
            } for metric in metrics
        ],
        "insights": insights
    }
    
    with open(f"debug_{report_file.replace('.pdf', '.json')}", "w") as f:
        json.dump(report_data, f, indent=2, default=str)
    
    logger.info(f"✅ Report data saved to debug_{report_file.replace('.pdf', '.json')}")
    return report_file

async def main():
    """Main function to generate a debug JLL report."""
    logger.info("🚀 Starting Debug JLL Report Generator")
    
    # Create an async session
    async with async_session() as session:
        try:
            # Step 1: Get JLL company data
            company = await get_jll_company_data(session)
            if not company:
                logger.error("❌ Cannot proceed without company data")
                return
            
            # Step 2: Get metrics
            metrics = await get_metrics(session, company.id)
            
            # Step 3: Get competitors
            competitors = await get_competitors(session, company.id)
            
            # Step 4: Generate mock insights
            logger.info("Generating mock insights for debugging")
            insights = await generate_mock_insights()
            
            # Step 5: Generate a mock PDF report
            report_file = await generate_pdf_report(company, metrics, insights)
            
            logger.info(f"✅ Debug report generation completed successfully: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ Error in debug report generation: {str(e)}")
        finally:
            # Clean up
            await session.close()
            logger.info("✅ Session closed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
        logger.info("✅ Debug JLL report generation completed")
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
    finally:
        logger.info("✅ Debug script execution finished")
