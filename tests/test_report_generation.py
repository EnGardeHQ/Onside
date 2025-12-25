"""
Test suite for enhanced report generation with PDF export.

This module tests the integration of our Sprint 4 AI/ML capabilities
and PDF export functionality.
"""
import os
import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from src.services.report_generator import ReportGeneratorService
from src.services.pdf_export import PDFExportService
from src.models.report import Report, ReportType
from src.models.competitor_metrics import CompetitorMetrics
from src.models.ai_insight import AIInsight

@pytest.fixture
async def report_generator():
    """Fixture for report generator service."""
    service = ReportGeneratorService()
    return service

@pytest.fixture
async def pdf_export():
    """Fixture for PDF export service."""
    export_dir = Path("test_exports")
    service = PDFExportService(export_dir=str(export_dir))
    yield service
    # Cleanup test exports after tests
    if export_dir.exists():
        for file in export_dir.glob("*.pdf"):
            file.unlink()
        export_dir.rmdir()

@pytest.mark.asyncio
async def test_competitor_report_generation(report_generator, pdf_export):
    """Test competitor report generation with PDF export."""
    # Setup test data
    report = Report(
        type=ReportType.COMPETITOR,
        parameters={
            "competitor_ids": [1, 2],
            "metrics": ["engagement", "growth", "sentiment"],
            "timeframe": {
                "start": datetime.now() - timedelta(days=30),
                "end": datetime.now()
            },
            "with_chain_of_thought": True
        }
    )
    
    # Generate report
    result = await report_generator._generate_competitor_report(report)
    
    # Validate report structure
    assert "analysis" in result
    assert "metadata" in result
    assert result["metadata"]["model"] == "gpt-4"
    assert result["metadata"]["provider"] == "openai"
    assert isinstance(result["metadata"]["confidence_score"], float)
    assert result["metadata"]["confidence_score"] >= 0.0
    assert result["metadata"]["confidence_score"] <= 1.0
    
    # Validate analysis components
    analysis = result["analysis"]
    assert "metrics" in analysis
    assert "trends" in analysis
    assert "opportunities" in analysis
    assert "threats" in analysis
    assert "competitive_positioning" in analysis
    assert "recommendations" in analysis
    
    # Validate recommendations confidence threshold
    for rec in analysis["recommendations"]:
        assert rec["confidence"] >= 0.7
    
    # Export to PDF
    pdf_path = await pdf_export.export_report(result, "competitor")
    assert os.path.exists(pdf_path)
    assert pdf_path.endswith(".pdf")

@pytest.mark.asyncio
async def test_market_report_generation(report_generator, pdf_export):
    """Test market report generation with PDF export."""
    # Setup test data
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
    
    # Generate report
    result = await report_generator._generate_market_report(report)
    
    # Validate report structure
    assert "analysis" in result
    assert "metadata" in result
    assert result["metadata"]["model"] == "gpt-4"
    assert isinstance(result["metadata"]["confidence_score"], float)
    
    # Validate analysis components
    analysis = result["analysis"]
    assert "market_predictions" in analysis
    assert "sector_trends" in analysis
    assert "recommendations" in analysis
    
    # Export to PDF
    pdf_path = await pdf_export.export_report(result, "market")
    assert os.path.exists(pdf_path)

@pytest.mark.asyncio
async def test_audience_report_generation(report_generator, pdf_export):
    """Test audience report generation with PDF export."""
    # Setup test data
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
    
    # Generate report
    result = await report_generator._generate_audience_report(report)
    
    # Validate report structure
    assert "analysis" in result
    assert "metadata" in result
    assert result["metadata"]["model"] == "gpt-4"
    assert isinstance(result["metadata"]["confidence_score"], float)
    
    # Validate analysis components
    analysis = result["analysis"]
    assert "engagement_patterns" in analysis
    assert "audience_personas" in analysis
    assert "demographic_insights" in analysis
    assert "behavioral_insights" in analysis
    assert "recommendations" in analysis
    
    # Export to PDF
    pdf_path = await pdf_export.export_report(result, "audience")
    assert os.path.exists(pdf_path)

@pytest.mark.asyncio
async def test_pdf_export_error_handling(pdf_export):
    """Test PDF export error handling."""
    with pytest.raises(RuntimeError):
        await pdf_export.export_report({}, "invalid_type")

@pytest.mark.asyncio
async def test_report_confidence_scoring():
    """Test confidence scoring across different report types."""
    report_generator = ReportGeneratorService()
    
    # Test competitor report confidence
    competitor_report = Report(
        type=ReportType.COMPETITOR,
        parameters={
            "competitor_ids": [1],
            "metrics": ["engagement"],
            "timeframe": {
                "start": datetime.now() - timedelta(days=30),
                "end": datetime.now()
            },
            "with_chain_of_thought": True
        }
    )
    
    result = await report_generator._generate_competitor_report(competitor_report)
    assert 0.0 <= result["metadata"]["confidence_score"] <= 1.0
    
    # Validate confidence components
    assert all(0.0 <= v <= 1.0 for v in competitor_report.confidence_metrics.values())
    
    # Test that high-confidence recommendations are included
    recommendations = result["analysis"]["recommendations"]
    assert all(rec["confidence"] >= 0.7 for rec in recommendations)
