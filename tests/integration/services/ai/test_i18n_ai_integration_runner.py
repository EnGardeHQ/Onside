#!/usr/bin/env python
"""
Simple integration test runner for i18n AI integration.

This module provides a straightforward way to test the integration between
the i18n framework and AI services without external dependencies.
"""
import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

# Import required classes - with error handling for missing modules
try:
    from unittest.mock import MagicMock, AsyncMock
    
    from src.services.i18n.integration import I18nFramework
    from src.services.i18n.language_service import SupportedLanguage
    from src.services.ai.i18n_chain_of_thought import I18nAwareChainOfThought
    from src.services.llm_provider.fallback_manager import FallbackManager
    from src.models.report import Report
    from src.models.llm_fallback import LLMProvider
    
    # Test is viable, continue
    TEST_VIABLE = True
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    TEST_VIABLE = False


class SimpleAsyncTest:
    """Simple async test helper for running async tests."""
    
    @staticmethod
    def run_async(coro):
        """Run an async coroutine in the event loop."""
        return asyncio.run(coro)


class MockReport:
    """Mock Report class if the real one can't be imported."""
    
    def __init__(self, id=1, title="Test"):
        self.id = id
        self.title = title
        self.metadata = {}


class I18nAIIntegrationTest:
    """Basic integration tests for i18n AI services."""
    
    def setup(self):
        """Set up test fixtures."""
        print("Setting up test fixtures...")
        
        # Create mock fallback manager
        self.mock_fallback_manager = MagicMock(spec=FallbackManager)
        
        # Set up the execute_with_fallback method as an AsyncMock
        self.mock_fallback_manager.execute_with_fallback = AsyncMock()
        self.mock_fallback_manager.execute_with_fallback.return_value = (
            {
                "reasoning": "This is the reasoning step",
                "result": {"key": "value"},
                "confidence_score": 0.8
            },
            LLMProvider.OPENAI
        )
        
        # Create i18n framework with mocked methods
        self.i18n_framework = I18nFramework()
        
        # Mock the translation methods
        self.i18n_framework.translate = AsyncMock()
        self.i18n_framework.translate.return_value = "Translated text"
        
        self.i18n_framework.detect_language = AsyncMock()
        self.i18n_framework.detect_language.return_value = SupportedLanguage.JAPANESE
        
        self.i18n_framework.format_ai_prompt = AsyncMock()
        self.i18n_framework.format_ai_prompt.return_value = "Formatted prompt in Japanese"
        
        # Create the service to test
        self.i18n_llm_service = self.i18n_framework.create_i18n_ai_service(self.mock_fallback_manager)
        
        # Create a report
        try:
            self.report = Report(id=1, title="Test Report")
        except:
            self.report = MockReport(id=1, title="Test Report")
            
        print("Setup complete.")
        
    async def test_i18n_prompt_translation(self):
        """Test that prompts are properly translated before being sent to the LLM."""
        print("\nRunning test_i18n_prompt_translation...")
        
        # Given a prompt template and variables
        prompt_vars = {"company_name": "Acme Corp", "industry": "Technology"}
        
        # When we execute the prompt with Japanese as target language
        result, confidence = await self.i18n_llm_service.execute_multilingual_prompt(
            template_id="competitor_analysis",
            language=SupportedLanguage.JAPANESE,
            variables=prompt_vars,
            report=self.report
        )
        
        # Then the i18n framework should have been called to format the prompt
        assert self.i18n_framework.format_ai_prompt.called, "format_ai_prompt should have been called"
        
        # And the result should include the language
        assert result["language"] == "ja", f"Expected language 'ja', got '{result.get('language')}'"
        
        # And the confidence score should be from the mock
        assert confidence == 0.8, f"Expected confidence 0.8, got {confidence}"
        
        print("test_i18n_prompt_translation: PASSED")
        return True
    
    async def test_i18n_result_translation(self):
        """Test that results are properly translated after being received from the LLM."""
        print("\nRunning test_i18n_result_translation...")
        
        # Given an LLM result in English
        llm_result = {
            "reasoning": "The company shows strong growth in the technology sector.",
            "result": {
                "strengths": ["Innovative products", "Strong market position"],
                "weaknesses": ["Limited international presence"]
            },
            "confidence_score": 0.85,
            "language": "en"
        }
        
        # When we translate the result to French
        translated_result = await self.i18n_llm_service.translate_llm_result(
            result=llm_result,
            target_language=SupportedLanguage.FRENCH
        )
        
        # Then the result should be translated
        assert translated_result["language"] == "fr", f"Expected language 'fr', got '{translated_result.get('language')}'"
        assert translated_result["translated_from"] == "en", f"Expected translated_from 'en', got '{translated_result.get('translated_from')}'"
        
        # And at least one call to translate should have been made
        assert self.i18n_framework.translate.called, "translate should have been called"
        
        print("test_i18n_result_translation: PASSED")
        return True
    
    async def test_chain_of_thought_i18n(self):
        """Test that chain-of-thought reasoning works with different languages."""
        print("\nRunning test_chain_of_thought_i18n...")
        
        # When we execute a chain of thought in Japanese
        result, confidence = await self.i18n_llm_service.execute_with_language(
            prompt="競合他社の分析を行う",  # "Perform competitor analysis" in Japanese
            report=self.report,
            language=SupportedLanguage.JAPANESE
        )
        
        # Then the language detection should be skipped (since we provided it)
        assert not self.i18n_framework.detect_language.called, "detect_language should not have been called"
        
        # And the prompt should be translated to English for the LLM
        assert self.i18n_framework.translate.called, "translate should have been called"
        
        # And the result should include the language
        assert result["language"] == "ja", f"Expected language 'ja', got '{result.get('language')}'"
        
        print("test_chain_of_thought_i18n: PASSED")
        return True
    
    async def run_all_tests(self):
        """Run all tests and return results."""
        self.setup()
        
        results = {
            "test_i18n_prompt_translation": await self.test_i18n_prompt_translation(),
            "test_i18n_result_translation": await self.test_i18n_result_translation(),
            "test_chain_of_thought_i18n": await self.test_chain_of_thought_i18n()
        }
        
        all_passed = all(results.values())
        
        if all_passed:
            print("\n✅ All tests PASSED!")
        else:
            print("\n❌ Some tests FAILED!")
            for test_name, passed in results.items():
                status = "PASSED" if passed else "FAILED"
                print(f"  - {test_name}: {status}")
        
        return all_passed


if __name__ == "__main__":
    if not TEST_VIABLE:
        print("Tests cannot be run due to missing dependencies")
        sys.exit(1)
        
    try:
        print(f"Starting I18nAIIntegration tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        test_suite = I18nAIIntegrationTest()
        success = SimpleAsyncTest.run_async(test_suite.run_all_tests())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)
