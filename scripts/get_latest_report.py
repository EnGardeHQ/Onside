#!/usr/bin/env python3
"""Script to retrieve the latest report from the database."""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://tobymorning@localhost:5432/onside')

# Import models after setting up environment
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.models.report import Report

async def get_latest_report():
    """Retrieve and display the most recent report from the database."""
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get the most recent report
        result = await session.execute(
            select(Report)
            .order_by(Report.created_at.desc())
            .limit(1)
        )
        report = result.scalars().first()
        
        if report:
            print(f"\n=== Report ID: {report.id} ===")
            print(f"Type: {report.type}")
            print(f"Status: {report.status}")
            print(f"Created: {report.created_at}")
            print(f"Parameters: {report.parameters}")
            print(f"Confidence Score: {report.confidence_score}")
            print("\nChain of Thought:")
            print(report.chain_of_thought)
            print("\n=== End of Report ===\n")
        else:
            print("No reports found in the database.")

if __name__ == "__main__":
    asyncio.run(get_latest_report())
