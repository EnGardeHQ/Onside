#!/usr/bin/env python
"""
Script to display the contents of the latest TCS report.
Following Semantic Seed Venture Studio Coding Standards V2.0.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text


async def main():
    """
    Retrieve and display the latest TCS report from the database.
    """
    # Connect to the database following project requirements
    engine = create_async_engine('postgresql+asyncpg://tobymorning@localhost:5432/onside')
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        # Query the latest TCS report
        result = await session.execute(text(
            """
            SELECT content_text, content_metadata 
            FROM contents 
            WHERE title LIKE '%TCS Competitive Analysis Report%' 
            ORDER BY id DESC LIMIT 1
            """
        ))
        
        content = result.fetchone()
        if not content:
            print('No TCS report found')
            return
            
        # Parse the report data
        report_data = json.loads(content[0])
        metadata = report_data.get('metadata', {})
        analysis = report_data.get('analysis', {})
        
        # Display report summary
        print(f"\nTCS REPORT SUMMARY\n{'=' * 20}")
        print(f"Company: {metadata.get('company_name')}")
        print(f"Report ID: {metadata.get('report_id')}")
        print(f"Generated: {metadata.get('generated_at')}")
        print(f"Confidence Score: {metadata.get('confidence_score')}")
        print(f"Model: {metadata.get('model')} (Provider: {metadata.get('provider')})")
        
        # Display key insights
        print(f"\nKEY INSIGHTS\n{'=' * 20}")
        for insight in analysis.get('key_insights', []):
            print(f"- {insight}")
        
        # Display competitive positioning
        print(f"\nCOMPETITIVE POSITIONING\n{'=' * 20}")
        positioning = analysis.get('competitive_positioning', {})
        print(f"Overview: {positioning.get('overview')}")
        print(f"Market Share: {positioning.get('market_share')}")
        
        print(f"\nStrengths:")
        for strength in positioning.get('strengths', []):
            print(f"- {strength}")
        
        print(f"\nWeaknesses:")
        for weakness in positioning.get('weaknesses', []):
            print(f"- {weakness}")
        
        # Display competitor analysis
        print(f"\nCOMPETITOR ANALYSIS\n{'=' * 20}")
        for competitor in analysis.get('competitor_analysis', []):
            print(f"\n{competitor.get('name')} (Threat: {competitor.get('threat_level')})")
            print(f"Strengths: {', '.join(competitor.get('strengths', []))}")
            print(f"Weaknesses: {', '.join(competitor.get('weaknesses', []))}")
        
        # Display market analysis
        print(f"\nMARKET ANALYSIS\n{'=' * 20}")
        market = analysis.get('market_analysis', {})
        print(f"Market Size: {market.get('market_size')}")
        print(f"Growth Rate: {market.get('growth_rate')}")
        
        print(f"\nTrends:")
        for trend in market.get('trends', []):
            print(f"- {trend}")
        
        print(f"\nOpportunities:")
        for opportunity in market.get('opportunities', []):
            print(f"- {opportunity}")
            
        # Display AI-generated insights
        print(f"\nAI-GENERATED INSIGHTS\n{'=' * 20}")
        ai_insights = analysis.get('ai_generated_insights', {})
        print(f"Confidence Score: {ai_insights.get('confidence_score')}")
        
        print(f"\nKey Insights:")
        for insight in ai_insights.get('key_insights', []):
            print(f"- {insight}")
        
        print(f"\nReasoning Chain:")
        for step in ai_insights.get('reasoning_chain', []):
            print(f"- {step}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
