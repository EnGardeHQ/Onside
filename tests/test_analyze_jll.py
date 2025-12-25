"""
Integration test for the complete JLL analysis workflow.

This test validates the entire workflow from:
1. Campaign creation
2. Competitor identification
3. Web scraping
4. Report generation
5. PDF export
"""
import pytest
import asyncio
import os
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

# Import script to test
from analyze_jll import generate_jll_report

@pytest.mark.asyncio
@patch('analyze_jll.PDFExportService')
@patch('analyze_jll.ReportGeneratorService')
@patch('analyze_jll.CampaignService')
@patch('analyze_jll.WebScraperService')
@patch('analyze_jll.LinkSearchService')
@patch('analyze_jll.EngagementExtractionService')
@patch('analyze_jll.create_db_session')
async def test_generate_jll_report_workflow(
    mock_create_db_session,
    mock_engagement_extraction,
    mock_link_search,
    mock_web_scraper,
    mock_campaign_service,
    mock_report_generator,
    mock_pdf_export
):
    """Test the complete JLL analysis workflow with mocked services."""
    # Setup mock DB
    mock_db = AsyncMock()
    mock_create_db_session.return_value = mock_db
    
    # Mock campaign creation
    mock_campaign_instance = mock_campaign_service.return_value
    mock_campaign_instance.create_campaign.return_value = {
        "success": True,
        "campaign": {
            "id": 1,
            "name": "JLL Competitive Analysis",
            "primary_company_id": 1,
            "description": "Analysis of JLL's competitive positioning in the real estate services market"
        }
    }
    
    # Mock competitor identification
    mock_campaign_instance.identify_competitors.return_value = [
        {"id": 2, "name": "CBRE", "relevance_score": 0.91},
        {"id": 3, "name": "Cushman & Wakefield", "relevance_score": 0.85},
        {"id": 4, "name": "Colliers", "relevance_score": 0.78}
    ]
    
    # Mock web scraping
    mock_web_scraper_instance = mock_web_scraper.return_value
    mock_link_search_instance = mock_link_search.return_value
    mock_engagement_instance = mock_engagement_extraction.return_value
    
    # Mock scrape_company_data and scrape_competitors_data functions
    with patch('analyze_jll.scrape_company_data') as mock_scrape_company:
        with patch('analyze_jll.scrape_competitors_data') as mock_scrape_competitors:
            # Configure mocks
            mock_scrape_company.return_value = {
                "success": True,
                "links_scraped": 5,
                "data": {
                    "content": "JLL company data",
                    "engagement_metrics": {"avg_score": 0.82}
                }
            }
            
            mock_scrape_competitors.return_value = {
                "successful_scrapes": 3,
                "data": {
                    "competitors": [
                        {"id": 2, "name": "CBRE", "data": "CBRE data"},
                        {"id": 3, "name": "Cushman & Wakefield", "data": "C&W data"},
                        {"id": 4, "name": "Colliers", "data": "Colliers data"}
                    ]
                }
            }
            
            # Mock report generation
            mock_report_generator_instance = mock_report_generator.return_value
            mock_report_generator_instance._generate_competitor_report.return_value = {
                "metadata": {
                    "confidence_score": 0.92,
                    "processing_time": {"total": 5.2, "analysis": 3.1, "data_processing": 2.1},
                    "model": "gpt-4",
                    "data_coverage": {"quality_score": 0.88},
                    "chain_of_thought": "Thought process for analysis..."
                },
                "analysis": {
                    "summary": "JLL is a leading real estate services company...",
                    "competitive_positioning": "JLL maintains a strong position...",
                    "strengths": ["Global presence", "Diversified services"],
                    "weaknesses": ["Digital transformation challenges"],
                    "opportunities": ["Proptech integration", "ESG consulting"],
                    "threats": ["Economic uncertainty", "New market entrants"],
                    "trends": ["Digital transformation", "Sustainability focus"],
                    "recommendations": [
                        {"action": "Accelerate digital transformation", "priority": 1, "impact": "High", "confidence": 0.95},
                        {"action": "Expand ESG services", "priority": 2, "impact": "Medium", "confidence": 0.88}
                    ]
                }
            }
            
            # Mock PDF export
            mock_pdf_export_instance = mock_pdf_export.return_value
            mock_pdf_export_instance.export_report.return_value = "/Users/tobymorning/OnSide/exports/jll_analysis_test.pdf"
            
            # Execute
            result = await generate_jll_report()
            
            # Assert
            assert result.endswith(".pdf")
            assert mock_campaign_instance.create_campaign.called
            assert mock_campaign_instance.identify_competitors.called
            assert mock_scrape_company.called
            assert mock_scrape_competitors.called
            assert mock_report_generator_instance._generate_competitor_report.called
            assert mock_pdf_export_instance.export_report.called

if __name__ == "__main__":
    # This allows running the test directly
    asyncio.run(pytest.main(["-xvs", __file__]))
