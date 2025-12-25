#!/usr/bin/env python
"""
Simple test runner for i18n AI integration tests.

This script provides a minimal test environment to verify that
the I18nAwareChainOfThought implementation passes all tests.

Following Semantic Seed coding standards with proper error handling.
"""
import os
import sys
import asyncio
import inspect
from enum import Enum
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

# Add the project root to sys.path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import required classes
from src.services.i18n.language_service import SupportedLanguage
from src.models.llm_fallback import LLMProvider
from src.models.report import Report


class MinimalTestRunner:
    """A minimal test runner for I18nAwareChainOfThought tests."""
    
    def __init__(self):
        """Initialize the test runner."""
        self.results = {
            "tests": [],
            "passed": 0,
            "failed": 0,
            "errors": 0
        }
    
    def find_test_methods(self, test_class):
        """Find all test methods in a test class."""
        return [
            method_name for method_name, method in inspect.getmembers(
                test_class, predicate=inspect.ismethod
            ) if method_name.startswith("test_")
        ]
    
    async def run_test(self, test_instance, test_method_name):
        """Run a single test method."""
        test_method = getattr(test_instance, test_method_name)
        
        # Print test info
        print(f"\nRunning test: {test_method_name}")
        print("-" * 60)
        
        # Setup test fixtures if needed
        if hasattr(test_instance, "setUp"):
            await test_instance.setUp()
        
        try:
            # Run the test
            await test_method()
            result = {"name": test_method_name, "status": "PASSED"}
            self.results["passed"] += 1
            print(f"✅ TEST PASSED: {test_method_name}")
        except AssertionError as e:
            result = {"name": test_method_name, "status": "FAILED", "error": str(e)}
            self.results["failed"] += 1
            print(f"❌ TEST FAILED: {test_method_name}")
            print(f"   Error: {str(e)}")
        except Exception as e:
            result = {"name": test_method_name, "status": "ERROR", "error": str(e)}
            self.results["errors"] += 1
            print(f"⚠️ TEST ERROR: {test_method_name}")
            print(f"   Exception: {str(e)}")
        
        # Teardown test fixtures if needed
        if hasattr(test_instance, "tearDown"):
            await test_instance.tearDown()
        
        self.results["tests"].append(result)
        return result
    
    async def run_tests(self, test_class):
        """Run all tests in a test class."""
        # Create test class instance
        test_instance = test_class()
        
        # Find test methods
        test_methods = self.find_test_methods(test_instance)
        
        # Run each test
        for test_method_name in test_methods:
            await self.run_test(test_instance, test_method_name)
        
        # Print summary
        print("\nTest Summary:")
        print("-" * 60)
        print(f"Total tests: {len(self.results['tests'])}")
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        print(f"Errors: {self.results['errors']}")
        
        return self.results["failed"] == 0 and self.results["errors"] == 0


# Create mock classes to avoid dependencies
class MockAsyncMock:
    """A simple async mock for testing."""
    
    def __init__(self, return_value=None):
        """Initialize the mock with a return value."""
        self.return_value = return_value
        self.calls = []
        self.called = False
    
    async def __call__(self, *args, **kwargs):
        """Record the call and return the mocked value."""
        self.calls.append((args, kwargs))
        self.called = True
        return self.return_value
    
    def assert_called(self):
        """Assert that the mock was called."""
        assert self.called, "Expected the mock to be called"
    
    def assert_called_once_with(self, *args, **kwargs):
        """Assert that the mock was called once with specific args."""
        assert len(self.calls) == 1, f"Expected 1 call, got {len(self.calls)}"
        call_args, call_kwargs = self.calls[0]
        
        # Check positional args
        assert len(call_args) == len(args), f"Expected {len(args)} args, got {len(call_args)}"
        for i, (expected, actual) in enumerate(zip(args, call_args)):
            assert expected == actual, f"Arg {i} doesn't match: expected {expected}, got {actual}"
        
        # Check keyword args
        for key, expected in kwargs.items():
            assert key in call_kwargs, f"Expected '{key}' in kwargs"
            actual = call_kwargs[key]
            assert expected == actual, f"Kwarg '{key}' doesn't match: expected {expected}, got {actual}"
    
    def assert_not_called(self):
        """Assert that the mock was not called."""
        assert not self.called, "Expected the mock not to be called"


class MockI18nFramework:
    """Mock I18n framework for testing."""
    
    def __init__(self):
        """Initialize with mock methods."""
        self.translate = MockAsyncMock("Translated text")
        self.detect_language = MockAsyncMock(SupportedLanguage.JAPANESE)
        self.format_ai_prompt = MockAsyncMock("Formatted prompt in Japanese")
    
    def create_i18n_ai_service(self, llm_manager):
        """Create an I18nAwareChainOfThought instance."""
        from src.services.ai.i18n_chain_of_thought import I18nAwareChainOfThought
        return I18nAwareChainOfThought(
            llm_manager=llm_manager,
            i18n_framework=self,
            default_language=SupportedLanguage.ENGLISH
        )


class MockFallbackManager:
    """Mock LLM fallback manager for testing."""
    
    def __init__(self):
        """Initialize with mock execute_with_fallback method."""
        self.execute_with_fallback = MockAsyncMock((
            {
                "reasoning": "This is the reasoning step",
                "result": {"key": "value"},
                "confidence_score": 0.8
            },
            LLMProvider.OPENAI
        ))


class TestI18nAIIntegration:
    """Test suite for integrating i18n with AI services."""
    
    async def setUp(self):
        """Set up test fixtures."""
        self.mock_fallback_manager = MockFallbackManager()
        self.i18n_framework = MockI18nFramework()
        self.i18n_llm_service = self.i18n_framework.create_i18n_ai_service(self.mock_fallback_manager)
    
    async def test_i18n_prompt_translation(self):
        """Test that prompts are properly translated before being sent to the LLM."""
        # Given a report
        report = Report(id=1, title="Test Report")
        
        # And a prompt template
        prompt_vars = {"company_name": "Acme Corp", "industry": "Technology"}
        
        # When we execute the prompt with Japanese as target language
        result, confidence = await self.i18n_llm_service.execute_multilingual_prompt(
            template_id="competitor_analysis",
            language=SupportedLanguage.JAPANESE,
            variables=prompt_vars,
            report=report
        )
        
        # Then the i18n framework should have been called to format the prompt
        self.i18n_framework.format_ai_prompt.assert_called_once_with(
            "competitor_analysis", 
            SupportedLanguage.JAPANESE,
            prompt_vars
        )
        
        # And the result should include the language
        assert result["language"] == "ja"
        
        # And the confidence score should be from the mock
        assert confidence == 0.8
    
    async def test_i18n_result_translation(self):
        """Test that results are properly translated after being received from the LLM."""
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
        assert translated_result["language"] == "fr"
        assert translated_result["translated_from"] == "en"
        
        # And at least one call to translate should have been made
        self.i18n_framework.translate.assert_called()
    
    async def test_chain_of_thought_i18n(self):
        """Test that chain-of-thought reasoning works with different languages."""
        # Given a report
        report = Report(id=1, title="Test Report")
        
        # When we execute a chain of thought in Japanese
        result, confidence = await self.i18n_llm_service.execute_with_language(
            prompt="競合他社の分析を行う",  # "Perform competitor analysis" in Japanese
            report=report,
            language=SupportedLanguage.JAPANESE
        )
        
        # Then the language detection should be skipped (since we provided it)
        self.i18n_framework.detect_language.assert_not_called()
        
        # And the prompt should be translated to English for the LLM
        self.i18n_framework.translate.assert_called()
        
        # And the result should include the language
        assert result["language"] == "ja"


async def main():
    """Run the tests."""
    print(f"Starting I18nAwareChainOfThought tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    runner = MinimalTestRunner()
    success = await runner.run_tests(TestI18nAIIntegration)
    
    if success:
        print("\n✅ ALL TESTS PASSED! The i18n AI integration is working correctly.")
    else:
        print("\n❌ SOME TESTS FAILED! Please fix the issues before proceeding.")
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except ImportError as e:
        print(f"Error: {e}")
        print("Please ensure all required modules are available.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
