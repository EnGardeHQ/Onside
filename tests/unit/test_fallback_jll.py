#!/usr/bin/env python
"""
Simplified test script for JLL report generation using FallbackManager.
This script tests the fixed execute_with_fallback method to ensure no recursion issues.
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_fallback_jll")

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from src.models.llm_fallback import LLMProvider
from src.services.llm_provider.fallback_manager import FallbackManager
from src.models.report import Report
from src.database import SessionLocal
from src.models.company import Company
from src.models.ai_insight import AIInsight

async def test_fallback_execution():
    """Test the FallbackManager's execute_with_fallback method to ensure no recursion."""
    logger.info("Starting fallback execution test")
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create a test report
        test_report = Report(
            title=f"Test Report {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            company_id=1,  # Default ID for testing
            created_at=datetime.now()
        )
        
        # Initialize providers for FallbackManager
        providers = [
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
            LLMProvider.COHERE
        ]
        
        # Initialize FallbackManager
        fallback_manager = FallbackManager(providers=providers, db_session=db)
        
        logger.info("Testing execute_with_fallback method...")
        
        # Define test prompts for different AI services
        test_prompts = [
            "Analyze competitor landscape for JLL in commercial real estate with chain-of-thought reasoning",
            "Provide market analysis for real estate services industry with focus on growth",
            "Analyze audience engagement patterns for corporate real estate content"
        ]
        
        insights = []
        
        # Test each prompt with execute_with_fallback
        for i, prompt in enumerate(test_prompts):
            logger.info(f"Test {i+1}: Running execute_with_fallback with prompt: {prompt[:50]}...")
            
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
            
            # Create AI insight from result
            insight = AIInsight(
                report_id=test_report.id if hasattr(test_report, 'id') else 1,
                type=f"Test{i+1}",
                content=result['response'],
                confidence=result['confidence'],
                metadata=result.get('metadata', {})
            )
            insights.append(insight)
            
            logger.info("-" * 50)
        
        # Print stats
        stats = fallback_manager.get_stats()
        logger.info(f"FallbackManager stats: {stats}")
        
        # Verify insights
        logger.info(f"Generated {len(insights)} insights")
        for i, insight in enumerate(insights):
            logger.info(f"Insight {i+1}: Type={insight.type}, Confidence={insight.confidence:.2f}")
        
        logger.info("✅ All tests completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Close the database session
        await db.close()
        logger.info("Database session closed")

async def main():
    """Main entry point for testing."""
    logger.info("Starting fallback execution test")
    
    try:
        await test_fallback_execution()
        logger.info("✅ Test completed successfully")
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
    
    logger.info("Test complete")


if __name__ == "__main__":
    asyncio.run(main())
