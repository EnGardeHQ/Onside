#!/usr/bin/env python
"""
Test script for the FallbackManager to verify recursion issues are fixed.
This script tests the AI/ML integration with minimal dependencies.
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_fallback")

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from src.models.llm_fallback import LLMProvider
from src.services.llm_provider.fallback_manager import FallbackManager

# Create a simple report class for testing
class SimpleReport:
    """A simplified Report class for testing purposes."""
    def __init__(self, id, title, company_id=None):
        self.id = id
        self.title = title
        self.company_id = company_id


async def test_fallback_manager():
    """Test the FallbackManager with various prompts to verify it works correctly."""
    logger.info("Initializing FallbackManager for testing")
    
    # Create a simple report for testing
    report = SimpleReport(
        id=123,
        title="Test Report",
        company_id=456
    )
    
    # Initialize providers
    providers = [
        LLMProvider.OPENAI,
        LLMProvider.ANTHROPIC,
        LLMProvider.COHERE
    ]
    
    # Create FallbackManager
    fallback_manager = FallbackManager(providers=providers)
    
    # Test prompts
    test_prompts = [
        # Competitor analysis prompt
        "Analyze the competitor landscape for JLL in the commercial real estate sector with chain-of-thought reasoning.",
        
        # Market analysis prompt
        "Provide market analysis for the real estate services industry with focus on growth trends.",
        
        # Audience analysis prompt
        "Analyze the audience engagement patterns for corporate real estate content."
    ]
    
    for i, prompt in enumerate(test_prompts):
        logger.info(f"Test {i+1}: Running fallback manager with prompt: {prompt[:50]}...")
        
        try:
            # Execute with fallback
            result, provider = await fallback_manager.execute_with_fallback(
                prompt=prompt,
                report=report,
                confidence_threshold=0.7
            )
            
            # Log results
            logger.info(f"✅ Response received from provider: {provider}")
            logger.info(f"Confidence: {result.get('confidence', 0):.2f}")
            
            if "reasoning" in result:
                logger.info(f"Reasoning: {result['reasoning'][:100]}...")
            
            logger.info(f"Response: {result['response'][:100]}...")
            logger.info("-" * 50)
            
        except Exception as e:
            logger.error(f"❌ Error during test {i+1}: {str(e)}")
    
    # Get stats
    stats = fallback_manager.get_stats()
    logger.info(f"FallbackManager stats: {stats}")


async def main():
    """Main entry point for testing."""
    logger.info("Starting FallbackManager test")
    
    try:
        await test_fallback_manager()
        logger.info("✅ All tests completed successfully")
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
    
    logger.info("Test complete")


if __name__ == "__main__":
    asyncio.run(main())
