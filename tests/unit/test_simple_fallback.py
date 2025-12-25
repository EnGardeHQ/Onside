#!/usr/bin/env python
"""
Minimal test script for FallbackManager's execute_with_fallback method.
This script tests the method directly without complex dependencies.
"""
import os
import sys
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_simple_fallback")

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the FallbackManager
from src.models.llm_fallback import LLMProvider
from src.services.llm_provider.fallback_manager import FallbackManager

# Simple mock Report class
class MockReport:
    """Mock Report class for testing."""
    def __init__(self, id=1, title="Test Report"):
        self.id = id
        self.title = title
        self.created_at = datetime.now()

async def test_fallback_execution():
    """Test the execute_with_fallback method directly."""
    logger.info("Starting simplified fallback execution test")
    
    # Create a test report
    test_report = MockReport()
    
    # Initialize providers for FallbackManager
    providers = [
        LLMProvider.OPENAI,
        LLMProvider.ANTHROPIC,
        LLMProvider.COHERE
    ]
    
    # Initialize FallbackManager
    fallback_manager = FallbackManager(providers=providers)
    
    # Define test prompts
    test_prompts = [
        "Analyze competitor landscape for JLL in commercial real estate with chain-of-thought reasoning",
        "Provide market analysis for real estate services industry with focus on growth",
        "Analyze audience engagement patterns for corporate real estate content"
    ]
    
    # Test each prompt with execute_with_fallback
    for i, prompt in enumerate(test_prompts):
        logger.info(f"Test {i+1}: Running execute_with_fallback with prompt: {prompt[:50]}...")
        
        try:
            result, provider = await fallback_manager.execute_with_fallback(
                prompt=prompt,
                report=test_report,
                confidence_threshold=0.7,
                max_tokens=1000,
                temperature=0.7
            )
            
            logger.info(f"✅ Response received from provider: {provider}")
            logger.info(f"Confidence: {result.get('confidence', 0):.2f}")
            
            if "reasoning" in result:
                logger.info(f"Reasoning: {result['reasoning'][:100]}...")
            
            logger.info(f"Response: {result['response'][:100]}...")
            logger.info("-" * 50)
            
        except Exception as e:
            logger.error(f"❌ Error during test {i+1}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Print stats
    stats = fallback_manager.get_stats()
    logger.info(f"FallbackManager stats: {stats}")
    logger.info("Test complete")

async def main():
    """Main entry point for testing."""
    logger.info("Starting minimal fallback test")
    
    try:
        await test_fallback_execution()
        logger.info("✅ All tests completed successfully")
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("Test complete")

if __name__ == "__main__":
    asyncio.run(main())
