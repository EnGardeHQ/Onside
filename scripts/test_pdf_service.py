#!/usr/bin/env python
"""
Test script for the Enhanced PDF Service
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import from the module
from report_generators.services.enhanced_pdf_service import OnSidePDFService

def test_pdf_service():
    """Test the PDF service with sample data."""
    try:
        # Sample TCS analysis data
        sample_data = {
            "metadata": {
                "title": "TCS (Tata Consultancy Services) Strategic Analysis",
                "client_name": "Test Client Inc.",
                "prepared_by": "OnSide Analytics Team",
                "date": datetime.now().strftime('%B %d, %Y')
            },
            "executive_summary": {
                "overview": "This report provides a comprehensive analysis of Tata Consultancy Services (TCS), one of the world's leading IT services, consulting, and business solutions organizations. TCS has demonstrated consistent growth in recent years, with a strong focus on digital transformation services and cloud solutions.",
                "key_insights": [
                    "TCS maintains a strong position in the IT services market with consistent revenue growth",
                    "The company's focus on digital transformation services aligns with market demand",
                    "TCS's Business 4.0 framework has positioned it well for future innovation",
                    "Continued investment in cloud, AI, and cybersecurity capabilities strengthens market position"
                ]
            },
            "competitor_analysis": {
                "overview": "Analysis of TCS's primary competitors in the global IT services market.",
                "competitors": [
                    {
                        "name": "Accenture",
                        "strengths": ["Strong consulting capabilities", "Wide global presence", "Advanced digital offerings"],
                        "weaknesses": ["Higher cost structure", "Less focus on traditional IT services"]
                    },
                    {
                        "name": "Infosys",
                        "strengths": ["Strong digital transformation capabilities", "Competitive pricing", "Growing AI portfolio"],
                        "weaknesses": ["Smaller global footprint than TCS", "Higher attrition rates"]
                    },
                    {
                        "name": "Wipro",
                        "strengths": ["Strong engineering services", "Growing cloud practice"],
                        "weaknesses": ["Slower growth compared to peers", "Less diversified client base"]
                    },
                    {
                        "name": "IBM",
                        "strengths": ["Strong legacy and brand recognition", "Advanced AI with Watson", "Strong enterprise relationships"],
                        "weaknesses": ["Higher cost structure", "Complex organizational structure"]
                    }
                ],
                "market_share": {
                    "chart_data": {
                        "labels": ["TCS", "Accenture", "Infosys", "Wipro", "IBM", "Others"],
                        "values": [20, 22, 12, 8, 15, 23]
                    }
                }
            },
            "market_analysis": {
                "overview": "Analysis of the global IT services market in which TCS operates, with focus on key trends affecting the company's growth strategy.",
                "market_size": 1250000000000,  # $1.25 trillion global IT services market
                "growth_rate": 0.065,  # 6.5% annual growth
                "trends": [
                    "Accelerated digital transformation post-pandemic",
                    "Growing demand for cloud migration and modernization",
                    "Increasing importance of AI and automation solutions",
                    "Rising cybersecurity concerns and spending",
                    "Shift toward experience-led transformation",
                    "Increasing demand for sustainability solutions"
                ],
                "segments": [
                    {"name": "Banking and Financial Services", "size": 325000000000, "growth": 0.07},
                    {"name": "Healthcare and Life Sciences", "size": 175000000000, "growth": 0.085},
                    {"name": "Retail and Consumer Goods", "size": 150000000000, "growth": 0.065},
                    {"name": "Communications and Media", "size": 125000000000, "growth": 0.06},
                    {"name": "Manufacturing", "size": 225000000000, "growth": 0.055},
                    {"name": "Other Industries", "size": 250000000000, "growth": 0.05}
                ],
                "key_insights": [
                    "TCS has a particularly strong position in Banking and Financial Services",
                    "Healthcare represents the fastest growing segment at 8.5% annually",
                    "Cloud transformation services represent about 30% of overall IT spending",
                    "TCS's investments in AI and automation align with current market demand"
                ]
            },
            "swot_analysis": {
                "overview": "SWOT analysis of TCS's current market position and future prospects.",
                "strengths": [
                    "Strong global brand recognition and reputation",
                    "Industry-leading profit margins (25%+)",
                    "Comprehensive service portfolio across industries",
                    "Low attrition rate compared to industry peers",
                    "Strong financial position with minimal debt",
                    "Proven delivery model with location-independent agile methods",
                    "Large and diverse client base with strong relationships"
                ],
                "weaknesses": [
                    "Higher dependence on traditional IT services compared to some competitors",
                    "Lower revenue per employee than global competitors like Accenture",
                    "Geographic concentration with high dependency on US and UK markets",
                    "Less specialized in high-end consulting compared to MBB firms",
                    "Brand perception as more of a service provider than innovation partner"
                ],
                "opportunities": [
                    "Expansion of cloud migration and modernization services",
                    "Growth in AI, machine learning, and data analytics capabilities",
                    "Increased demand for cybersecurity solutions",
                    "Geographic expansion in Europe and Asia-Pacific regions",
                    "Sustainability and ESG-focused services",
                    "Growth in healthcare and life sciences verticals"
                ],
                "threats": [
                    "Intensifying competition from both global and local players",
                    "Potential visa restrictions in key markets like the US",
                    "Margin pressure due to wage inflation and pricing competition",
                    "Rapid technology changes requiring continuous upskilling",
                    "Potential economic slowdown affecting IT spending",
                    "Geopolitical tensions affecting global delivery model"
                ]
            },
            "strategic_recommendations": [
                {
                    "priority": "High", 
                    "action": "Accelerate AI and Automation Capabilities",
                    "description": "Enhance TCS's AI, ML, and automation offerings through internal development and strategic acquisitions to capture growing demand for intelligent automation.",
                    "expected_impact": "High - Potential to increase AI-driven revenue by 25%",
                    "timeline": "6-12 months"
                },
                {
                    "priority": "High", 
                    "action": "Expand Cloud Transformation Services",
                    "description": "Strengthen partnerships with major cloud providers (AWS, Azure, GCP) and develop industry-specific cloud migration frameworks to capitalize on growing cloud adoption.",
                    "expected_impact": "High - Could drive 20% growth in cloud services revenue",
                    "timeline": "3-9 months"
                },
                {
                    "priority": "Medium", 
                    "action": "Strengthen Consulting Capabilities",
                    "description": "Enhance high-value strategic consulting services by recruiting industry experts and developing specialized industry knowledge to shift brand perception toward that of a strategic advisor.",
                    "expected_impact": "Medium - Potential 15% increase in consulting revenue",
                    "timeline": "12-18 months"
                },
                {
                    "priority": "Medium", 
                    "action": "Develop Sustainability Service Offerings",
                    "description": "Create a dedicated sustainability practice offering ESG reporting, carbon footprint analysis, and green IT solutions to meet growing demand for sustainability services.",
                    "expected_impact": "Medium - New revenue stream with high growth potential",
                    "timeline": "9-15 months"
                },
                {
                    "priority": "Medium", 
                    "action": "Geographic Expansion in Europe",
                    "description": "Increase investment in European markets, particularly Germany, France, and the Nordics, through local talent acquisition and delivery centers.",
                    "expected_impact": "Medium - Potential 18% growth in European revenue",
                    "timeline": "12-24 months"
                }
            ],
            "appendices": {
                "methodology": "This TCS analysis was prepared using a combination of primary and secondary research methods, including financial statement analysis, expert interviews, industry reports, and competitive benchmarking. Our team employed both quantitative analysis of market and financial data and qualitative assessment of strategic positioning.",
                "data_sources": [
                    "TCS Annual Reports and Financial Statements (2020-2025)",
                    "Competitor Annual Reports and Investor Presentations",
                    "Gartner IT Services Market Reports",
                    "IDC Industry Analysis",
                    "Forrester Wave Reports for IT Services",
                    "Expert interviews with industry analysts",
                    "Client satisfaction surveys and testimonials"
                ],
                "definitions": {
                    "BFSI": "Banking, Financial Services, and Insurance",
                    "CAGR": "Compound Annual Growth Rate",
                    "ACV": "Annual Contract Value",
                    "TCV": "Total Contract Value",
                    "ADM": "Application Development and Maintenance",
                    "BPS": "Business Process Services",
                    "GCC": "Global Capability Centers",
                    "ODC": "Offshore Development Center",
                    "SaaS": "Software as a Service",
                    "IaaS": "Infrastructure as a Service",
                    "PaaS": "Platform as a Service"
                }
            }
        }
        
        # For this test, we'll just test the OnSide PDF service directly
        # Use an absolute path for the output directory
        output_dir = Path("/Volumes/Cody/projects/OnSide/exports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_service = OnSidePDFService(str(output_dir))
        pdf_path = pdf_service.create_onside_report(sample_data, "tcs_analysis_report")
        
        # Print the full path where the PDF was saved
        full_path = Path(pdf_path).resolve()
        print(f"\n✅ OnSide PDF report created at: {full_path}")
        print(f"   File exists: {full_path.exists()}")
        
        # List the contents of the output directory
        print("\nContents of output directory:")
        for f in output_dir.glob("*"):
            print(f"  - {f.name} (size: {f.stat().st_size} bytes)")
        return pdf_path
        
    except Exception as e:
        print(f"\n❌ Error testing PDF service: {str(e)}")

if __name__ == "__main__":
    test_pdf_service()
