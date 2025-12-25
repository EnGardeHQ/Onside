#!/usr/bin/env python3
"""
Generate Comprehensive AI/ML Report Script

This script demonstrates the AI/ML capabilities implemented in Sprint 4
by generating a comprehensive report that includes competitor analysis,
market analysis, and audience analysis for a specified domain.

Usage:
    python generate_comprehensive_report.py --domain https://www.us.jll.com/
"""
import asyncio
import argparse
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import get_settings
from src.database import get_db, Base
from src.models.report import Report, ReportType, ReportStatus
from src.models.company import Company
from src.models.competitor import Competitor
from src.services.report_generator import ReportGeneratorService
from src.services.data.competitor_data import CompetitorDataService
from src.services.data.metrics import MetricsService
from src.services.llm_provider import FallbackManager
from src.services.ai.competitor_analysis import CompetitorAnalysisService
from src.services.ai.market_analysis import MarketAnalysisService
from src.services.ai.audience_analysis import AudienceAnalysisService
from src.repositories.competitor_repository import CompetitorRepository
from src.repositories.competitor_metrics_repository import CompetitorMetricsRepository
from src.repositories.company_repository import CompanyRepository


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("comprehensive_report")


async def setup_database():
    """Set up database connection."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    return async_session


async def get_or_create_company(db: AsyncSession, domain: str) -> Company:
    """Get or create a company for the given domain."""
    company_repo = CompanyRepository(db)
    
    # Try to find existing company by domain
    company = await company_repo.get_by_domain(domain)
    
    if not company:
        # Create a new company
        logger.info(f"Creating new company for domain: {domain}")
        company_name = domain.split("//")[-1].split(".")[0].upper()
        company = Company(
            name=f"{company_name} Inc.",
            domain=domain,
            industry="Real Estate",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(company)
        await db.commit()
        await db.refresh(company)
    
    return company


async def get_or_create_competitors(db: AsyncSession, company_id: int) -> List[Competitor]:
    """Get or create competitors for the company."""
    competitor_repo = CompetitorRepository(db)
    
    # Try to find existing competitors
    competitors = await competitor_repo.get_by_company_id(company_id)
    
    if not competitors:
        # Create sample competitors for JLL
        logger.info(f"Creating sample competitors for company ID: {company_id}")
        competitor_data = [
            {"name": "CBRE Group", "domain": "https://www.cbre.com/", "industry": "Real Estate"},
            {"name": "Cushman & Wakefield", "domain": "https://www.cushmanwakefield.com/", "industry": "Real Estate"},
            {"name": "Colliers International", "domain": "https://www.colliers.com/", "industry": "Real Estate"},
            {"name": "Newmark Group", "domain": "https://www.nmrk.com/", "industry": "Real Estate"}
        ]
        
        competitors = []
        for data in competitor_data:
            competitor = Competitor(
                company_id=company_id,
                name=data["name"],
                domain=data["domain"],
                industry=data["industry"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(competitor)
            competitors.append(competitor)
        
        await db.commit()
        for competitor in competitors:
            await db.refresh(competitor)
    
    return competitors


async def generate_comprehensive_report(domain: str):
    """Generate a comprehensive report for the given domain."""
    # Set up database session
    async_session = await setup_database()
    
    async with async_session() as db:
        try:
            # Get or create company
            company = await get_or_create_company(db, domain)
            logger.info(f"Using company: {company.name} (ID: {company.id})")
            
            # Get or create competitors
            competitors = await get_or_create_competitors(db, company.id)
            competitor_ids = [competitor.id for competitor in competitors]
            logger.info(f"Using competitors: {[c.name for c in competitors]}")
            
            # Set up repositories
            competitor_repo = CompetitorRepository(db)
            metrics_repo = CompetitorMetricsRepository(db)
            
            # Set up services
            llm_manager = FallbackManager()
            competitor_data_service = CompetitorDataService(competitor_repo, metrics_repo)
            metrics_service = MetricsService()
            
            # Initialize AI services
            competitor_analysis = CompetitorAnalysisService(
                llm_manager=llm_manager,
                competitor_data_service=competitor_data_service,
                metrics_service=metrics_service
            )
            
            # Initialize report generator service
            report_generator = ReportGeneratorService(db)
            
            # Generate competitor analysis report
            logger.info("Generating competitor analysis report...")
            competitor_report = await report_generator.create_report(
                user_id=1,  # Assuming user ID 1 exists
                report_type=ReportType.COMPETITOR,
                parameters={
                    "competitor_ids": competitor_ids,
                    "metrics": ["engagement", "visibility", "growth", "sentiment"],
                    "timeframe": "last_quarter",
                    "with_chain_of_thought": True,
                    "confidence_threshold": 0.6
                }
            )
            
            # Generate market analysis report
            logger.info("Generating market analysis report...")
            market_report = await report_generator.create_report(
                user_id=1,
                report_type=ReportType.MARKET,
                parameters={
                    "company_id": company.id,
                    "sectors": ["commercial_real_estate", "residential_real_estate", "property_management"],
                    "timeframe": "last_quarter",
                    "with_chain_of_thought": True,
                    "include_predictions": True
                }
            )
            
            # Generate audience analysis report
            logger.info("Generating audience analysis report...")
            audience_report = await report_generator.create_report(
                user_id=1,
                report_type=ReportType.AUDIENCE,
                parameters={
                    "company_id": company.id,
                    "segment_id": None,  # All segments
                    "timeframe": "last_quarter",
                    "demographic_filters": {
                        "age_range": ["25-34", "35-44", "45-54"],
                        "interests": ["real_estate", "investment", "commercial_property"]
                    },
                    "with_chain_of_thought": True
                }
            )
            
            # Wait for reports to complete
            report_ids = [competitor_report.id, market_report.id, audience_report.id]
            completed_reports = []
            
            for _ in range(30):  # Wait up to 30 seconds
                all_completed = True
                reports = []
                
                for report_id in report_ids:
                    report = await report_generator.get_report(report_id)
                    reports.append(report)
                    if report.status != ReportStatus.COMPLETED:
                        all_completed = False
                
                if all_completed:
                    completed_reports = reports
                    break
                
                await asyncio.sleep(1)
            
            # Print report results
            logger.info("\n" + "="*80)
            logger.info("COMPREHENSIVE REPORT RESULTS")
            logger.info("="*80)
            
            for report in completed_reports:
                logger.info(f"\nReport Type: {report.type.value}")
                logger.info(f"Status: {report.status.value}")
                logger.info(f"Confidence Score: {report.confidence_score}")
                
                if report.result:
                    logger.info(f"Results: {json.dumps(report.result, indent=2)}")
                
                if report.chain_of_thought:
                    logger.info("\nChain of Thought Reasoning:")
                    for step in report.chain_of_thought.get("steps", []):
                        logger.info(f"- {step}")
                
                logger.info("-"*80)
            
            logger.info("\nComprehensive report generation completed!")
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {str(e)}")
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a comprehensive AI/ML report")
    parser.add_argument("--domain", type=str, default="https://www.us.jll.com/",
                        help="Domain to analyze")
    
    args = parser.parse_args()
    
    asyncio.run(generate_comprehensive_report(args.domain))
