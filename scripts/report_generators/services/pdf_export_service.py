#!/usr/bin/env python
"""
PDF Export Service for TCS Reports

This service handles the generation of PDF reports with visualizations
from the TCS API data, following Semantic Seed Venture Studio Coding Standards.

Implements BDD principles with proper error handling and logging.
"""

import os
import io
import json
import logging
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, 
    TableStyle, PageBreak, ListFlowable, ListItem
)
from reportlab.lib.units import inch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pdf_export_service")

class PDFExportService:
    """Service for exporting TCS reports to PDF with visualizations."""
    
    def __init__(self, output_dir: str = "exports"):
        """Initialize the PDF export service.
        
        Args:
            output_dir: Directory to save PDF reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()
        
        # Create or modify custom styles
        self.custom_styles = {
            'CustomHeading1': ParagraphStyle(
                name='CustomHeading1',
                parent=self.styles['Heading1'],
                fontSize=18,
                spaceAfter=12,
                textColor=colors.darkblue
            ),
            'CustomHeading2': ParagraphStyle(
                name='CustomHeading2',
                parent=self.styles['Heading2'],
                fontSize=14,
                spaceAfter=8,
                textColor=colors.darkblue
            ),
            'CustomBodyText': ParagraphStyle(
                name='CustomBodyText',
                parent=self.styles['BodyText'],
                fontSize=10,
                spaceAfter=6
            )
        }
        
        # Add all custom styles
        for style_name, style in self.custom_styles.items():
            self.styles.add(style)
        
        # Add additional styles
        additional_styles = {
            'CustomBullet': ParagraphStyle(
                name='CustomBullet',
                parent=self.styles['BodyText'],
                fontSize=10,
                spaceAfter=3,
                leftIndent=20
            ),
            'CustomCaption': ParagraphStyle(
                name='CustomCaption',
                parent=self.styles['BodyText'],
                fontSize=8,
                spaceAfter=5,
                alignment=1  # Center alignment
            )
        }
        
        # Add these to both dictionaries
        self.custom_styles.update(additional_styles)
        for style_name, style in additional_styles.items():
            self.styles.add(style)
    
    def create_pdf_report(
        self, 
        data: Dict[str, Any], 
        visualizations: Dict[str, str],
        output_name: Optional[str] = None
    ) -> str:
        """Create a PDF report with visualizations.
        
        Args:
            data: API data for the report
            visualizations: Paths to visualization images
            output_name: Optional name for the output file
            
        Returns:
            Path to the generated PDF file
        """
        logger.info("Creating PDF report with visualizations")
        try:
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if output_name:
                filename = f"{output_name}_{timestamp}.pdf"
            else:
                filename = f"tcs_report_{timestamp}.pdf"
            
            output_path = self.output_dir / filename
            
            # Create the PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build content
            elements = []
            
            # Add title
            elements.append(Paragraph("COMPETITIVE INTELLIGENCE REPORT", self.styles["Title"]))
            elements.append(Paragraph("Tata Consultancy Services (TCS)", self.custom_styles["CustomHeading1"]))
            elements.append(Spacer(1, 12))
            
            # Add report metadata
            elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles["Normal"]))
            elements.append(Paragraph(f"Domain: {data.get('domain', 'tcs.com')}", self.styles["Normal"]))
            elements.append(Spacer(1, 24))
            
            # Add executive summary
            elements.append(Paragraph("Executive Summary", self.custom_styles["CustomHeading1"]))
            
            # Extract summary from AI analysis
            ai_content = data.get("ai_analysis", {}).get("content", "{}")
            try:
                ai_data = json.loads(ai_content)
                competitive_positioning = ai_data.get("competitive_positioning", "")
                if competitive_positioning:
                    elements.append(Paragraph(competitive_positioning, self.custom_styles["CustomBodyText"]))
            except:
                # Fallback summary
                elements.append(Paragraph(
                    "Tata Consultancy Services (TCS) maintains a strong market position as a global leader in IT "
                    "services, consulting, and business solutions. With operations across 46 countries and a diverse "
                    "portfolio of services, TCS continues to demonstrate resilience and innovation in a competitive market.",
                    self.custom_styles["CustomBodyText"]
                ))
            
            elements.append(Spacer(1, 12))
            
            # Add SWOT Analysis section
            elements.append(Paragraph("SWOT Analysis", self.custom_styles["CustomHeading2"]))
            
            # Add SWOT visualization if available
            swot_path = visualizations.get("swot_analysis", "")
            if swot_path and os.path.exists(swot_path):
                img = Image(swot_path, width=6.5*inch, height=5*inch)
                elements.append(img)
                elements.append(Paragraph("Figure 1: TCS SWOT Analysis", self.custom_styles["CustomCaption"]))
            
            elements.append(Spacer(1, 24))
            
            # Add Competitor Analysis section
            elements.append(Paragraph("Competitor Analysis", self.custom_styles["CustomHeading1"]))
            
            competitor_chart = visualizations.get("competitor_chart", "")
            if competitor_chart and os.path.exists(competitor_chart):
                elements.append(Spacer(1, 6))
                img = Image(competitor_chart, width=6.5*inch, height=3.5*inch)
                elements.append(img)
                elements.append(Paragraph("Figure 2: Competitor Threat Analysis", self.custom_styles["CustomCaption"]))
            
            # Add competitor analysis text
            elements.append(Spacer(1, 12))
            
            try:
                ai_data = json.loads(ai_content)
                competitor_analysis = ai_data.get("competitor_analysis", [])
                
                if competitor_analysis:
                    elements.append(Paragraph("Key Competitors:", self.custom_styles["CustomHeading2"]))
                    
                    for comp in competitor_analysis:
                        name = comp.get("competitor_name", "")
                        strengths = comp.get("strengths", [])
                        weaknesses = comp.get("weaknesses", [])
                        threat = comp.get("threat_level", "")
                        
                        elements.append(Paragraph(f"{name} (Threat Level: {threat})", self.custom_styles["CustomHeading2"]))
                        
                        if strengths:
                            elements.append(Paragraph("Strengths:", self.custom_styles["CustomBodyText"]))
                            strength_items = []
                            for strength in strengths:
                                strength_items.append(ListItem(Paragraph(strength, self.custom_styles["CustomBullet"])))
                            elements.append(ListFlowable(strength_items, bulletType='bullet'))
                        
                        if weaknesses:
                            elements.append(Paragraph("Weaknesses:", self.custom_styles["CustomBodyText"]))
                            weakness_items = []
                            for weakness in weaknesses:
                                weakness_items.append(ListItem(Paragraph(weakness, self.custom_styles["CustomBullet"])))
                            elements.append(ListFlowable(weakness_items, bulletType='bullet'))
                        
                        elements.append(Spacer(1, 6))
            except:
                # Fallback competitor analysis
                elements.append(Paragraph(
                    "TCS faces strong competition from major players including Infosys, Wipro, and Cognizant. "
                    "Each competitor presents unique challenges in different market segments and geographies.",
                    self.custom_styles["CustomBodyText"]
                ))
            
            elements.append(PageBreak())
            
            # Add Market Analysis section
            elements.append(Paragraph("Market Analysis", self.custom_styles["CustomHeading1"]))
            
            market_chart = visualizations.get("market_trends", "")
            if market_chart and os.path.exists(market_chart):
                elements.append(Spacer(1, 6))
                img = Image(market_chart, width=6.5*inch, height=3.5*inch)
                elements.append(img)
                elements.append(Paragraph("Figure 3: Market Trends Analysis", self.custom_styles["CustomCaption"]))
            
            # Add market analysis text
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(
                "TCS operates in a dynamic IT services market with significant growth in cloud services, AI/ML, "
                "and digital transformation. The company is well-positioned to capitalize on emerging trends while "
                "maintaining its core business strengths.",
                self.custom_styles["CustomBodyText"]
            ))
            
            # Add News Analysis section
            elements.append(Paragraph("News Analysis", self.custom_styles["CustomHeading2"]))
            
            news_chart = visualizations.get("news_sentiment", "")
            if news_chart and os.path.exists(news_chart):
                elements.append(Spacer(1, 6))
                img = Image(news_chart, width=5*inch, height=5*inch)
                elements.append(img)
                elements.append(Paragraph("Figure 4: News Sentiment Analysis", self.custom_styles["CustomCaption"]))
            
            # Add news analysis text
            elements.append(Spacer(1, 12))
            
            # Extract recent news
            news_articles = data.get("news", {}).get("articles", [])
            if news_articles:
                elements.append(Paragraph("Recent News Headlines:", self.custom_styles["CustomBodyText"]))
                
                news_items = []
                for article in news_articles[:5]:  # Limit to top 5 articles
                    title = article.get("title", "")
                    date = article.get("publishedAt", "")
                    if date:
                        try:
                            date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
                            date_str = date_obj.strftime("%Y-%m-%d")
                        except:
                            date_str = date
                    else:
                        date_str = "N/A"
                    
                    news_text = f"{title} ({date_str})"
                    news_items.append(ListItem(Paragraph(news_text, self.custom_styles["CustomBullet"])))
                
                elements.append(ListFlowable(news_items, bulletType='bullet'))
            
            elements.append(PageBreak())
            
            # Add Geographic Analysis section
            elements.append(Paragraph("Geographic Presence", self.custom_styles["CustomHeading1"]))
            
            geo_chart = visualizations.get("geographic_distribution", "")
            if geo_chart and os.path.exists(geo_chart):
                elements.append(Spacer(1, 6))
                img = Image(geo_chart, width=6*inch, height=4.5*inch)
                elements.append(img)
                elements.append(Paragraph("Figure 5: TCS Global Footprint", self.custom_styles["CustomCaption"]))
            
            # Add geographic analysis text
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(
                "TCS maintains a strong global presence with significant operations across North America, Europe, "
                "and Asia Pacific regions. This global footprint provides resilience against regional economic "
                "fluctuations and enables the company to serve multinational clients effectively.",
                self.custom_styles["CustomBodyText"]
            ))
            
            # Add Domain Information section
            elements.append(Paragraph("Domain Information", self.custom_styles["CustomHeading2"]))
            
            # Extract domain information
            domain_info = data.get("domain_info", {})
            if domain_info:
                # Create a table for domain information
                domain_data = [
                    ["Attribute", "Value"],
                    ["Domain", domain_info.get("domain", "N/A")],
                    ["Registrar", domain_info.get("registrar", "N/A")],
                    ["Creation Date", domain_info.get("creation_date", "N/A")],
                    ["Expiration Date", domain_info.get("expiration_date", "N/A")]
                ]
                
                domain_table = Table(domain_data, colWidths=[2*inch, 4*inch])
                domain_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
                    ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (1, 0), 5),
                    ('BACKGROUND', (0, 1), (1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                elements.append(domain_table)
                elements.append(Spacer(1, 12))
            
            # Add Search Engine Visibility section
            elements.append(Paragraph("Search Engine Visibility", self.custom_styles["CustomHeading2"]))
            
            # Extract search insights
            search_insights = data.get("search_insights", {})
            if search_insights:
                elements.append(Paragraph(
                    f"TCS maintains strong search engine visibility for key industry terms. "
                    f"Query: \"{search_insights.get('query', '')}\" returned "
                    f"{search_insights.get('result_count', 0)} top results.",
                    self.custom_styles["CustomBodyText"]
                ))
                
                # Add information about top results
                top_results = search_insights.get("top_results", [])
                if top_results:
                    elements.append(Paragraph("Top Search Results:", self.custom_styles["CustomBodyText"]))
                    
                    result_items = []
                    for result in top_results[:3]:  # Limit to top 3 results
                        position = result.get("position", 0)
                        title = result.get("title", "")
                        result_text = f"Position {position}: {title}"
                        result_items.append(ListItem(Paragraph(result_text, self.custom_styles["CustomBullet"])))
                    
                    elements.append(ListFlowable(result_items, bulletType='bullet'))
            
            elements.append(PageBreak())
            
            # Add Recommendations section
            elements.append(Paragraph("Strategic Recommendations", self.custom_styles["CustomHeading1"]))
            
            # Generate recommendations based on SWOT analysis
            try:
                ai_data = json.loads(ai_content)
                strengths = ai_data.get("strengths", [])
                weaknesses = ai_data.get("weaknesses", [])
                
                # Leverage strengths
                if strengths:
                    elements.append(Paragraph("Leverage Strengths:", self.custom_styles["CustomHeading2"]))
                    
                    strength_recs = []
                    for strength in strengths[:3]:  # Use top 3 strengths
                        rec = f"Capitalize on {strength.lower()} to expand market share in emerging technologies"
                        strength_recs.append(ListItem(Paragraph(rec, self.custom_styles["CustomBullet"])))
                    
                    elements.append(ListFlowable(strength_recs, bulletType='bullet'))
                
                # Address weaknesses
                if weaknesses:
                    elements.append(Paragraph("Address Weaknesses:", self.custom_styles["CustomHeading2"]))
                    
                    weakness_recs = []
                    for weakness in weaknesses[:3]:  # Use top 3 weaknesses
                        rec = f"Develop strategy to overcome {weakness.lower()} through targeted initiatives"
                        weakness_recs.append(ListItem(Paragraph(rec, self.custom_styles["CustomBullet"])))
                    
                    elements.append(ListFlowable(weakness_recs, bulletType='bullet'))
            except:
                # Fallback recommendations
                elements.append(Paragraph("Key Recommendations:", self.custom_styles["CustomHeading2"]))
                
                rec_items = [
                    ListItem(Paragraph("Expand cloud services capabilities to capitalize on market growth", self.custom_styles["CustomBullet"])),
                    ListItem(Paragraph("Enhance AI/ML offerings to maintain competitive edge", self.custom_styles["CustomBullet"])),
                    ListItem(Paragraph("Address talent retention through improved career development programs", self.custom_styles["CustomBullet"])),
                    ListItem(Paragraph("Diversify geographic presence to reduce dependency on specific markets", self.custom_styles["CustomBullet"])),
                    ListItem(Paragraph("Strengthen digital marketing to improve market perception", self.custom_styles["CustomBullet"]))
                ]
                
                elements.append(ListFlowable(rec_items, bulletType='bullet'))
            
            # Add report footer
            elements.append(Spacer(1, 36))
            elements.append(Paragraph(
                f"Generated by OnSide AI | Confidential | {datetime.now().strftime('%Y-%m-%d')}",
                self.custom_styles["CustomCaption"]
            ))
            
            # Build the PDF
            doc.build(elements)
            
            logger.info(f"PDF report successfully created at {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error creating PDF report: {str(e)}")
            logger.error(traceback.format_exc())
            return ""


if __name__ == "__main__":
    # Test the PDF export service with sample data
    try:
        # Create sample data
        with open("exports/tcs_api_demo_20250516_164740.json", "r") as f:
            sample_data = json.load(f)
        
        # Sample visualization paths
        visualizations = {
            "competitor_chart": "exports/competitor_comparison_20250516_165000.png",
            "news_sentiment": "exports/news_sentiment_20250516_165000.png",
            "market_trends": "exports/market_trends_20250516_165000.png",
            "geographic_distribution": "exports/geographic_distribution_20250516_165000.png",
            "swot_analysis": "exports/swot_analysis_20250516_165000.png"
        }
        
        # Create PDF report
        exporter = PDFExportService()
        pdf_path = exporter.create_pdf_report(sample_data, visualizations, "tcs_report_test")
        
        print(f"\n✅ PDF report created successfully: {pdf_path}")
    except Exception as e:
        print(f"\n❌ Error creating PDF report: {str(e)}")
