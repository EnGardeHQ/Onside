"""
PDF Export Service for OnSide Reports.

This module provides functionality for converting report data into
professionally formatted PDF documents with charts and insights.
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import asyncio
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

# Import visualization utilities
from src.services.pdf_visualization import create_swot_table, create_market_position_chart

logger = logging.getLogger(__name__)

class PDFExportService:
    """Service for exporting reports to PDF format with professional styling."""
    
    def __init__(self, export_dir: str = "exports"):
        """Initialize the PDF export service.
        
        Args:
            export_dir: Directory to store exported PDFs
        """
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        
        # Add custom styles
        self.styles.add(ParagraphStyle(
            name='Insight',
            parent=self.styles['Normal'],
            spaceAfter=10,
            bulletIndent=20,
            leftIndent=35
        ))
        
        self.styles.add(ParagraphStyle(
            name='Recommendation',
            parent=self.styles['Normal'],
            spaceAfter=15,
            bulletIndent=20,
            leftIndent=35,
            fontName='Helvetica-Bold',
        ))
        
        self.styles.add(ParagraphStyle(
            name='ExecutiveSummary',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=12,
            borderWidth=1,
            borderColor=colors.lightgrey,
            borderPadding=10,
            borderRadius=5,
            backColor=colors.whitesmoke,
        ))
        
        self.styles.add(ParagraphStyle(
            name='SWOTItem',
            parent=self.styles['Normal'],
            spaceAfter=6,
            bulletIndent=15,
            leftIndent=25,
            textColor=colors.blue
        ))
    
    async def export_report(
        self,
        report_data: Dict[str, Any],
        report_type: str,
        filename: Optional[str] = None
    ) -> str:
        """Export report data to a PDF file.
        
        Args:
            report_data: Report data to export
            report_type: Type of report (competitor, market, audience)
            filename: Optional filename, defaults to auto-generated name
            
        Returns:
            Path to the generated PDF file
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{report_type}_report_{timestamp}.pdf"
            
            filepath = self.export_dir / filename
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build content based on report type
            story = await self._build_report_content(report_data, report_type)
            
            # Generate PDF
            doc.build(story)
            
            logger.info(f"Successfully exported {report_type} report to {filepath}")
            return str(filepath)
            
        except Exception as e:
            error_msg = f"Error exporting {report_type} report to PDF: {str(e)}"
            logger.exception(error_msg)
            raise RuntimeError(error_msg)
    
    async def _build_report_content(
        self,
        report_data: Dict[str, Any],
        report_type: str
    ) -> List[Any]:
        """Build PDF content based on report type and data.
        
        Args:
            report_data: Report data to format
            report_type: Type of report
            
        Returns:
            List of PDF elements
        """
        story = []
        
        # Add header
        title = f"{report_type.title()} Analysis Report"
        story.append(Paragraph(title, self.styles["Heading1"]))
        story.append(Spacer(1, 12))
        
        # Add metadata
        metadata = report_data["metadata"]
        story.extend([
            Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles["Normal"]),
            Paragraph(f"Confidence Score: {metadata['confidence_score']:.2f}", self.styles["Normal"]),
            Paragraph(f"Model: {metadata['model']}", self.styles["Normal"]),
            Spacer(1, 12)
        ])
        
        # Add chain of thought reasoning if available
        if "chain_of_thought" in metadata:
            story.append(Paragraph("Analysis Process:", self.styles["Heading2"]))
            
            # Handle chain_of_thought properly whether it's a string or list
            chain_content = metadata["chain_of_thought"]
            if isinstance(chain_content, list):
                # Handle list of strings
                for step in chain_content:
                    story.append(Paragraph(str(step), self.styles["Normal"]))
            else:
                # Handle string
                story.append(Paragraph(str(chain_content), self.styles["Normal"]))
                
            story.append(Spacer(1, 12))
        
        # Add report-specific content
        if report_type == "competitor":
            story.extend(await self._format_competitor_content(report_data))
        elif report_type == "market":
            story.extend(await self._format_market_content(report_data))
        elif report_type == "audience":
            story.extend(await self._format_audience_content(report_data))
        
        return story
    
    async def _format_competitor_content(self, data: Dict[str, Any]) -> List[Any]:
        """Format competitor analysis content for PDF with enhanced styling.
        
        Following the Semantic Seed coding standards, this method creates a professionally
        formatted PDF with proper visualization, structured insights, and SWOT analysis.
        
        Args:
            data: Report data to format
            
        Returns:
            List of PDF elements
        """
        story = []
        analysis = data["analysis"]
        metadata = data["metadata"]
        
        # Add executive summary
        if analysis.get("summary"):
            story.extend([
                Paragraph("Executive Summary", self.styles["Heading2"]),
                Paragraph(analysis["summary"], self.styles["ExecutiveSummary"]),
                Spacer(1, 15)
            ])
        
        # Add company profile with logo if available
        company_name = analysis.get("company_name", "JLL")
        story.extend([
            Paragraph(f"{company_name} Company Profile", self.styles["Heading2"]),
        ])
        
        # Add company description
        if analysis.get("company_description"):
            story.append(Paragraph(analysis["company_description"], self.styles["Normal"]))
        story.append(Spacer(1, 15))
        
        # Create market positioning visualization
        try:
            if analysis.get("market_position") or analysis.get("market_share"):
                story.append(Paragraph("Market Position", self.styles["Heading2"]))
                positioning_img = await create_market_position_chart(analysis)
                if positioning_img:
                    story.append(positioning_img)
                    story.append(Spacer(1, 10))
        except Exception as e:
            logger.error(f"Error creating market position chart: {str(e)}")
        
        # Add competitive positioning analysis
        story.extend([
            Paragraph("Competitive Positioning Analysis", self.styles["Heading2"]),
            Paragraph(str(analysis["competitive_positioning"]), self.styles["Normal"]),
            Spacer(1, 15)
        ])
        
        # Add SWOT analysis as a table
        story.append(Paragraph("SWOT Analysis", self.styles["Heading2"]))
        swot_table = await create_swot_table(analysis, self.styles)
        story.append(swot_table)
        story.append(Spacer(1, 15))
        
        # Add trends with enhanced styling
        if analysis.get("trends"):
            story.extend([
                Paragraph("Market Trends", self.styles["Heading2"]),
                *[Paragraph(f"• {trend}", self.styles["Insight"]) 
                  for trend in analysis["trends"]],
                Spacer(1, 15)
            ])
        
        # Add opportunities and threats with improved formatting
        for section in ["opportunities", "threats"]:
            if analysis.get(section):
                story.extend([
                    Paragraph(section.title(), self.styles["Heading2"]),
                    *[Paragraph(f"• {item}", self.styles["Insight"]) 
                      for item in analysis[section]],
                    Spacer(1, 15)
                ])
        
        # Add recommendations with priority indicators
        if analysis.get("recommendations"):
            story.append(Paragraph("Strategic Recommendations", self.styles["Heading2"]))
            
            # Sort recommendations by priority if available
            recommendations = analysis["recommendations"]
            if isinstance(recommendations[0], dict) and "priority" in recommendations[0]:
                recommendations = sorted(recommendations, key=lambda x: x.get("priority", 3))
                
                for rec in recommendations:
                    priority = rec.get("priority", 3)
                    action = rec.get("action", rec.get("text", ""))
                    impact = rec.get("impact", "")
                    
                    priority_label = "⭐⭐⭐ HIGH" if priority == 1 else "⭐⭐ MEDIUM" if priority == 2 else "⭐ LOW"
                    rec_text = f"<b>{priority_label}:</b> {action}"
                    if impact:
                        rec_text += f"<br/><i>Impact: {impact}</i>"
                    
                    story.append(Paragraph(f"• {rec_text}", self.styles["Recommendation"]))
            else:
                # Handle simple string recommendations
                story.extend([
                    *[Paragraph(f"• {rec}", self.styles["Recommendation"]) 
                      for rec in recommendations],
                ])
            
            story.append(Spacer(1, 15))
        
        return story
    
    async def _format_market_content(self, data: Dict[str, Any]) -> List[Any]:
        """Format market analysis content for PDF."""
        story = []
        analysis = data["analysis"]
        
        # Add market predictions
        if analysis.get("market_predictions"):
            story.extend([
                Paragraph("Market Predictions", self.styles["Heading2"]),
                *[Paragraph(f"• {pred}", self.styles["Insight"]) 
                  for pred in analysis["market_predictions"]],
                Spacer(1, 12)
            ])
        
        # Add sector trends
        if analysis.get("sector_trends"):
            story.extend([
                Paragraph("Sector Trends", self.styles["Heading2"]),
                *[Paragraph(f"• {trend}", self.styles["Insight"]) 
                  for trend in analysis["sector_trends"]],
                Spacer(1, 12)
            ])
        
        # Add recommendations
        if analysis.get("recommendations"):
            story.extend([
                Paragraph("Strategic Recommendations", self.styles["Heading2"]),
                *[Paragraph(f"• {rec}", self.styles["Recommendation"]) 
                  for rec in analysis["recommendations"]],
                Spacer(1, 12)
            ])
        
        return story
    
    async def _format_audience_content(self, data: Dict[str, Any]) -> List[Any]:
        """Format audience analysis content for PDF."""
        story = []
        analysis = data["analysis"]
        
        # Add engagement patterns
        if analysis.get("engagement_patterns"):
            story.extend([
                Paragraph("Engagement Patterns", self.styles["Heading2"]),
                *[Paragraph(f"• {pattern}", self.styles["Insight"]) 
                  for pattern in analysis["engagement_patterns"]],
                Spacer(1, 12)
            ])
        
        # Add audience personas
        if analysis.get("audience_personas"):
            story.extend([
                Paragraph("Audience Personas", self.styles["Heading2"]),
                *[Paragraph(f"• {persona}", self.styles["Insight"]) 
                  for persona in analysis["audience_personas"]],
                Spacer(1, 12)
            ])
        
        # Add demographic insights
        if analysis.get("demographic_insights"):
            story.extend([
                Paragraph("Demographic Insights", self.styles["Heading2"]),
                *[Paragraph(f"• {insight}", self.styles["Insight"]) 
                  for insight in analysis["demographic_insights"]],
                Spacer(1, 12)
            ])
        
        # Add recommendations
        if analysis.get("recommendations"):
            story.extend([
                Paragraph("Strategic Recommendations", self.styles["Heading2"]),
                *[Paragraph(f"• {rec}", self.styles["Recommendation"]) 
                  for rec in analysis["recommendations"]],
                Spacer(1, 12)
            ])
        
        return story
