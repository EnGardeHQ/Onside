"""
Demo script for enhanced report generation with PDF export.

This script demonstrates the Sprint 4 AI/ML capabilities including:
- Chain-of-thought reasoning
- Confidence scoring
- AI-driven insights
- PDF export with professional formatting
"""
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

from src.services.pdf_export import PDFExportService

# Sample report data following our Sprint 4 AI/ML structure
SAMPLE_COMPETITOR_REPORT = {
    "analysis": {
        "metrics": {
            "engagement": {
                "score": 0.85,
                "trends": ["Consistent growth in user engagement", "High comment-to-view ratio"],
                "confidence": 0.92
            },
            "growth": {
                "score": 0.78,
                "trends": ["20% MoM user acquisition", "Expanding market presence"],
                "confidence": 0.88
            }
        },
        "trends": [
            "Increasing focus on AI-driven features",
            "Expansion into enterprise market",
            "Enhanced data analytics capabilities"
        ],
        "opportunities": [
            {
                "insight": "Market gap in mid-tier enterprise solutions",
                "confidence": 0.89,
                "supporting_data": "Based on market survey and competitor pricing analysis"
            },
            {
                "insight": "Potential for AI-powered automation services",
                "confidence": 0.92,
                "supporting_data": "Competitor feature analysis and customer demand signals"
            }
        ],
        "threats": [
            {
                "insight": "New market entrants with ML-first approach",
                "confidence": 0.85,
                "impact": "High"
            }
        ],
        "competitive_positioning": {
            "strengths": ["Superior AI capabilities", "Strong market presence"],
            "weaknesses": ["Limited enterprise features"],
            "confidence": 0.88
        },
        "recommendations": [
            {
                "action": "Accelerate AI feature development",
                "impact": "High",
                "confidence": 0.94,
                "reasoning": "Based on market trends and competitor positioning"
            },
            {
                "action": "Expand enterprise offering",
                "impact": "High",
                "confidence": 0.91,
                "reasoning": "Address identified market gap and counter competitive threats"
            }
        ]
    },
    "metadata": {
        "model": "gpt-4",
        "provider": "openai",
        "processing_time": 2.45,
        "confidence_score": 0.89,
        "chain_of_thought": """
        1. Analyzed competitor metrics focusing on engagement and growth
        2. Identified key market trends through ML-based pattern recognition
        3. Evaluated competitive positioning using sentiment analysis
        4. Generated strategic recommendations using chain-of-thought reasoning:
           - Market gap analysis suggests opportunity in mid-tier enterprise
           - AI capabilities analysis shows strong competitive advantage
           - Growth trends indicate timing is optimal for expansion
        5. Validated insights through confidence scoring and data quality checks
        """,
        "data_coverage": {
            "time_range": "Last 30 days",
            "data_points": 15000,
            "quality_score": 0.92
        }
    }
}

async def main():
    """Generate and export a sample report with enhanced AI/ML insights."""
    try:
        # Create exports directory
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        
        # Initialize PDF export service
        pdf_service = PDFExportService(export_dir="exports")
        
        print("\n=== Generating Enhanced Competitor Report ===")
        print("Using GPT-4 for AI/ML insights and chain-of-thought reasoning")
        
        # Export report to PDF
        pdf_path = await pdf_service.export_report(
            SAMPLE_COMPETITOR_REPORT,
            "competitor",
            filename="enhanced_competitor_report.pdf"
        )
        
        print("\nReport Generation Summary:")
        print(f"- Confidence Score: {SAMPLE_COMPETITOR_REPORT['metadata']['confidence_score']:.2f}")
        print(f"- Processing Time: {SAMPLE_COMPETITOR_REPORT['metadata']['processing_time']:.2f}s")
        print(f"- Model: {SAMPLE_COMPETITOR_REPORT['metadata']['model']}")
        print(f"- Data Quality: {SAMPLE_COMPETITOR_REPORT['metadata']['data_coverage']['quality_score']:.2f}")
        
        print("\nKey Insights (High Confidence):")
        for rec in SAMPLE_COMPETITOR_REPORT["analysis"]["recommendations"]:
            if rec["confidence"] >= 0.9:
                print(f"- {rec['action']} (Confidence: {rec['confidence']:.2f})")
        
        print(f"\nPDF Report exported to: {pdf_path}")
        print("\nChain of Thought Process:")
        print(SAMPLE_COMPETITOR_REPORT["metadata"]["chain_of_thought"])
        
    except Exception as e:
        print(f"Error generating report: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
