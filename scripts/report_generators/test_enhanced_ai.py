#!/usr/bin/env python
"""
Test Enhanced AI Service

A simple script to test the enhanced AI service with sample data.
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path to ensure imports work
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import the enhanced AI service
from scripts.report_generators.services.enhanced_ai_service_clean import EnhancedAIService

# Sample data for testing
SAMPLE_DATA = {
    "company": {
        "name": "Test Company",
        "industry": "Technology",
        "description": "A leading technology company specializing in AI solutions."
    },
    "data_points": [
        {
            "text": "We're seeing strong growth in our AI division.",
            "sentiment": 0.8,
            "source": "internal"
        },
        {
            "text": "Customer feedback has been positive overall.",
            "sentiment": 0.7,
            "source": "survey"
        },
        {
            "text": "There are some concerns about market saturation.",
            "sentiment": -0.3,
            "source": "news"
        },
        {
            "text": "Our latest product launch was well received.",
            "sentiment": 0.9,
            "source": "social_media"
        },
        {
            "text": "There are some issues with customer support response times.",
            "sentiment": -0.5,
            "source": "feedback"
        }
    ]
}

async def main():
    """Main function to test the enhanced AI service."""
    print("🚀 Starting Enhanced AI Service Test")
    
    # Initialize the AI service
    ai_service = EnhancedAIService()
    
    try:
        # Test analyze_data method
        print("\n🔍 Analyzing data...")
        analysis = await ai_service.analyze_data(SAMPLE_DATA)
        
        # Print results
        print("\n📊 Analysis Results:")
        print(json.dumps(analysis, indent=2, default=str))
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
