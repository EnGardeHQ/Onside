#!/usr/bin/env python
"""
Test Enhanced TCS Report Generation

This script tests the enhanced TCS report generator with sample data
to validate the integration of all components.

Following Semantic Seed Venture Studio Coding Standards V2.0.
"""

import os
import sys
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional
import unittest
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_enhanced_tcs")

# Add parent directory to path to ensure import availability
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import the report generator
from report_generators.enhanced_tcs_report_generator import EnhancedTCSReportGenerator


class TestEnhancedTCSReport(unittest.TestCase):
    """
    Test suite for the enhanced TCS report generator.
    """
    
    def setUp(self):
        """Set up test environment."""
        self.output_dir = Path("test_outputs")
        self.output_dir.mkdir(exist_ok=True)
        
        # Create sample data path
        self.sample_data_path = self.output_dir / "tcs_api_sample.json"
        
        # Generate sample data if it doesn't exist
        if not self.sample_data_path.exists():
            self._generate_sample_data()
    
    def _generate_sample_data(self):
        """Generate sample API data for testing."""
        sample_data = {
            "domain_info": {
                "domain": "example.com",
                "registered": True,
                "creation_date": "2005-08-21",
                "expiration_date": "2025-08-21",
                "registrar": "Example Registrar, LLC",
                "status": "active"
            },
            "seo": {
                "title": "Example Domain",
                "description": "Example website for demonstration purposes",
                "keywords": ["example", "test", "demonstration"],
                "traffic_estimate": 15000,
                "backlinks": 1250,
                "meta_tags": {
                    "robots": "index, follow",
                    "viewport": "width=device-width, initial-scale=1.0"
                },
                "page_load_time": 1.5
            },
            "search": {
                "related_queries": [
                    "example domain purpose",
                    "example website template",
                    "what is an example domain",
                    "example websites for business",
                    "example.com vs example.org"
                ],
                "top_keywords": [
                    "example domain",
                    "test website",
                    "sample webpage",
                    "domain examples",
                    "web standards"
                ],
                "volume_data": {
                    "example domain": 5400,
                    "test website": 8200,
                    "sample webpage": 3100,
                    "domain examples": 2700,
                    "web standards": 6500
                },
                "categories": [
                    "Technology",
                    "Web Development",
                    "Domain Names",
                    "Internet Standards"
                ]
            },
            "competitive": {
                "competitors": [
                    {
                        "name": "Competitor A",
                        "domain": "competitora.com",
                        "traffic_estimate": 25000,
                        "overlap_score": 0.65,
                        "market_share": 0.18,
                        "growth_rate": 0.12,
                        "ranking": {
                            "global": 15000,
                            "local": 1200,
                            "category": 350
                        }
                    },
                    {
                        "name": "Competitor B",
                        "domain": "competitorb.com",
                        "traffic_estimate": 18000,
                        "overlap_score": 0.48,
                        "market_share": 0.12,
                        "growth_rate": 0.08,
                        "ranking": {
                            "global": 22000,
                            "local": 1800,
                            "category": 520
                        }
                    },
                    {
                        "name": "Competitor C",
                        "domain": "competitorc.net",
                        "traffic_estimate": 32000,
                        "overlap_score": 0.35,
                        "market_share": 0.22,
                        "growth_rate": 0.15,
                        "ranking": {
                            "global": 12000,
                            "local": 950,
                            "category": 280
                        }
                    }
                ]
            },
            "news": {
                "articles": [
                    {
                        "title": "Example Domain Celebrates 20 Years",
                        "description": "The iconic example.com domain marks two decades of serving as the standard example in documentation.",
                        "publishedAt": "2023-08-21T08:15:00Z",
                        "source": {
                            "name": "Tech News Daily"
                        },
                        "url": "https://technews.example/articles/example-domain-anniversary"
                    },
                    {
                        "title": "Web Standards Organization Recognizes Example Domain",
                        "description": "Example.com receives recognition for its role in web development education and documentation.",
                        "publishedAt": "2023-07-15T14:30:00Z",
                        "source": {
                            "name": "Web Developer Weekly"
                        },
                        "url": "https://webdev.example/news/standards-recognition"
                    },
                    {
                        "title": "Using Example Domains in Education",
                        "description": "How example domains are helping students learn web development concepts safely.",
                        "publishedAt": "2023-06-22T09:45:00Z",
                        "source": {
                            "name": "Education Technology Review"
                        },
                        "url": "https://edtech.example/articles/example-domains-education"
                    }
                ]
            },
            "social": {
                "platforms": [
                    {
                        "name": "Twitter",
                        "handle": "@exampledomain",
                        "followers": 12500,
                        "engagement_rate": 0.028,
                        "activity_score": 76
                    },
                    {
                        "name": "LinkedIn",
                        "handle": "example-domain",
                        "followers": 8300,
                        "engagement_rate": 0.035,
                        "activity_score": 64
                    },
                    {
                        "name": "Facebook",
                        "handle": "ExampleDomain",
                        "followers": 15800,
                        "engagement_rate": 0.019,
                        "activity_score": 58
                    }
                ],
                "sentiment": {
                    "positive": 0.68,
                    "neutral": 0.25,
                    "negative": 0.07
                },
                "trend_topics": [
                    "Web examples",
                    "Documentation standards",
                    "Learning resources"
                ]
            },
            "engagement": {
                "channels": {
                    "organic_search": 0.42,
                    "direct": 0.30,
                    "social": 0.15,
                    "referral": 0.10,
                    "email": 0.03
                },
                "user_metrics": {
                    "avg_session_duration": 185,  # seconds
                    "bounce_rate": 0.35,
                    "pages_per_session": 2.4
                },
                "content_engagement": [
                    {
                        "page": "/home",
                        "views": 25000,
                        "avg_time": 145,  # seconds
                        "bounce_rate": 0.30
                    },
                    {
                        "page": "/about",
                        "views": 12000,
                        "avg_time": 210,  # seconds
                        "bounce_rate": 0.22
                    },
                    {
                        "page": "/examples",
                        "views": 18500,
                        "avg_time": 280,  # seconds
                        "bounce_rate": 0.18
                    }
                ]
            }
        }
        
        # Save the sample data
        with open(self.sample_data_path, 'w') as f:
            json.dump(sample_data, f, indent=4)
        
        logger.info(f"Generated sample API data at {self.sample_data_path}")
    
    def test_report_generation_with_sample_data(self):
        """Test report generation with sample data."""
        try:
            # Load sample data
            with open(self.sample_data_path, 'r') as f:
                sample_data = json.load(f)
            
            # Create report generator
            generator = EnhancedTCSReportGenerator(output_dir=str(self.output_dir))
            
            # Generate report
            report_path = generator.generate_report(input_data=sample_data)
            
            # Check if report was generated successfully
            self.assertTrue(report_path, "Report should be generated successfully")
            self.assertTrue(Path(report_path).exists(), "Report file should exist")
            
            logger.info(f"Successfully generated report at {report_path}")
            
        except Exception as e:
            self.fail(f"Test failed with exception: {str(e)}\n{traceback.format_exc()}")
    
    @patch('report_generators.enhanced_tcs_report_generator.EnhancedAIService')
    @patch('report_generators.enhanced_tcs_report_generator.DataIntegrationService')
    @patch('report_generators.enhanced_tcs_report_generator.EnhancedVisualizationService')
    @patch('report_generators.enhanced_tcs_report_generator.EnhancedPDFService')
    def test_service_integration(self, mock_pdf, mock_viz, mock_integration, mock_ai):
        """Test integration of all services."""
        # Configure mocks
        mock_ai_instance = MagicMock()
        mock_ai_instance.analyze_data.return_value = {"analysis": "Sample AI analysis"}
        mock_ai.return_value = mock_ai_instance
        
        mock_integration_instance = MagicMock()
        mock_integration_instance.integrate_data.return_value = {"integrated": "Sample integrated data"}
        mock_integration.return_value = mock_integration_instance
        
        mock_viz_instance = MagicMock()
        mock_viz_instance.create_all_visualizations.return_value = {"viz1": "path/to/viz1.png"}
        mock_viz.return_value = mock_viz_instance
        
        mock_pdf_instance = MagicMock()
        mock_pdf_instance.create_pdf_report.return_value = str(self.output_dir / "mock_report.pdf")
        mock_pdf.return_value = mock_pdf_instance
        
        # Create generator with mocks
        generator = EnhancedTCSReportGenerator(output_dir=str(self.output_dir))
        
        # Load sample data
        with open(self.sample_data_path, 'r') as f:
            sample_data = json.load(f)
        
        # Generate report
        report_path = generator.generate_report(input_data=sample_data)
        
        # Verify service interactions
        mock_ai_instance.analyze_data.assert_called_once()
        mock_integration_instance.integrate_data.assert_called_once()
        mock_viz_instance.create_all_visualizations.assert_called_once()
        mock_pdf_instance.create_pdf_report.assert_called_once()
        
        # Check result
        self.assertEqual(report_path, str(self.output_dir / "mock_report.pdf"))


def run_test():
    """Run the test suite."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEnhancedTCSReport)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return result.wasSuccessful()


def demo_report():
    """Generate a demo report using the enhanced TCS report generator."""
    try:
        # Define output directory
        output_dir = Path("exports")
        output_dir.mkdir(exist_ok=True)
        
        # Create sample data path
        sample_data_path = output_dir / "tcs_api_demo.json"
        
        # Check if sample data exists
        if not sample_data_path.exists():
            # Copy from test directory or create new
            test_output = Path("test_outputs")
            if (test_output / "tcs_api_sample.json").exists():
                # Copy from test directory
                import shutil
                shutil.copy(test_output / "tcs_api_sample.json", sample_data_path)
            else:
                # Create test instance to generate sample data
                test = TestEnhancedTCSReport()
                test.output_dir = output_dir
                test.sample_data_path = sample_data_path
                test._generate_sample_data()
        
        # Load sample data
        with open(sample_data_path, 'r') as f:
            sample_data = json.load(f)
        
        print("\n🔍 Generating enhanced TCS report with KPMG-style analytics...\n")
        
        # Create report generator
        generator = EnhancedTCSReportGenerator(output_dir=str(output_dir), verbose=True)
        
        # Generate report
        report_path = generator.generate_report(input_data=sample_data)
        
        if report_path:
            print(f"\n✅ Successfully generated enhanced TCS report: {report_path}")
            return report_path
        else:
            print("\n❌ Failed to generate report")
            return None
        
    except Exception as e:
        print(f"\n❌ Error in demo: {str(e)}")
        print(traceback.format_exc())
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test or demo the enhanced TCS report generator')
    parser.add_argument('--mode', '-m', choices=['test', 'demo'], default='demo',
                        help='Run mode (test or demo)')
    
    args = parser.parse_args()
    
    if args.mode == 'test':
        print("\n🧪 Running Enhanced TCS Report Generator tests...\n")
        success = run_test()
        sys.exit(0 if success else 1)
    else:
        demo_report()
