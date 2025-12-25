#!/usr/bin/env python
"""
Minimal test for I18nAwareChainOfThought implementation.

This is a standalone test that verifies the core functionality
of the internationalized AI services without external dependencies.
"""
import os
import sys
import json
import asyncio
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))


# ---------- Mock classes to avoid dependencies ----------
class SupportedLanguage(str, Enum):
    """Enum representing languages supported by the platform."""
    ENGLISH = "en"
    FRENCH = "fr"
    JAPANESE = "ja"


class LLMProvider(str, Enum):
    """Mock of LLM provider enum."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"


class Report:
    """Mock Report class."""
    def __init__(self, id=1, title="Test"):
        self.id = id
        self.title = title
        self.metadata = {}
        self.chain_of_thought = None


class MockTranslationService:
    """Mock translation service."""
    async def translate(self, text, source_lang=None, target_lang=None):
        """Mock translate method."""
        if target_lang == SupportedLanguage.FRENCH:
            return f"[FR] {text}"
        elif target_lang == SupportedLanguage.JAPANESE:
            return f"[JA] {text}"
        return text
        
    async def detect_language(self, text):
        """Mock language detection."""
        if text.startswith("[FR]"):
            return SupportedLanguage.FRENCH
        elif text.startswith("[JA]"):
            return SupportedLanguage.JAPANESE
        return SupportedLanguage.ENGLISH
        
    async def format_ai_prompt(self, template_id, language, variables):
        """Mock prompt formatting."""
        var_str = ", ".join([f"{k}={v}" for k, v in variables.items()])
        if language == SupportedLanguage.FRENCH:
            return f"[FR] Template {template_id} with {var_str}"
        elif language == SupportedLanguage.JAPANESE:
            return f"[JA] Template {template_id} with {var_str}"
        return f"Template {template_id} with {var_str}"


class MockI18nFramework:
    """Mock I18n framework."""
    def __init__(self):
        """Initialize the mock framework."""
        self.language_service = MockTranslationService()
        self.translate_calls = []
        self.detect_calls = []
        self.format_calls = []
        
    async def translate(self, text, source_lang=None, target_lang=None):
        """Mock translate method with tracking."""
        self.translate_calls.append((text, source_lang, target_lang))
        return await self.language_service.translate(text, source_lang, target_lang)
        
    async def detect_language(self, text):
        """Mock language detection with tracking."""
        self.detect_calls.append(text)
        return await self.language_service.detect_language(text)
        
    async def format_ai_prompt(self, template_id, language, variables):
        """Mock prompt formatting with tracking."""
        self.format_calls.append((template_id, language, variables))
        return await self.language_service.format_ai_prompt(template_id, language, variables)


class MockFallbackManager:
    """Mock LLM fallback manager."""
    async def execute_with_fallback(self, prompt, report, confidence_threshold=None, **kwargs):
        """Mock execute with fallback."""
        return {
            "reasoning": "This is mock reasoning",
            "result": {"key": "value"},
            "confidence_score": 0.9
        }, LLMProvider.OPENAI


# ---------- Test class ----------
class I18nAITester:
    """Test suite for I18nAwareChainOfThought."""
    
    def __init__(self):
        """Set up the test environment."""
        # Import the implementation to test
        from src.services.ai.i18n_chain_of_thought import I18nAwareChainOfThought
        
        # Create mocks
        self.i18n = MockI18nFramework()
        self.fallback_manager = MockFallbackManager()
        
        # Create the service to test
        self.service = I18nAwareChainOfThought(
            llm_manager=self.fallback_manager,
            i18n_framework=self.i18n,
            default_language=SupportedLanguage.ENGLISH
        )
        
        # Test results
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "failures": []
        }
        
    def assert_equal(self, actual, expected, message):
        """Assert that values are equal."""
        self.results["total"] += 1
        
        if actual == expected:
            self.results["passed"] += 1
            return True
        else:
            self.results["failed"] += 1
            failure = {
                "message": message,
                "expected": expected,
                "actual": actual
            }
            self.results["failures"].append(failure)
            print(f"❌ FAIL: {message}")
            print(f"   Expected: {expected}")
            print(f"   Actual:   {actual}")
            return False
            
    def assert_true(self, condition, message):
        """Assert that a condition is true."""
        self.results["total"] += 1
        
        if condition:
            self.results["passed"] += 1
            return True
        else:
            self.results["failed"] += 1
            failure = {
                "message": message,
                "expected": True,
                "actual": False
            }
            self.results["failures"].append(failure)
            print(f"❌ FAIL: {message}")
            return False
            
    async def test_execute_multilingual_prompt(self):
        """Test executing a multilingual prompt."""
        print("\n📝 Testing execute_multilingual_prompt...")
        
        # Create a report
        report = Report(id=123, title="Test Report")
        
        # Test with Japanese language
        result, confidence = await self.service.execute_multilingual_prompt(
            template_id="test_template",
            language=SupportedLanguage.JAPANESE,
            variables={"name": "Test", "value": 42},
            report=report
        )
        
        # Verify format_ai_prompt was called
        self.assert_true(
            len(self.i18n.format_calls) > 0,
            "format_ai_prompt should have been called"
        )
        
        # Verify the language in the result
        self.assert_equal(
            result.get("language"),
            "ja",
            "Result should contain Japanese language code"
        )
        
        # Verify metadata was added to the report
        self.assert_true(
            "language" in report.metadata,
            "Report metadata should contain language information"
        )
        
        print("✅ execute_multilingual_prompt test completed")
        
    async def test_translate_llm_result(self):
        """Test translating an LLM result."""
        print("\n📝 Testing translate_llm_result...")
        
        # Create a mock result
        mock_result = {
            "reasoning": "This product shows strong growth potential.",
            "result": {
                "strengths": ["Good market fit", "Strong team"],
                "weaknesses": ["Limited funding"]
            },
            "confidence_score": 0.85,
            "language": "en"
        }
        
        # Translate to French
        translated = await self.service.translate_llm_result(
            result=mock_result,
            target_language=SupportedLanguage.FRENCH
        )
        
        # Verify translate was called
        self.assert_true(
            len(self.i18n.translate_calls) > 0,
            "translate should have been called"
        )
        
        # Verify the language was updated
        self.assert_equal(
            translated.get("language"),
            "fr",
            "Result should contain French language code"
        )
        
        # Verify original language was recorded
        self.assert_equal(
            translated.get("translated_from"),
            "en",
            "Result should record the original language"
        )
        
        print("✅ translate_llm_result test completed")
        
    async def test_execute_with_language(self):
        """Test executing with a specific language."""
        print("\n📝 Testing execute_with_language...")
        
        # Create a report
        report = Report(id=123, title="Test Report")
        
        # Test with Japanese language
        result, confidence = await self.service.execute_with_language(
            prompt="[JA] Analyze the company performance",
            report=report,
            language=SupportedLanguage.JAPANESE
        )
        
        # Verify the language in the result
        self.assert_equal(
            result.get("language"),
            "ja",
            "Result should contain Japanese language code"
        )
        
        # Verify the report metadata was updated
        self.assert_true(
            "original_language" in report.metadata,
            "Report metadata should contain original language information"
        )
        
        # Test with auto-detection (should detect English)
        reset_service = lambda: self.i18n.detect_calls.clear()
        reset_service()
        
        result2, confidence2 = await self.service.execute_with_language(
            prompt="Analyze the company performance",
            report=report,
            language=None  # Auto-detect
        )
        
        # Verify detect_language was called
        self.assert_true(
            len(self.i18n.detect_calls) > 0,
            "detect_language should have been called for auto-detection"
        )
        
        print("✅ execute_with_language test completed")
        
    async def run_all_tests(self):
        """Run all tests."""
        print("\n🧪 Running I18nAwareChainOfThought tests...")
        
        await self.test_execute_multilingual_prompt()
        await self.test_translate_llm_result()
        await self.test_execute_with_language()
        
        print("\n📊 Test Results:")
        print(f"  Total:  {self.results['total']}")
        print(f"  Passed: {self.results['passed']}")
        print(f"  Failed: {self.results['failed']}")
        
        if self.results["failed"] == 0:
            print("\n✅ ALL TESTS PASSED!")
            return True
        else:
            print("\n❌ SOME TESTS FAILED!")
            return False


# ---------- Main function ----------
if __name__ == "__main__":
    print(f"Starting I18nAwareChainOfThought tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run the tests
        tester = I18nAITester()
        success = asyncio.run(tester.run_all_tests())
        
        # Exit with appropriate status code
        sys.exit(0 if success else 1)
    except ImportError as e:
        print(f"Error importing modules: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)
