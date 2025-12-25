#!/usr/bin/env python
"""
KPMG Standard PDF Report Service

Creates professional KPMG-standard PDF reports with:
- Executive summaries
- Market and competitor analysis
- SWOT analysis
- Strategic recommendations
- Professional visualizations
- Confidence metrics and reasoning chains

Following Semantic Seed Venture Studio Coding Standards V2.0.
"""

import os
import logging
import json
from typing import Dict, Any, List, Tuple, Optional, Union
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4, letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    Image, PageBreak, NextPageTemplate, 
    Frame, FrameBreak, KeepTogether, PageTemplate, 
    HRFlowable, Flowable, ListFlowable, ListItem
)
from reportlab.lib.units import inch, cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, Line, LineShape, String, Group, Polygon, PolyLine
from reportlab.graphics.charts.barcharts import VerticalBarChart, HorizontalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.textlabels import Label
from reportlab.graphics import renderPDF
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.colors import HexColor, Color, PCMYKColor, PCMYKColorSep, black, white, lightgrey, grey, darkgrey
from reportlab.pdfgen import canvas
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image as PILImage
import io

class HRFlow(Flowable):
    """Horizontal line flowable --- draws a line in a flowable."""

    def __init__(self, width="100%", thickness=1, color=colors.black, 
                 lineCap='round', spaceBefore=0, spaceAfter=0, **kw):
        Flowable.__init__(self, **kw)
        self.width = width
        self.thickness = thickness
        self.color = color
        self.lineCap = lineCap
        self.spaceBefore = spaceBefore
        self.spaceAfter = spaceAfter
        self.hAlign = 'CENTER'  # Default alignment

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        if isinstance(self.width, str) and self.width.endswith('%'):
            self.width = availWidth * float(self.width.strip('%')) / 100.0
        self.height = self.thickness + self.spaceBefore + self.spaceAfter
        return (self.width, self.height)

    def draw(self):
        self.canv.saveState()
        self.canv.setLineWidth(self.thickness)
        self.canv.setStrokeColor(self.color)
        self.canv.setLineCap(1 if self.lineCap == 'round' else 0)
        
        # Calculate y position to account for space before
        y = self.height - self.spaceAfter - (self.thickness / 2.0)
        
        # Draw the line
        self.canv.line(0, y, self.width, y)
        self.canv.restoreState()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("enhanced_pdf_service")

class OnSidePDFService:
    """Service for creating KPMG-standard PDF reports with professional visualizations."""
    
    # OnSide Brand Colors
    ONSIDE_BLUE = HexColor('#00338D')  # Primary blue
    ONSIDE_LIGHT_BLUE = HexColor('#006AB3')
    ONSIDE_GREEN = HexColor('#009A44')
    ONSIDE_RED = HexColor('#E31837')
    ONSIDE_YELLOW = HexColor('#FFCD00')
    ONSIDE_WHITE = colors.white
    ONSIDE_BLACK = colors.black
    ONSIDE_GRAY = HexColor('#666666')
    ONSIDE_LIGHT_GRAY = HexColor('#F2F2F2')
    
    def __init__(self, output_dir: str = "exports"):
        """Initialize the KPMG PDF service.
        
        Args:
            output_dir: Directory to save generated PDFs
        """
        self.output_dir = Path(output_dir) / "onside_reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        
        # Register fonts
        self._register_fonts()
        
        # Define custom styles
        self._define_styles()
        
        # Initialize visualization tools
        self._init_visualization_tools()
    
    def _register_fonts(self):
        """Register custom fonts for the report."""
        try:
            # Register Arial fonts (fallback to default if not found)
            fonts_dir = Path(__file__).parent.parent.parent / 'assets' / 'fonts'
            
            # Try to register Arial fonts if they exist
            arial_path = fonts_dir / 'Arial.ttf'
            if arial_path.exists():
                pdfmetrics.registerFont(TTFont('Arial', str(arial_path)))
                
            arial_bold_path = fonts_dir / 'Arial_Bold.ttf'
            if arial_bold_path.exists():
                pdfmetrics.registerFont(TTFont('Arial-Bold', str(arial_bold_path)))
                
            arial_italic_path = fonts_dir / 'Arial_Italic.ttf'
            if arial_italic_path.exists():
                pdfmetrics.registerFont(TTFont('Arial-Italic', str(arial_italic_path)))
                
            arial_bold_italic_path = fonts_dir / 'Arial_Bold_Italic.ttf'
            if arial_bold_italic_path.exists():
                pdfmetrics.registerFont(TTFont('Arial-BoldItalic', str(arial_bold_italic_path)))
                
        except Exception as e:
            logger.warning(f"Could not register custom fonts: {e}")
    
    def _define_styles(self):
        """Define custom styles for the OnSide report."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='OnSide-Title',
            parent=self.styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=18,
            textColor=self.ONSIDE_BLUE,
            spaceAfter=12,
            alignment=TA_LEFT
        ))
        
        # Heading 1
        self.styles.add(ParagraphStyle(
            name='OnSide-Heading1',
            parent=self.styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=self.ONSIDE_BLUE,
            spaceAfter=10,
            alignment=TA_LEFT
        ))
        
        # Heading 2
        self.styles.add(ParagraphStyle(
            name='OnSide-Heading2',
            parent=self.styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=self.ONSIDE_BLUE,
            spaceAfter=8,
            alignment=TA_LEFT
        ))
        
        # Normal text
        self.styles.add(ParagraphStyle(
            name='OnSide-BodyText',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=self.ONSIDE_BLACK,
            spaceBefore=4,
            spaceAfter=4,
            leading=14
        ))
        
        # Caption style
        self.styles.add(ParagraphStyle(
            name='OnSide-Caption',
            parent=self.styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            textColor=self.ONSIDE_GRAY,
            alignment=TA_CENTER
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='OnSide-Footer',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            textColor=self.ONSIDE_GRAY,
            alignment=TA_CENTER
        ))
        
        # Table header style
        self.styles.add(ParagraphStyle(
            name='OnSide-TableHeader',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=self.ONSIDE_WHITE,
            alignment=TA_CENTER,
            backColor=self.ONSIDE_BLUE
        ))
        
        # Table cell style
        self.styles.add(ParagraphStyle(
            name='OnSide-TableCell',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=self.ONSIDE_BLACK,
            alignment=TA_LEFT
        ))
    
    def _init_visualization_tools(self):
        """Initialize tools needed for visualizations."""
        # Create temporary directory for storing visualization assets
        self.temp_dir = self.output_dir / "temp"
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        
        # Set matplotlib style
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
        plt.rcParams['axes.edgecolor'] = '#CCCCCC'
        plt.rcParams['axes.linewidth'] = 0.8
        plt.rcParams['xtick.color'] = '#555555'
        plt.rcParams['ytick.color'] = '#555555'
        plt.rcParams['text.color'] = '#333333'
        plt.rcParams['axes.titlesize'] = 11
        plt.rcParams['axes.labelsize'] = 10
        plt.rcParams['xtick.labelsize'] = 8
        plt.rcParams['ytick.labelsize'] = 8
        plt.rcParams['legend.fontsize'] = 8
        plt.rcParams['figure.titlesize'] = 12
        
        # OnSide color palette
        self.color_palette = [
            self.ONSIDE_BLUE,
            self.ONSIDE_LIGHT_BLUE,
            self.ONSIDE_GREEN,
            self.ONSIDE_RED,
            self.ONSIDE_YELLOW,
            self.ONSIDE_GRAY,
            '#7F7F7F',  # Medium gray
            '#BFBFBF'   # Light gray
        ]
        
        # Register color names for ReportLab
        # Directly use HexColor objects which are already compatible with ReportLab
        # We'll store them in a dictionary for easy access
        self.color_map = {
            'onside_blue': self.ONSIDE_BLUE,
            'onside_light_blue': self.ONSIDE_LIGHT_BLUE,
            'onside_green': self.ONSIDE_GREEN,
            'onside_red': self.ONSIDE_RED,
        }
    def create_onside_report(self, report_data: Dict[str, Any], filename: str = None) -> str:
        """
        Create an OnSide-standard PDF report with the provided data.
        
        Args:
            report_data: Dictionary containing all report data including:
                - executive_summary
                - competitor_analysis
                - market_analysis
                - swot_analysis
                - strategic_recommendations
                - visualization_data
                - metadata
            filename: Output filename (without extension)
            
        Returns:
            Path to the generated PDF file
        """
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"onside_report_{timestamp}"
        
        # Convert filename to Path object if it's a string
        if isinstance(filename, str):
            # If filename includes directory, split it
            filename = Path(filename)
            
            # If filename has a parent, ensure it exists
            if filename.parent != Path('.'):
                filename.parent.mkdir(parents=True, exist_ok=True)
                output_path = filename.with_suffix('.pdf')
            else:
                output_path = self.output_dir / f"{filename}.pdf"
        else:
            # It's already a Path object
            output_path = filename.with_suffix('.pdf')
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create the PDF document with page templates
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Store the document reference for later use
        self.doc = doc
        
        # Define page templates
        self._define_page_templates(doc)
        
        # Build the document story
        story = self._build_story(report_data)
        
        # Generate the PDF
        doc.build(
            story,
            onFirstPage=self._header_footer,
            onLaterPages=self._header_footer
        )
        
        logger.info(f"OnSide report generated: {output_path}")
        return str(output_path)
    
    def _define_page_templates(self, doc):
        """Define page templates for the document."""
        # Main template with header and footer
        frame = Frame(
            doc.leftMargin, doc.bottomMargin, 
            doc.width, doc.height - 2 * cm,  # Leave space for header/footer
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0
        )
        
        # Add the template to the document
        doc.addPageTemplates([
            PageTemplate(id='FirstPage', frames=frame, onPage=self._header_footer),
            PageTemplate(id='OtherPages', frames=frame, onPage=self._header_footer)
        ])
    
    def _header_footer(self, canvas, doc):
        """Add header and footer to each page."""
        # Save the current state of the canvas
        canvas.saveState()
        
        # Draw header
        header_height = 1.5 * cm
        canvas.setFillColor(self.ONSIDE_BLUE)
        canvas.rect(0, doc.pagesize[1] - header_height, 
                   doc.pagesize[0], header_height, fill=1, stroke=0)
        
        # Add OnSide logo (placeholder)
        logo_text = "OnSide"
        canvas.setFont('Helvetica-Bold', 14)
        canvas.setFillColor(self.ONSIDE_WHITE)
        canvas.drawRightString(doc.pagesize[0] - 2*cm, doc.pagesize[1] - 1*cm, logo_text)
        
        # Add report title if first page
        if canvas.getPageNumber() == 1 and hasattr(doc, 'title'):
            canvas.setFont('Helvetica-Bold', 16)
            canvas.drawCentredString(doc.pagesize[0] / 2, doc.pagesize[1] - 1*cm, doc.title)
        
        # Add page number
        page_num = canvas.getPageNumber()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(self.ONSIDE_GRAY)
        canvas.drawCentredString(
            doc.pagesize[0] / 2,
            1 * cm,
            f"Page {page_num}"
        )
        
        # Restore the canvas state
        canvas.restoreState()
    
    def _build_story(self, report_data: Dict[str, Any]) -> List[Any]:
        """Build the document story from report data with improved section handling.
        
        Args:
            report_data: Dictionary containing all report data
            
        Returns:
            List of flowables for the document
        """
        story = []
        
        try:
            # Set document title for header
            if hasattr(self, 'doc'):
                self.doc.title = report_data.get('metadata', {}).get('title', 'OnSide Report')
            
            # Add title page
            title_page = self._create_title_page(report_data)
            if title_page:
                story.extend(title_page)
            
            # Add table of contents
            toc = self._create_toc(report_data)
            if toc:
                story.extend(toc)
            
            # Add a page break after TOC
            story.append(PageBreak())
            
            # Add executive summary with improved formatting
            if 'executive_summary' in report_data:
                summary = self._create_section(
                    "Executive Summary", 
                    report_data['executive_summary'],
                    is_first_section=True
                )
                if summary:
                    story.extend(summary)
            
            # Add competitor analysis with visual separation
            if 'competitor_analysis' in report_data:
                story.append(PageBreak())
                comp_analysis = self._create_competitor_analysis(
                    report_data['competitor_analysis']
                )
                if comp_analysis:
                    story.extend(comp_analysis)
            
            # Add market analysis with visual separation
            if 'market_analysis' in report_data:
                story.append(PageBreak())
                market_analysis = self._create_market_analysis(
                    report_data['market_analysis']
                )
                if market_analysis:
                    story.extend(market_analysis)
            
            # Add SWOT analysis with visual separation
            if 'swot_analysis' in report_data:
                story.append(PageBreak())
                swot = self._create_swot_analysis(
                    report_data['swot_analysis']
                )
                if swot:
                    story.extend(swot)
            
            # Add strategic recommendations with visual separation
            if 'strategic_recommendations' in report_data:
                story.append(PageBreak())
                recommendations = self._create_strategic_recommendations(
                    report_data['strategic_recommendations']
                )
                if recommendations:
                    story.extend(recommendations)
            
            # Add appendices with visual separation
            if 'appendices' in report_data:
                story.append(PageBreak())
                appendices = self._create_appendices(
                    report_data['appendices']
                )
                if appendices:
                    story.extend(appendices)
            
            # Add a final page with report metadata
            metadata = self._create_report_metadata(report_data)
            if metadata:
                story.extend(metadata)
                
            # Add debug information
            print(f"\n📄 Generated story with {len(story)} flowables")
            for i, flowable in enumerate(story[:5]):  # Print first 5 flowables for debugging
                print(f"  {i+1}. {type(flowable).__name__}")
            if len(story) > 5:
                print(f"  ... and {len(story) - 5} more flowables")
                
        except Exception as e:
            print(f"\n❌ Error in _build_story: {str(e)}")
            import traceback
            print(traceback.format_exc())
            
            # Add error message to the PDF
            story.append(Paragraph("An error occurred while generating the report.", 
                                self.styles['Title']))
            story.append(Paragraph(str(e), self.styles['Normal']))
        
        return story
    
    def _create_title_page(self, report_data: Dict[str, Any]) -> List[Any]:
        """Create the title page of the report."""
        elements = []
        
        # Add OnSide logo (placeholder)
        logo = f"<para align=center><font name='Helvetica-Bold' size=24 color=#00338D>OnSide</font></para>"
        elements.append(Paragraph(logo, self.styles['Normal']))
        elements.append(Spacer(1, 2*cm))
        
        # Add report title
        title = report_data.get('metadata', {}).get('title', 'Strategic Analysis Report')
        elements.append(Paragraph(f"<para align=center><font size=20><b>{title}</b></font></para>", 
                                self.styles['Normal']))
        elements.append(Spacer(1, 1*cm))
        
        # Add client name if available
        if 'client_name' in report_data.get('metadata', {}):
            client = report_data['metadata']['client_name']
            elements.append(Paragraph(f"<para align=center><i>Prepared for: {client}</i></para>", 
                                    self.styles['Normal']))
        
        elements.append(Spacer(1, 3*cm))
        
        # Add prepared by and date
        prepared_by = report_data.get('metadata', {}).get('prepared_by', 'OnSide Analytics Team')
        date = report_data.get('metadata', {}).get('date', datetime.now().strftime('%B %d, %Y'))
        
        elements.append(Paragraph(f"<para align=center>Prepared by: {prepared_by}</para>", 
                                self.styles['Normal']))
        elements.append(Paragraph(f"<para align=center>{date}</para>", 
                                self.styles['Normal']))
        elements.append(PageBreak())
        
        return elements
    
    def _create_toc(self, report_data: Dict[str, Any]) -> List[Any]:
        """Create the table of contents."""
        elements = []
        
        # Add TOC title
        elements.append(Paragraph("Table of Contents", self.styles['OnSide-Heading1']))
        elements.append(Spacer(1, 0.5*cm))
        
        # TOC entries - only include sections that exist in the report
        toc_entries = []
        page_num = 2  # Start after title page and TOC
        
        # Add sections that exist in the report data
        sections = [
            ('executive_summary', 'Executive Summary'),
            ('competitor_analysis', 'Competitor Analysis'),
            ('market_analysis', 'Market Analysis'),
            ('swot_analysis', 'SWOT Analysis'),
            ('strategic_recommendations', 'Strategic Recommendations'),
            ('appendices', 'Appendices')
        ]
        
        # Add sections that exist in the report data
        for section_key, section_title in sections:
            if section_key in report_data:
                toc_entries.append((str(len(toc_entries) + 1), section_title, page_num))
                page_num += 1
        
        # Create TOC entries with dots
        for num, title, page in toc_entries:
            # Create a table with two columns: title and page number
            toc_line = Table([
                [
                    Paragraph(f"<para><b>{num}. {title}</b></para>", self.styles['OnSide-BodyText']),
                    Paragraph(f"<para align=right><b>{page}</b></para>", self.styles['OnSide-BodyText'])
                ]
            ], colWidths=[self.doc.width * 0.8, self.doc.width * 0.2])
            
            # Add dotted line
            toc_line.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (0, 0), 0),
                ('RIGHTPADDING', (1, 0), (1, 0), 0),
                ('LINEBELOW', (0, 0), (0, 0), 0.5, colors.grey, None, (2, 2, 0)),
            ]))
            
            elements.append(toc_line)
            elements.append(Spacer(1, 0.2*cm))
        
        return elements

    def _create_section(self, title: str, content: Any, is_first_section: bool = False) -> List[Any]:
        """Create a standard report section with improved formatting.
            
        Args:
            title: Section title
            content: Section content (can be string, list, or dict)
            is_first_section: Whether this is the first section after TOC
            
        Returns:
            List of flowables for the section
        """
        elements = []
        
        # Add section title
        elements.append(Paragraph(
            title,
            self.styles['OnSide-Heading1' if is_first_section else 'OnSide-Heading2']
        ))
        
        # Add a horizontal line under the section title
        elements.append(HRFlow(
            width="100%",
            thickness=1,
            lineCap='round',
            color=self.ONSIDE_LIGHT_BLUE,
            spaceBefore=6,
            spaceAfter=12
        ))
        
        # Add content based on type
        if isinstance(content, str):
            # Handle string content
            elements.append(Paragraph(content, self.styles['OnSide-BodyText']))
            elements.append(Spacer(1, 0.3*cm))
        elif isinstance(content, list):
            # Handle list content
            for item in content:
                if isinstance(item, str):
                    elements.append(Paragraph(f"• {item}", self.styles['OnSide-BodyText']))
                    elements.append(Spacer(1, 0.2*cm))
                elif isinstance(item, dict):
                    # Handle dictionary items
                    if 'heading' in item:
                        elements.append(Paragraph(
                            f"<b>{item['heading']}</b>", 
                            self.styles['OnSide-BodyText']
                        ))
                    if 'text' in item:
                        elements.append(Paragraph(item['text'], self.styles['OnSide-BodyText']))
                    if 'points' in item:
                        for point in item['points']:
                            elements.append(Paragraph(f"• {point}", self.styles['OnSide-BodyText']))
                    elements.append(Spacer(1, 0.2*cm))
        elif isinstance(content, dict):
            # Handle dictionary content
            if 'overview' in content:
                elements.append(Paragraph("<b>Overview</b>", self.styles['OnSide-BodyText']))
                elements.append(Paragraph(content['overview'], self.styles['OnSide-BodyText']))
                elements.append(Spacer(1, 0.3*cm))
            
            # Handle key insights
            if 'key_insights' in content and content['key_insights']:
                elements.append(Paragraph("<b>Key Insights</b>", self.styles['OnSide-BodyText']))
                for insight in content['key_insights']:
                    elements.append(Paragraph(f"• {insight}", self.styles['OnSide-BodyText']))
                elements.append(Spacer(1, 0.3*cm))
            
            # Handle other content fields
            for key, value in content.items():
                if key not in ['overview', 'key_insights'] and value:
                    if isinstance(value, (list, tuple)):
                        elements.append(Paragraph(f"<b>{key.title()}:</b>", self.styles['OnSide-BodyText']))
                        for item in value:
                            if isinstance(item, dict):
                                # Handle nested structures
                                for k, v in item.items():
                                    elements.append(Paragraph(f"<i>{k}:</i> {v}", self.styles['OnSide-BodyText']))
                            else:
                                elements.append(Paragraph(f"• {item}", self.styles['OnSide-BodyText']))
                        elements.append(Spacer(1, 0.2*cm))
                    elif isinstance(value, dict):
                        elements.append(Paragraph(f"<b>{key.title()}:</b>", self.styles['OnSide-BodyText']))
                        for k, v in value.items():
                            elements.append(Paragraph(f"<i>{k}:</i> {v}", self.styles['OnSide-BodyText']))
                        elements.append(Spacer(1, 0.2*cm))
                    elif key not in ['page_break_after']:
                        elements.append(Paragraph(f"<b>{key.title()}:</b> {value}", self.styles['OnSide-BodyText']))
        
        # Add page break if specified
        if isinstance(content, dict) and content.get('page_break_after', False):
            elements.append(PageBreak())
        
        return elements

    def _create_competitor_analysis(self, analysis_data: Dict[str, Any]) -> List[Any]:
        """Create the competitor analysis section with improved formatting."""
        elements = []
        
        # Add section title with bookmark
        elements.append(Paragraph(
            "Competitor Analysis",
            self.styles['OnSide-Heading1']
        ))
        
        # Add a horizontal line under the section title
        elements.append(HRFlow(
            width="100%",
            thickness=1,
            lineCap='round',
            color=self.ONSIDE_LIGHT_BLUE,
            spaceBefore=6,
            spaceAfter=12
        ))
        
        # Add overview if available
        if 'overview' in analysis_data:
            elements.append(Paragraph(
                analysis_data['overview'],
                self.styles['OnSide-BodyText']
            ))
            elements.append(Spacer(1, 0.5*cm))
        elements.append(Spacer(1, 0.5*cm))
        
        # Add overview
        if 'overview' in analysis_data:
            elements.append(Paragraph(
                analysis_data['overview'],
                self.styles['OnSide-BodyText']
            ))
            elements.append(Spacer(1, 0.5*cm))
        
        # Add market share analysis if available
        if 'market_share' in analysis_data:
            elements.append(Paragraph(
                "<b>Market Share Analysis</b>",
                self.styles['OnSide-Heading2']
            ))
            elements.append(Spacer(1, 0.3*cm))
            
            # Add market share chart
            if 'chart_data' in analysis_data['market_share']:
                chart = self._create_market_share_chart(
                    analysis_data['market_share']['chart_data']
                )
                elements.append(chart)
                elements.append(Spacer(1, 0.5*cm))
            
            # Add market share table
            if 'table_data' in analysis_data['market_share']:
                table = self._create_table(
                    analysis_data['market_share']['table_data'],
                    ['Competitor', 'Market Share', 'Growth']
                )
                elements.append(table)
                elements.append(Spacer(1, 0.5*cm))
        
        elements.append(PageBreak())
        return elements
    
    def _create_market_analysis(self, analysis_data: Dict[str, Any]) -> List[Any]:
        """Create the market analysis section with improved formatting."""
        elements = []
        
        # Add section title with bookmark
        elements.append(Paragraph(
            "Market Analysis",
            self.styles['OnSide-Heading1']
        ))
        
        # Add a horizontal line under the section title
        elements.append(HRFlow(
            width="100%",
            thickness=1,
            lineCap='round',
            color=self.ONSIDE_LIGHT_BLUE,
            spaceBefore=6,
            spaceAfter=12
        ))
        
        # Add overview if available
        if 'overview' in analysis_data:
            elements.append(Paragraph(
                analysis_data['overview'],
                self.styles['OnSide-BodyText']
            ))
            elements.append(Spacer(1, 0.5*cm))
        elements.append(Spacer(1, 0.5*cm))
        
        # Add overview
        if 'overview' in analysis_data:
            elements.append(Paragraph(
                analysis_data['overview'],
                self.styles['OnSide-BodyText']
            ))
            elements.append(Spacer(1, 0.5*cm))
        
        # Add market size and growth
        if 'market_size' in analysis_data:
            elements.append(Paragraph(
                "<b>Market Size and Growth</b>",
                self.styles['OnSide-Heading2']
            ))
            elements.append(Spacer(1, 0.3*cm))
            
            market_size = analysis_data['market_size']
            
            # Handle case where market_size is a dictionary with chart/table data
            if isinstance(market_size, dict):
                # Add market size chart if chart data is available
                if 'chart_data' in market_size:
                    chart = self._create_market_size_chart(
                        market_size['chart_data']
                    )
                    elements.append(chart)
                    elements.append(Spacer(1, 0.5*cm))
                
                # Add market size table if table data is available
                if 'table_data' in market_size:
                    table = self._create_table(
                        market_size['table_data'],
                        ['Year', 'Market Size', 'Growth Rate']
                    )
                    elements.append(table)
                    elements.append(Spacer(1, 0.5*cm))
            # Handle case where market_size is just a number
            elif isinstance(market_size, (int, float)):
                elements.append(Paragraph(
                    f"Market Size: ${market_size:,.2f}",
                    self.styles['OnSide-BodyText']
                ))
                elements.append(Spacer(1, 0.3*cm))
        
        elements.append(PageBreak())
        return elements
    
    def _create_swot_analysis(self, analysis_data: Dict[str, Any]) -> List[Any]:
        """Create the SWOT analysis section with improved formatting."""
        elements = []
        
        # Add section title with bookmark
        elements.append(Paragraph(
            "SWOT Analysis",
            self.styles['OnSide-Heading1']
        ))
        
        # Add a horizontal line under the section title
        elements.append(HRFlow(
            width="100%",
            thickness=1,
            lineCap='round',
            color=self.ONSIDE_LIGHT_BLUE,
            spaceBefore=6,
            spaceAfter=12
        ))
        
        # Add overview if available
        if 'overview' in analysis_data:
            elements.append(Paragraph(
                analysis_data['overview'],
                self.styles['OnSide-BodyText']
            ))
            elements.append(Spacer(1, 0.5*cm))
        elements.append(Spacer(1, 0.5*cm))
        
        # Add overview
        if 'overview' in analysis_data:
            elements.append(Paragraph(
                analysis_data['overview'],
                self.styles['OnSide-BodyText']
            ))
            elements.append(Spacer(1, 0.5*cm))
        
        # Create a 2x2 grid for SWOT
        swot_table = self._create_swot_table(analysis_data)
        elements.append(swot_table)
        elements.append(Spacer(1, 0.5*cm))
        
        elements.append(PageBreak())
        return elements
    
    def _create_strategic_recommendations(self, recommendations_data: Dict[str, Any]) -> List[Any]:
        """Create the strategic recommendations section."""
        elements = []
        
        # Add section title with bookmark
        elements.append(Paragraph(
            "Strategic Recommendations",
            self.styles['OnSide-Heading1']
        ))
        elements.append(Spacer(1, 0.5*cm))
        
        # Add introductory text
        elements.append(Paragraph(
            "Based on our analysis, we recommend the following strategic actions:",
            self.styles['OnSide-BodyText']
        ))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Spacer(1, 0.5*cm))
        
        # Add recommendations with error handling
        if not recommendations_data:
            elements.append(Paragraph(
                "No specific recommendations could be generated at this time.",
                self.styles['OnSide-BodyText']
            ))
            return elements
            
        if 'recommendations' in recommendations_data and recommendations_data['recommendations']:
            for i, rec in enumerate(recommendations_data['recommendations'], 1):
                try:
                    # Safely get title with fallback
                    title = rec.get('title', f'Recommendation {i}')
                    elements.append(Paragraph(
                        f"<b>{i}. {title}</b>",
                        self.styles['OnSide-Heading2']
                    ))
                    elements.append(Spacer(1, 0.2*cm))
                    
                    # Safely get description with fallback
                    description = rec.get('description', 'No detailed description available.')
                    elements.append(Paragraph(
                        description,
                        self.styles['OnSide-BodyText']
                    ))
                    elements.append(Spacer(1, 0.3*cm))
                except Exception as e:
                    logger.error(f"Error processing recommendation {i}: {str(e)}")
                    continue
        
        elements.append(PageBreak())
        return elements
    
    def _create_appendices(self, appendices_data: Dict[str, Any]) -> List[Any]:
        """Create the appendices section."""
        elements = []
        
        # Add section title with bookmark
        elements.append(Paragraph(
            "Appendices",
            self.styles['OnSide-Heading1']
        ))
        elements.append(Spacer(1, 0.5*cm))
        
        # Add introductory text
        elements.append(Paragraph(
            "This section contains supplementary information referenced in the main report.",
            self.styles['OnSide-BodyText']
        ))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Spacer(1, 0.5*cm))
        
        # Add data sources
        if 'data_sources' in appendices_data:
            elements.append(Paragraph(
                "<b>Data Sources</b>",
                self.styles['OnSide-Heading2']
            ))
            elements.append(Spacer(1, 0.3*cm))
            
            for i, source in enumerate(appendices_data['data_sources'], 1):
                elements.append(Paragraph(
                    f"{i}. {source}",
                    self.styles['OnSide-BodyText']
                ))
            
            elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    # Helper methods for creating visualizations
    def _create_market_share_chart(self, chart_data: Dict[str, Any]) -> Any:
        """Create a market share chart."""
        try:
            # Create a figure with white background
            fig, ax = plt.subplots(figsize=(8, 5))
            
            # Extract data
            labels = chart_data.get('labels', [])
            values = chart_data.get('values', [])
            # Use hex colors directly to avoid any color format issues
            colors = ['#00338D', '#006AB3', '#009A44', '#E31837', '#FFCD00']
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(
                values, 
                labels=labels,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors[:len(labels)],
                wedgeprops=dict(width=0.6, edgecolor='w'),
                textprops=dict(color="w")
            )
            
            # Style the chart
            plt.setp(autotexts, size=8, weight="bold")
            plt.title("Market Share Distribution", fontsize=12, pad=20)
            
            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            
            # Create ReportLab image
            buf.seek(0)
            img = Image(buf, width=15*cm, height=10*cm)
            return img
            
        except Exception as e:
            logger.error(f"Error creating market share chart: {e}")
            return Paragraph("Error generating market share chart.", self.styles['OnSide-BodyText'])
    
    def _create_table(self, data: List[List[Any]], headers: List[str]) -> Table:
        """Create a styled table from data and headers."""
        # Add headers to data
        table_data = [headers] + data
        
        # Create table
        table = Table(table_data, colWidths=[self.doc.width / len(headers)] * len(headers))
        
        # Style table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.ONSIDE_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.ONSIDE_WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), self.ONSIDE_LIGHT_GRAY),
            ('GRID', (0, 0), (-1, -1), 0.5, self.ONSIDE_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        return table
    
    def _create_swot_table(self, analysis_data: Dict[str, Any]) -> Table:
        """Create a 2x2 SWOT analysis table."""
        swot_data = [
            ["Strengths", "Weaknesses"],
            ["Opportunities", "Threats"]
        ]
        
        # Fill in the SWOT data
        for i, category in enumerate(['strengths', 'weaknesses', 'opportunities', 'threats']):
            row = i // 2
            col = i % 2
            content = "\n".join([f"• {item}" for item in analysis_data.get(category, [])])
            swot_data[row][col] = [
                Paragraph(f"<b>{category.capitalize()}</b>", self.styles['OnSide-BodyText']),
                Paragraph(content, self.styles['OnSide-BodyText'])
            ]
        
        # Create the table
        table = Table(swot_data, colWidths=[self.doc.width/2] * 2)
        
        # Style the table
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, self.ONSIDE_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        return table
    
    def _create_market_size_chart(self, chart_data: Dict[str, Any]) -> Any:
        """Create a market size line chart."""
        try:
            # Create a figure with white background
            fig, ax1 = plt.subplots(figsize=(10, 6))
            
            # Extract data
            years = chart_data.get('years', [])
            sizes = chart_data.get('sizes', [])
            growth_rates = chart_data.get('growth_rates', [])
            
            # Create line plot for market size
            ax1.plot(years, sizes, 'o-', color=self.ONSIDE_BLUE, linewidth=2, markersize=8)
            ax1.set_ylabel('Market Size ($B)', color=self.ONSIDE_BLUE)
            ax1.tick_params(axis='y', labelcolor=self.ONSIDE_BLUE)
            
            # Create second y-axis for growth rates
            ax2 = ax1.twinx()
            ax2.bar(years, [float(g.rstrip('%')) if g != '-' else 0 for g in growth_rates], 
                   color=self.ONSIDE_LIGHT_BLUE, alpha=0.3, width=0.4)
            ax2.set_ylabel('Growth Rate (%)', color=self.ONSIDE_LIGHT_BLUE)
            ax2.tick_params(axis='y', labelcolor=self.ONSIDE_LIGHT_BLUE)
            
            # Style the chart
            plt.title('Market Size and Growth Rate', fontsize=12, pad=20)
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            
            # Create ReportLab image
            buf.seek(0)
            img = Image(buf, width=18*cm, height=10*cm)
            return img
            
        except Exception as e:
            logger.error(f"Error creating market size chart: {e}")
            return Paragraph("Error generating market size chart.", self.styles['OnSide-BodyText'])
            
    def _create_kpmg_heading3(self):
        """Create OnSide Heading3 style."""
        self.styles.add(ParagraphStyle(
            name='OnSide-Heading3',
            parent=self.styles['Heading3'],
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=self.ONSIDE_BLUE,
            spaceAfter=6,
            alignment=TA_LEFT
        ))
        
        # Also add TCSHeading3 style
        self.styles.add(ParagraphStyle(
            name='TCSHeading3',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.darkblue
        ))
        
        return {
            'OnSide-Heading3': self.styles['OnSide-Heading3'],
            'TCSHeading3': self.styles['TCSHeading3']
        }
        
        # Define OnSide styles
        self.styles.add(ParagraphStyle(
            name='OnSide-Heading1',
            parent=self.styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=self.ONSIDE_BLUE,
            spaceAfter=10,
            alignment=TA_LEFT
        ))
        
        self.styles.add(ParagraphStyle(
            name='OnSide-Heading2',
            parent=self.styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=self.ONSIDE_BLUE,
            spaceAfter=8,
            alignment=TA_LEFT
        ))
        
        self.styles.add(ParagraphStyle(
            name='OnSide-BodyText',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=self.ONSIDE_BLACK,
            spaceBefore=4,
            spaceAfter=4,
            leading=14
        ))
        
        # Add TCS styles for backward compatibility
        self.styles.add(ParagraphStyle(
            name='TCSBodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12,
            spaceAfter=6
        ))
        self.styles.add(ParagraphStyle(
            name='TCSNotes',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.gray,
            spaceAfter=4
        ))
        self.styles.add(ParagraphStyle(
            name='TCSCaption',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=12,
            alignment=1,  # Center alignment
            textColor=colors.darkgrey
        ))
        self.styles.add(ParagraphStyle(
            name='TCSConfidence',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.green,
            spaceAfter=4
        ))
        self.styles.add(ParagraphStyle(
            name='TCSBullet',
            parent=self.styles['Normal'],
            fontSize=10,
            leftIndent=20,
            firstLineIndent=-15,
            bulletIndent=0,
            spaceAfter=3
        ))
        self.styles.add(ParagraphStyle(
            name='TCSReasoningHeader',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.darkblue,
            spaceAfter=6,
            spaceBefore=8
        ))
        self.styles.add(ParagraphStyle(
            name='TCSReasoningText',
            parent=self.styles['Normal'],
            fontSize=9,
            leftIndent=20,
            textColor=colors.darkslategray,
            spaceAfter=6
        ))
        
        # Add TCS styles for backward compatibility
        self.styles.add(ParagraphStyle(
            name='TCSCaption',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=12,
            alignment=1,  # Center alignment
            textColor=colors.darkgrey
        ))
        
        self.styles.add(ParagraphStyle(
            name='TCSConfidence',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.green,
            spaceAfter=4
        ))
        
        self.styles.add(ParagraphStyle(
            name='TCSBullet',
            parent=self.styles['Normal'],
            fontSize=10,
            leftIndent=20,
            firstLineIndent=-15,
            bulletIndent=0,
            spaceAfter=3
        ))
        
        self.styles.add(ParagraphStyle(
            name='TCSReasoningHeader',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.darkblue,
            spaceAfter=6,
            spaceBefore=8
        ))
        
        self.styles.add(ParagraphStyle(
            name='TCSReasoningText',
            parent=self.styles['Normal'],
            fontSize=9,
            leftIndent=20,
            textColor=colors.darkslategray,
            spaceAfter=6
        ))
        
        # Add custom styles to the stylesheet
        for name, style in self.custom_styles.items():
            if name not in self.styles:
                self.styles.add(style)
    
    def create_pdf_report(
        self, 
        data: Dict[str, Any],
        integrated_data: Dict[str, Any], 
        visualizations: Dict[str, str]
    ) -> str:
        """Create an enhanced PDF report with reasoning chains."""
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tcs_enhanced_report_{timestamp}.pdf"
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
        
        # Build content elements
        elements = []
        
        # Add cover page
        self._add_cover_page(elements, data)
        
        # Add executive dashboard
        self._add_executive_dashboard(elements, integrated_data, visualizations)
        
        # Add competitor analysis with reasoning
        self._add_competitor_analysis(elements, integrated_data, visualizations)
        
        # And other sections...
        
        # Build the PDF
        doc.build(elements)
        
        return str(output_path)
    
    def _add_cover_page(self, elements, data):
        """Add the cover page."""
        # Implementation details...
        pass
    
    def _add_executive_dashboard(self, elements, integrated_data, visualizations):
        """Add the executive dashboard."""
        # Implementation details...
        pass
    
    def _add_competitor_analysis(self, elements, integrated_data, visualizations):
        """Add competitor analysis with reasoning chains."""
        elements.append(Paragraph("Competitor Analysis", self.custom_styles["TCSHeading1"]))
        elements.append(Spacer(1, 0.1*inch))
        
        # Add competitor matrix visualization if available
        competitor_matrix = visualizations.get("competitor_matrix", "")
        if competitor_matrix and os.path.exists(competitor_matrix):
            img = Image(competitor_matrix, width=6.5*inch, height=4.5*inch)
            elements.append(img)
            elements.append(Paragraph("Competitive Positioning Matrix with Threat Analysis", self.custom_styles["TCSCaption"]))
            elements.append(Spacer(1, 0.2*inch))
        
        # Add competitor analysis text
        competitor_analysis = integrated_data.get("integrated_analysis", {}).get("competitor_analysis", {})
        competitors = competitor_analysis.get("competitors", [])
        
        if competitors:
            for comp in competitors:
                name = comp.get("name", "")
                if name == "TCS":
                    continue  # Skip TCS itself
                    
                threat_level = comp.get("threat_level", "Medium")
                strengths = comp.get("strengths", [])
                weaknesses = comp.get("weaknesses", [])
                news_mentions = comp.get("news_mentions", [])
                threat_justification = comp.get("threat_justification", "")
                
                # Style threat level by color
                threat_color = colors.green
                if threat_level == "High":
                    threat_color = colors.red
                elif threat_level == "Medium":
                    threat_color = colors.orange
                
                # Create competitor heading with threat level
                competitor_style = ParagraphStyle(
                    name=f"CompetitorHeading{name}",
                    parent=self.custom_styles["TCSHeading2"],
                    textColor=threat_color
                )
                elements.append(Paragraph(f"{name} (Threat Level: {threat_level})", competitor_style))
                
                # Add strengths and weaknesses
                if strengths:
                    elements.append(Paragraph("Strengths:", self.custom_styles["TCSBodyText"]))
                    strength_items = []
                    for strength in strengths:
                        strength_items.append(ListItem(Paragraph(strength, self.custom_styles["TCSBullet"])))
                    elements.append(ListFlowable(strength_items, bulletType='bullet'))
                
                if weaknesses:
                    elements.append(Paragraph("Weaknesses:", self.custom_styles["TCSBodyText"]))
                    weakness_items = []
                    for weakness in weaknesses:
                        weakness_items.append(ListItem(Paragraph(weakness, self.custom_styles["TCSBullet"])))
                    elements.append(ListFlowable(weakness_items, bulletType='bullet'))
                
                # Add comparison metrics if available
                metrics = comp.get("comparison_metrics", {})
                if metrics:
                    data_rows = [
                        ["Metric", "Value", "vs TCS"]
                    ]
                    
                    for metric, value in metrics.items():
                        # Format metric name
                        metric_name = metric.replace("_", " ").title()
                        # Format comparison
                        comparison = "Lower"
                        if value >= 1.0:
                            comparison = "Higher"
                        data_rows.append([metric_name, f"{value:.2f}", comparison])
                    
                    # Create metrics table
                    metrics_table = Table(data_rows, colWidths=[2*inch, 1*inch, 1*inch])
                    metrics_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (2, 0), colors.lightblue),
                        ('TEXTCOLOR', (0, 0), (2, 0), colors.black),
                        ('ALIGN', (0, 0), (2, 0), 'CENTER'),
                        ('FONTNAME', (0, 0), (2, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (2, 0), 9),
                        ('BOTTOMPADDING', (0, 0), (2, 0), 5),
                        ('BACKGROUND', (0, 1), (2, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ALIGN', (1, 1), (2, -1), 'CENTER'),
                    ]))
                    elements.append(metrics_table)
                
                # Add reasoning
                if threat_justification:
                    elements.append(Paragraph("Threat Analysis:", self.custom_styles["TCSReasoningHeader"]))
                    elements.append(Paragraph(threat_justification, self.custom_styles["TCSReasoningText"]))
                
                # Add recent news mentions if available
                if news_mentions:
                    elements.append(Paragraph("Recent News:", self.custom_styles["TCSReasoningHeader"]))
                    news_items = []
                    for news in news_mentions[:3]:  # Limit to 3 most recent
                        news_items.append(ListItem(Paragraph(
                            f"{news.get('title', '')} ({news.get('date', 'N/A')})", 
                            self.custom_styles["TCSBullet"]
                        )))
                    if news_items:
                        elements.append(ListFlowable(news_items, bulletType='bullet'))
                
                elements.append(Spacer(1, 0.2*inch))
        
        # Add reasoning chain section if available
        ai_analysis = integrated_data.get("ai_analysis", {})
        reasoning_chains = ai_analysis.get("reasoning_chains", {})
        competitor_reasoning = reasoning_chains.get("competitor_research", "")
        
        if competitor_reasoning:
            elements.append(Paragraph("Analysis Reasoning Process:", self.custom_styles["TCSReasoningHeader"]))
            elements.append(Paragraph(competitor_reasoning, self.custom_styles["TCSReasoningText"]))
            elements.append(Spacer(1, 0.1*inch))
            
            # Add confidence indicator
            overall_confidence = ai_analysis.get("overall_confidence", 0.8)
            conf_color = self._get_confidence_color(overall_confidence)
            conf_style = ParagraphStyle(
                name='ConfidenceStyle',
                parent=self.custom_styles["TCSConfidence"],
                textColor=conf_color
            )
            elements.append(Paragraph(f"Analysis Confidence: {overall_confidence:.2f}", conf_style))
        
        elements.append(PageBreak())
        
    def _add_market_analysis(self, elements, integrated_data, visualizations):
        """Add market analysis section with visualizations."""
        elements.append(Paragraph("Market Analysis", self.custom_styles["TCSHeading1"]))
        elements.append(Spacer(1, 0.1*inch))
        
        # Add SWOT visualization if available
        swot_vis = visualizations.get("enhanced_swot", "")
        if swot_vis and os.path.exists(swot_vis):
            img = Image(swot_vis, width=6.5*inch, height=4.5*inch)
            elements.append(img)
            elements.append(Paragraph("SWOT Analysis with Confidence Scoring", self.custom_styles["TCSCaption"]))
            elements.append(Spacer(1, 0.2*inch))
        
        # Add market trends information
        market_trends = integrated_data.get("integrated_analysis", {}).get("market_trends", {})
        
        # Add market share and industry rank
        market_share = market_trends.get("market_share", "")
        industry_rank = market_trends.get("industry_rank", "")
        
        if market_share or industry_rank:
            elements.append(Paragraph("Market Position", self.custom_styles["TCSHeading2"]))
            
            if market_share:
                elements.append(Paragraph(f"Market Share: {market_share}", self.custom_styles["TCSBodyText"]))
            
            if industry_rank:
                elements.append(Paragraph(f"Industry Rank: {industry_rank}", self.custom_styles["TCSBodyText"]))
            
            elements.append(Spacer(1, 0.1*inch))
        
        # Add trending topics
        trending_topics = market_trends.get("trending_topics", [])
        if trending_topics:
            elements.append(Paragraph("Trending Industry Topics", self.custom_styles["TCSHeading2"]))
            topic_items = []
            for topic in trending_topics:
                topic_items.append(ListItem(Paragraph(topic, self.custom_styles["TCSBullet"])))
            elements.append(ListFlowable(topic_items, bulletType='bullet'))
            elements.append(Spacer(1, 0.1*inch))
        
        # Add search trends
        search_trends = market_trends.get("search_trends", [])
        if search_trends:
            elements.append(Paragraph("Popular Search Terms", self.custom_styles["TCSHeading2"]))
            trend_items = []
            for trend in search_trends:
                trend_items.append(ListItem(Paragraph(trend, self.custom_styles["TCSBullet"])))
            elements.append(ListFlowable(trend_items, bulletType='bullet'))
        
        # Add reasoning chain if available
        ai_analysis = integrated_data.get("ai_analysis", {})
        reasoning_chains = ai_analysis.get("reasoning_chains", {})
        market_reasoning = reasoning_chains.get("market_position_analysis", "")
        
        if market_reasoning:
            elements.append(Paragraph("Market Analysis Reasoning:", self.custom_styles["TCSReasoningHeader"]))
            elements.append(Paragraph(market_reasoning, self.custom_styles["TCSReasoningText"]))
            
            # Add confidence indicator
            elements.append(Paragraph(
                f"Confidence: {market_trends.get('confidence_score', 0.8):.2f}", 
                self.custom_styles["TCSConfidence"]
            ))
        
        elements.append(PageBreak())
    
    def _add_strategic_recommendations(self, elements, integrated_data, visualizations):
        """Add strategic recommendations section."""
        elements.append(Paragraph("Strategic Recommendations", self.custom_styles["TCSHeading1"]))
        elements.append(Spacer(1, 0.1*inch))
        
        # Add recommendations visualization if available
        recommendations_vis = visualizations.get("strategic_recommendations", "")
        if recommendations_vis and os.path.exists(recommendations_vis):
            img = Image(recommendations_vis, width=6.5*inch, height=4*inch)
            elements.append(img)
            elements.append(Paragraph("Strategic Recommendations with Priority Ranking", self.custom_styles["TCSCaption"]))
            elements.append(Spacer(1, 0.2*inch))
        
        # Add recommendations text
        recommendations = integrated_data.get("integrated_analysis", {}).get("strategic_recommendations", {})
        overall_rec = recommendations.get("overall_recommendation", "")

        if overall_rec:
            elements.append(Paragraph("Overall Strategy", self.custom_styles["TCSHeading2"]))
            elements.append(Paragraph(overall_rec, self.custom_styles["TCSBodyText"]))
            elements.append(Spacer(1, 0.1*inch))

    def _add_appendices(self, elements, data, integrated_data):
        """Add appendices with detailed data."""
        elements.append(Paragraph("Appendices", self.custom_styles["TCSHeading1"]))
        elements.append(Spacer(1, 0.1*inch))
        
        # Add domain information
        elements.append(Paragraph("Appendix A: Domain Information", 
                               self.custom_styles["TCSHeading2"]))
        domain_info = data.get("domain_info", {})
        
        if domain_info and domain_info.get("success", False):
            # Create domain info table
            data_rows = [
                ["Attribute", "Value"]
            ]
            
            attributes = [
                ("Domain", domain_info.get("domain", "N/A")),
                ("Registrar", domain_info.get("registrar", "N/A")),
                ("Creation Date", domain_info.get("creation_date", "N/A")),
                ("Expiration Date", domain_info.get("expiration_date", "N/A")),
                ("Status", domain_info.get("status", "N/A"))
            ]
            
            for attr, value in attributes:
                data_rows.append([attr, value])
            
            domain_table = Table(data_rows, colWidths=[2*inch, 3*inch])
            domain_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            elements.append(domain_table)
            elements.append(Spacer(1, 0.3*inch))
        
        else:
            elements.append(Paragraph("No domain information available.", self.custom_styles["TCSBodyText"]))
            elements.append(PageBreak())
        
        # Add news articles
        elements.append(Paragraph("Appendix B: News Articles", self.custom_styles["TCSHeading2"]))
        news_data = data.get("news", {})
        articles = news_data.get("articles", [])
        
        if articles:
            for i, article in enumerate(articles[:5]):  # Limit to 5 articles
                title = article.get("title", "")
                date = article.get("publishedAt", "")
                description = article.get("description", "")
                url = article.get("url", "")
                
                elements.append(Paragraph(f"Article {i+1}: {title}", self.custom_styles["TCSBodyText"]))
                elements.append(Paragraph(f"Date: {date}", self.custom_styles["TCSNotes"]))
                if description:
                    elements.append(Paragraph(f"Summary: {description}", self.custom_styles["TCSNotes"]))
                if url:
                    elements.append(Paragraph(f"Source: {url}", self.custom_styles["TCSNotes"]))
                
                elements.append(Spacer(1, 0.1*inch))
        else:
            elements.append(Paragraph("No news articles available.", self.custom_styles["TCSBodyText"]))
        
        # Add report metadata footer
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(
            f"Report generated by OnSide AI | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.custom_styles["TCSCaption"]
        ))
    
    def _get_confidence_color(self, confidence: float) -> str:
        """Get color based on confidence score."""
        if confidence >= 0.7:
            return colors.green
        elif confidence >= 0.4:
            return colors.orange
        else:
            return colors.red
            
    def _create_report_metadata(self, report_data: Dict[str, Any]) -> List[Any]:
        """Create a page with report metadata and generation details."""
        elements = []
        
        # We don't need an extra page break here
        # elements.append(PageBreak())
        
        # Add a title for the metadata section
        elements.append(Paragraph(
            "Report Metadata",
            self.styles['OnSide-Heading1']
        ))
        
        # Add a horizontal line under the title
        elements.append(HRFlow(
            width="100%",
            thickness=1,
            lineCap='round',
            color=self.ONSIDE_LIGHT_BLUE,
            spaceBefore=6,
            spaceAfter=12
        ))
        
        # Get metadata from report data
        metadata = report_data.get('metadata', {})
        
        # Create data for the table
        data = [
            ['Generated On', metadata.get('generation_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))],
            ['Report Version', metadata.get('version', '1.0')],
            ['Generated By', metadata.get('generated_by', 'OnSide Analytics Platform')],
            ['Data Sources', metadata.get('data_sources', 'Multiple sources')],
            ['Analysis Type', metadata.get('analysis_type', 'Comprehensive')],
        ]
        
        # Add disclaimer if available
        if 'disclaimer' in metadata:
            data.append(['Disclaimer', metadata['disclaimer']])
        
        # Create the table
        table = Table(data, colWidths=[2*inch, 4*inch])
        
        # Style the table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Add a footer note
        elements.append(Paragraph(
            "This report was generated by the OnSide Analytics Platform. "
            "For any questions or concerns, please contact the OnSide support team.",
            self.styles['OnSide-Footer']
        ))
        
        return elements


# Test function
def test_service():
    """Test the enhanced PDF service with sample data."""
    try:
        # Sample data for testing
        sample_data = {
            "metadata": {
                "title": "Competitive Intelligence Report",
                "report_id": "test_123",
                "generated_at": "2025-05-16T22:30:00Z",
                "company": "Test Company",
                "client_name": "Acme Corporation",
                "prepared_by": "OnSide Analytics Team",
                "date": "Q2 2025"
            },
            "executive_summary": "This is a test executive summary for the PDF report. It provides a high-level overview of the key findings and recommendations from our analysis.",
            "competitor_analysis": {
                "overview": "Analysis of key competitors in the market.",
                "competitors": [
                    {
                        "name": "Competitor A", 
                        "market_share": 30, 
                        "strengths": ["Strong brand", "Wide distribution"], 
                        "weaknesses": ["High prices", "Slow innovation"],
                        "opportunities": ["Emerging markets", "Product line expansion"],
                        "threats": ["New entrants", "Price competition"]
                    },
                    {
                        "name": "Competitor B", 
                        "market_share": 25, 
                        "strengths": ["Innovative", "Good customer service"], 
                        "weaknesses": ["Limited distribution"],
                        "opportunities": ["Online expansion"],
                        "threats": ["Market consolidation"]
                    }
                ],
                "key_insights": [
                    "Competitor A dominates with 30% market share",
                    "Competitor B shows strong innovation but limited reach"
                ]
            },
            "market_analysis": {
                "overview": "Analysis of current market conditions and trends.",
                "market_size": 1000000,
                "growth_rate": 0.05,
                "trends": ["Growing demand", "Increased competition", "Digital transformation"],
                "segments": [
                    {"name": "Enterprise", "size": 500000, "growth": 0.06},
                    {"name": "SMB", "size": 300000, "growth": 0.04},
                    {"name": "Consumer", "size": 200000, "growth": 0.03}
                ],
                "key_insights": [
                    "Market growing at 5% annually",
                    "Enterprise segment shows strongest growth"
                ]
            },
            "swot_analysis": {
                "overview": "SWOT analysis of the current market position.",
                "strengths": ["Strong brand", "Loyal customer base", "Innovative products"],
                "weaknesses": ["Limited online presence", "High operational costs", "Slow time-to-market"],
                "opportunities": ["Market expansion", "New product lines", "Digital transformation"],
                "threats": ["New competitors", "Regulatory changes", "Economic downturn"]
            },
            "strategic_recommendations": [
                {
                    "priority": "High", 
                    "action": "Expand digital marketing efforts",
                    "description": "Increase online presence through targeted digital marketing campaigns.",
                    "expected_impact": "High",
                    "timeline": "3-6 months"
                },
                {
                    "priority": "Medium", 
                    "action": "Diversify product portfolio",
                    "description": "Introduce new products to address emerging market segments.",
                    "expected_impact": "Medium",
                    "timeline": "6-12 months"
                },
                {
                    "priority": "Low", 
                    "action": "Explore new markets",
                    "description": "Conduct market research to identify potential expansion opportunities.",
                    "expected_impact": "Long-term",
                    "timeline": "12+ months"
                }
            ],
            "appendices": {
                "methodology": "This report was prepared using a combination of primary and secondary research methods...",
                "data_sources": [
                    "Internal company data",
                    "Market research reports",
                    "Competitor websites and filings",
                    "Industry publications"
                ],
                "definitions": {
                    "SMB": "Small and Medium-sized Businesses",
                    "CAGR": "Compound Annual Growth Rate"
                }
            }
        }
        
        # For this test, we'll just test the KPMG PDF service directly
        # Use an absolute path for the output directory
        output_dir = Path("/Volumes/Cody/projects/OnSide/exports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_service = KPMGPDFService(str(output_dir))
        pdf_path = pdf_service.create_kpmg_report(sample_data, "test_kpmg_report")
        
        # Print the full path where the PDF was saved
        full_path = Path(pdf_path).resolve()
        print(f"\n✅ KPMG PDF report created at: {full_path}")
        print(f"   File exists: {full_path.exists()}")
        
        # List the contents of the output directory
        print("\nContents of output directory:")
        for f in output_dir.glob("*"):
            print(f"  - {f.name} (size: {f.stat().st_size} bytes)")
        return pdf_path
        
    except Exception as e:
        print(f"\n❌ Error testing PDF service: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return ""
        
    def test_service(self) -> str:
        """Test the PDF service with sample data."""
        try:
            # Sample test data
            sample_data = {
                "metadata": {
                    "title": "Strategic Market Analysis Report",
                    "client_name": "Test Client Inc.",
                    "prepared_by": "OnSide Analytics Team",
                    "date": datetime.now().strftime('%B %d, %Y')
                },
                "executive_summary": {
                    "overview": "This report provides a comprehensive analysis of market conditions and strategic recommendations.",
                    "key_insights": [
                        "Market shows strong growth potential",
                        "Competitive landscape is evolving",
                        "Digital transformation presents opportunities"
                    ]
                },
                "competitor_analysis": {
                    "overview": "Analysis of key competitors in the market.",
                    "competitors": [
                        {
                            "name": "Competitor A",
                            "strengths": ["Strong brand", "Large market share"],
                            "weaknesses": ["High costs", "Limited innovation"]
                        },
                        {
                            "name": "Competitor B",
                            "strengths": ["Innovative products", "Efficient operations"],
                            "weaknesses": ["Small market share", "Limited resources"]
                        }
                    ],
                    "market_share": {
                        "chart_data": {
                            "labels": ["Our Company", "Competitor A", "Competitor B", "Others"],
                            "values": [30, 25, 20, 25]
                        }
                    }
                },
                "market_analysis": {
                    "overview": "Analysis of current market conditions and trends.",
                    "market_size": 1000000,
                    "growth_rate": 0.05,
                    "trends": ["Growing demand", "Increased competition", "Digital transformation"],
                    "segments": [
                        {"name": "Enterprise", "size": 500000, "growth": 0.06},
                        {"name": "SMB", "size": 300000, "growth": 0.04},
                        {"name": "Consumer", "size": 200000, "growth": 0.03}
                    ],
                    "key_insights": [
                        "Market growing at 5% annually",
                        "Enterprise segment shows strongest growth"
                    ]
                },
                "swot_analysis": {
                    "overview": "SWOT analysis of the current market position.",
                    "strengths": ["Strong brand", "Loyal customer base", "Innovative products"],
                    "weaknesses": ["Limited online presence", "High operational costs", "Slow time-to-market"],
                    "opportunities": ["Market expansion", "New product lines", "Digital transformation"],
                    "threats": ["New competitors", "Regulatory changes", "Economic downturn"]
                },
                "strategic_recommendations": [
                    {
                        "priority": "High", 
                        "action": "Expand digital marketing efforts",
                        "description": "Increase online presence through targeted digital marketing campaigns.",
                        "expected_impact": "High",
                        "timeline": "3-6 months"
                    },
                    {
                        "priority": "Medium", 
                        "action": "Diversify product portfolio",
                        "description": "Introduce new products to address emerging market segments.",
                        "expected_impact": "Medium",
                        "timeline": "6-12 months"
                    },
                    {
                        "priority": "Low", 
                        "action": "Explore new markets",
                        "description": "Conduct market research to identify potential expansion opportunities.",
                        "expected_impact": "Long-term",
                        "timeline": "12+ months"
                    }
                ],
                "appendices": {
                    "methodology": "This report was prepared using a combination of primary and secondary research methods...",
                    "data_sources": [
                        "Internal company data",
                        "Market research reports",
                        "Competitor websites and filings",
                        "Industry publications"
                    ],
                    "definitions": {
                        "SMB": "Small and Medium-sized Businesses",
                        "CAGR": "Compound Annual Growth Rate"
                    }
                }
            }
            
            # For this test, we'll just test the KPMG PDF service directly
            # Use an absolute path for the output directory
            output_dir = Path("/Volumes/Cody/projects/OnSide/exports")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            pdf_service = KPMGPDFService(str(output_dir))
            pdf_path = pdf_service.create_kpmg_report(sample_data, "test_kpmg_report")
            
            # Print the full path where the PDF was saved
            full_path = Path(pdf_path).resolve()
            print(f"\n✅ KPMG PDF report created at: {full_path}")
            print(f"   File exists: {full_path.exists()}")
            
            # List the contents of the output directory
            print("\nContents of output directory:")
            for f in output_dir.glob("*"):
                print(f"  - {f.name} (size: {f.stat().st_size} bytes)")
            return pdf_path
            
        except Exception as e:
            print(f"\n❌ Error testing PDF service: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return ""


if __name__ == "__main__":
    KPMGPDFService().test_service()