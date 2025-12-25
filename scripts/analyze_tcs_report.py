#!/usr/bin/env python3
"""
Analyze TCS Report against KPMG Standards

This script checks if the TCS report meets the KPMG standards by verifying the presence of required sections and content.
"""

import sys
import json
from pathlib import Path
from PyPDF2 import PdfReader

# KPMG Required Sections
KPMG_REQUIRED_SECTIONS = [
    "Executive Summary",
    "Competitor Analysis",
    "Market Analysis",
    "SWOT Breakdown",
    "Strategic Recommendations",
    "Confidence Ratings & Reasoning Chains",
    "Professional Charts & Visualizations"
]

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None
    return text

def check_kpmg_compliance(report_text):
    """Check if the report meets KPMG standards."""
    results = {}
    
    # Check for required sections
    missing_sections = []
    present_sections = []
    
    for section in KPMG_REQUIRED_SECTIONS:
        if section.lower() in report_text.lower():
            present_sections.append(section)
        else:
            missing_sections.append(section)
    
    results['missing_sections'] = missing_sections
    results['present_sections'] = present_sections
    
    # Check for key elements
    key_elements = {
        'has_confidence_scores': any(score in report_text.lower() for score in ['confidence:', 'confidence score', 'confidence:']),
        'has_visualizations': any(term in report_text.lower() for term in ['figure', 'chart', 'graph', 'visualization']),
        'has_recommendations': 'recommendation' in report_text.lower(),
        'has_swot': 'swot' in report_text.lower()
    }
    
    results['key_elements'] = key_elements
    
    # Calculate compliance score
    total_checks = len(KPMG_REQUIRED_SECTIONS) + len(key_elements)
    passed_checks = len(present_sections) + sum(1 for v in key_elements.values() if v)
    results['compliance_score'] = f"{passed_checks}/{total_checks} ({(passed_checks/total_checks)*100:.1f}%)"
    
    return results

def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_tcs_report.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    print(f"Analyzing report: {pdf_path}")
    print("-" * 50)
    
    # Extract text from PDF
    report_text = extract_text_from_pdf(pdf_path)
    if not report_text:
        print("Failed to extract text from PDF")
        sys.exit(1)
    
    # Check KPMG compliance
    results = check_kpmg_compliance(report_text)
    
    # Print results
    print("\n📊 KPMG Compliance Analysis")
    print("=" * 50)
    
    print("\n✅ Present Sections:")
    for section in results['present_sections']:
        print(f"   - {section}")
    
    if results['missing_sections']:
        print("\n❌ Missing Sections:")
        for section in results['missing_sections']:
            print(f"   - {section}")
    
    print("\n🔍 Key Elements:")
    for element, present in results['key_elements'].items():
        status = "✅" if present else "❌"
        print(f"   {status} {element.replace('_', ' ').title()}")
    
    print("\n📈 Compliance Score:", results['compliance_score'])
    
    # Print recommendations
    print("\n💡 Recommendations:")
    if not results['missing_sections'] and all(results['key_elements'].values()):
        print("   - The report fully meets KPMG standards!")
    else:
        if results['missing_sections']:
            print(f"   - Add missing sections: {', '.join(results['missing_sections'])}")
        for element, present in results['key_elements'].items():
            if not present:
                print(f"   - Add {element.replace('_', ' ')}")

if __name__ == "__main__":
    main()
