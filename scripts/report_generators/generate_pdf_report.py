"""
PDF Report Generator with Visualizations

This module creates formatted PDF reports with actual visualizations.
Following the Semantic Seed Venture Studio Coding Standards.
"""

import os
import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server-side generation
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from fpdf import FPDF
import io
from PIL import Image
import base64
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pdf_generator')

class EnhancedReportPDF(FPDF):
    """Enhanced PDF report generator with headers, footers, and styling."""
    
    def __init__(self, title="TCS Enhanced Report"):
        # Initialize with standard settings
        super().__init__(orientation='P', unit='mm', format='A4')
        self.title = title
        self.set_auto_page_break(auto=True, margin=15)
        self.company_name = "Tata Consultancy Services"
        
    def header(self):
        """Add header to each page with logo and title."""
        # Add company logo if available
        # self.image('logo.png', 10, 8, 33)
        
        # Set header styling
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self.title, 0, 1, 'C')
        self.ln(5)
        
    def footer(self):
        """Add footer with page numbers."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        
    def chapter_title(self, title):
        """Add formatted chapter title."""
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, 0, 1, 'L', True)
        self.ln(5)
        
    def section_title(self, title):
        """Add formatted section title."""
        self.set_font('Arial', 'B', 12)
        self.cell(0, 6, title, 0, 1, 'L')
        self.ln(2)
        
    def body_text(self, text):
        """Add formatted body text with safe Unicode handling."""
        # Replace Unicode bullet points with ASCII equivalent
        safe_text = text.replace('•', '*').replace('\u2022', '*')
        # Handle other potentially problematic Unicode characters
        safe_text = ''.join(c if ord(c) < 128 else '?' for c in safe_text)
        
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, safe_text)
        self.ln(2)
        
    def metric_box(self, title, value):
        """Add a formatted metric box."""
        width = 60
        height = 25
        
        # Save current position
        x = self.get_x()
        y = self.get_y()
        
        # Draw box
        self.set_fill_color(240, 240, 240)
        self.rect(x, y, width, height, 'DF')
        
        # Add title
        self.set_xy(x, y + 2)
        self.set_font('Arial', 'B', 10)
        self.cell(width, 8, title, 0, 1, 'C')
        
        # Add value
        self.set_xy(x, y + 12)
        self.set_font('Arial', 'B', 12)
        self.cell(width, 8, str(value), 0, 1, 'C')
        
        # Reset position to next box
        self.set_xy(x + width + 5, y)

def create_pie_chart(data, labels, title, filename):
    """Create a pie chart and save it to a file."""
    plt.figure(figsize=(8, 5))
    plt.pie(data, labels=labels, autopct='%1.1f%%', startangle=90, shadow=True)
    plt.title(title)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.savefig(filename, bbox_inches='tight')
    plt.close()
    return filename

def create_bar_chart(categories, values, title, xlabel, ylabel, filename):
    """Create a bar chart and save it to a file."""
    plt.figure(figsize=(10, 6))
    bars = plt.bar(categories, values, color='skyblue')
    
    # Add data values on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height:.1f}',
                ha='center', va='bottom')
    
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight')
    plt.close()
    return filename

def create_radar_chart(categories, values_list, labels, title, filename):
    """Create a radar chart for comparing multiple entities."""
    # Convert to numpy arrays
    categories = np.array(categories)
    
    # Number of variables
    N = len(categories)
    
    # Compute angle for each axis
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    
    # Make the plot close
    angles += angles[:1]
    
    plt.figure(figsize=(10, 10))
    ax = plt.subplot(111, polar=True)
    
    for i, values in enumerate(values_list):
        # Make values circular
        values = np.array(values)
        values = np.append(values, values[0])
        
        # Plot values
        ax.plot(angles, values, linewidth=2, linestyle='solid', label=labels[i])
        ax.fill(angles, values, alpha=0.1)
    
    # Fix axis to go in the right order and start at top
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    
    # Draw axis lines for each angle and label
    plt.xticks(angles[:-1], categories)
    
    # Draw y-labels
    ax.set_rlabel_position(0)
    
    # Add legend
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    plt.title(title, y=1.08)
    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight')
    plt.close()
    return filename

def generate_pdf_report(data, output_dir=None):
    """
    Generate a PDF report with visualizations.
    
    Args:
        data: Dictionary containing the report data
        output_dir: Directory to save the report
        
    Returns:
        Path to the generated report
    """
    if output_dir is None:
        output_dir = Path.cwd() / "reports"
    elif isinstance(output_dir, str):
        output_dir = Path(output_dir)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create temp directory for charts
    temp_dir = output_dir / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    # Extract report data
    report_data = data.get("report_data", {})
    metadata = report_data.get("metadata", {})
    exec_summary = report_data.get("executive_summary", {})
    company_name = metadata.get("company", "Tata Consultancy Services")
    
    # Create PDF report
    pdf = EnhancedReportPDF()
    pdf.company_name = company_name
    pdf.title = metadata.get("title", "TCS Enhanced Report")
    
    # Add cover page
    pdf.add_page()
    pdf.set_font('Arial', 'B', 24)
    pdf.cell(0, 60, '', 0, 1, 'C')  # Add space
    pdf.cell(0, 20, pdf.title, 0, 1, 'C')
    pdf.set_font('Arial', '', 14)
    pdf.cell(0, 10, f'Analysis Report for {company_name}', 0, 1, 'C')
    pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%B %d, %Y")}', 0, 1, 'C')
    
    # Executive Summary
    pdf.add_page()
    pdf.chapter_title("Executive Summary")
    pdf.body_text(exec_summary.get("content", "No executive summary available"))
    
    # Key Metrics
    pdf.ln(5)
    pdf.section_title("Key Metrics")
    
    # Add metrics in a row (3 per row)
    metrics = exec_summary.get("key_metrics", {})
    count = 0
    for key, value in metrics.items():
        if count % 3 == 0 and count > 0:
            pdf.ln(30)  # Add space for new row
        
        metric_name = " ".join(word.capitalize() for word in key.split("_"))
        pdf.metric_box(metric_name, value)
        count += 1
    
    # Reset position after metrics
    if metrics:
        pdf.ln(30)
    
    # Geographic Revenue Analysis with visualization
    geo_analysis = report_data.get("geographic_revenue_analysis", {})
    if geo_analysis:
        pdf.add_page()
        pdf.chapter_title("Geographic Revenue Analysis")
        pdf.body_text(geo_analysis.get("content", ""))
        
        # Create a pie chart for geographic revenue
        regions = geo_analysis.get("data", {}).get("regions", [])
        shares = geo_analysis.get("data", {}).get("revenue_share", [])
        
        if regions and shares:
            chart_path = temp_dir / "geo_revenue.png"
            create_pie_chart(
                shares, 
                regions, 
                "Revenue by Geographic Region (2024)", 
                chart_path
            )
            
            # Add chart to PDF
            pdf.image(str(chart_path), x=15, y=pdf.get_y() + 5, w=180)
            pdf.ln(120)  # Move down for space after chart
    
    # Service Line Analysis with visualization
    service_line = report_data.get("service_line_analysis", {})
    if service_line:
        pdf.add_page()
        pdf.chapter_title("Service Line Analysis")
        pdf.body_text(service_line.get("content", ""))
        
        # Create a bar chart for service lines
        services = service_line.get("data", {}).get("services", [])
        shares = service_line.get("data", {}).get("revenue_share", [])
        
        if services and shares:
            chart_path = temp_dir / "service_line.png"
            create_bar_chart(
                services,
                shares,
                "Revenue by Service Line (2024)",
                "Service Line",
                "Revenue Share (%)",
                chart_path
            )
            
            # Add chart to PDF
            pdf.image(str(chart_path), x=15, y=pdf.get_y() + 5, w=180)
            pdf.ln(120)  # Move down for space after chart
    
    # Competitive Landscape with radar chart
    comp_landscape = report_data.get("competitive_landscape", {})
    if comp_landscape:
        pdf.add_page()
        pdf.chapter_title("Competitive Landscape")
        pdf.body_text(comp_landscape.get("content", ""))
        
        competitors = comp_landscape.get("competitors", [])
        metrics = comp_landscape.get("metrics", [])
        
        if competitors and metrics:
            # Extract competitor names
            comp_names = [comp.get("name", f"Competitor {i+1}") for i, comp in enumerate(competitors)]
            
            # Create structured data for radar chart
            metric_values = []
            for competitor in competitors:
                values = []
                for metric in metrics:
                    values.append(float(competitor.get(metric, 0)))
                metric_values.append(values)
            
            # Create radar chart
            chart_path = temp_dir / "competitive_radar.png"
            create_radar_chart(
                metrics,
                metric_values,
                comp_names,
                "Competitive Analysis",
                chart_path
            )
            
            # Add chart to PDF
            pdf.image(str(chart_path), x=15, y=pdf.get_y() + 5, w=180)
            pdf.ln(120)  # Move down for space after chart
    
    # SWOT Analysis
    swot = report_data.get("swot_analysis", {})
    if swot:
        pdf.add_page()
        pdf.chapter_title("SWOT Analysis")
        pdf.body_text(swot.get("content", ""))
        
        # Strengths
        pdf.section_title("Strengths")
        for strength in swot.get("strengths", []):
            pdf.body_text(f"* {strength}")
        
        # Weaknesses
        pdf.section_title("Weaknesses")
        for weakness in swot.get("weaknesses", []):
            pdf.body_text(f"* {weakness}")
        
        # Opportunities
        pdf.section_title("Opportunities")
        for opportunity in swot.get("opportunities", []):
            pdf.body_text(f"* {opportunity}")
        
        # Threats
        pdf.section_title("Threats")
        for threat in swot.get("threats", []):
            pdf.body_text(f"* {threat}")
    
    # Strategic Recommendations
    recommendations = report_data.get("strategic_recommendations", {}).get("recommendations", [])
    if recommendations:
        pdf.add_page()
        pdf.chapter_title("Strategic Recommendations")
        
        for rec in recommendations:
            pdf.section_title(rec.get("title", ""))
            pdf.body_text(f"Description: {rec.get('description', '')}")
            pdf.body_text(f"Priority: {rec.get('priority', '')}")
            pdf.body_text(f"Impact: {rec.get('impact', '')}")
            pdf.ln(5)
    
    # Save the PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_company_name = company_name.replace(" ", "_")
    output_filename = f"{safe_company_name}_analysis_report_{timestamp}.pdf"
    output_path = output_dir / output_filename
    
    pdf.output(str(output_path))
    logger.info(f"PDF report generated: {output_path}")
    
    return output_path

if __name__ == "__main__":
    # Test data
    with open("sample_data.json", "r") as f:
        test_data = json.load(f)
    
    generate_pdf_report(test_data)
