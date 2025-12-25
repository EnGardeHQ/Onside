#!/usr/bin/env python
"""
Isolated test for I18nAwareChainOfThought implementation.

This test creates mock versions of all dependencies to verify the
implementation of I18nAwareChainOfThought without external dependencies.

Following Semantic Seed coding standards with proper error handling.
"""
import os
import sys
import asyncio
from enum import Enum
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


# Mock classes to replace external dependencies
class SupportedLanguage(str, Enum):
    """Mock of supported languages."""
    ENGLISH = "en"
    FRENCH = "fr"
    JAPANESE = "ja"


class LLMProvider(str, Enum):
    """Mock of LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"


class TranslationError(Exception):
    """Mock of translation error."""
    pass


class MockReport:
    """Mock report class."""
    
    def __init__(self, id=1, title="Test Report"):
        """Initialize with basic properties."""
        self.id = id
        self.title = title
        self.metadata = {}
        self.chain_of_thought = None


# Mock the base LLMWithChainOfThought class
class MockLLMWithChainOfThought:
    """Mock of the base LLMWithChainOfThought class."""
    
    def __init__(self, llm_manager):
        """Initialize with an LLM manager."""
        self.llm_manager = llm_manager
        self.reasoning_steps = []
    
    def _add_reasoning_step(self, step_name, step_content):
        """Add a reasoning step."""
        self.reasoning_steps.append((step_name, step_content))
    
    async def _execute_llm_with_reasoning(self, prompt, report, **kwargs):
        """Mock execution with reasoning."""
        # Just call the execute_with_fallback method
        result, provider = await self.llm_manager.execute_with_fallback(prompt, report, **kwargs)
        return result, result.get("confidence_score", 0.5)


# Mock of fallback manager
class MockFallbackManager:
    """Mock LLM fallback manager."""
    
    async def execute_with_fallback(self, prompt, report, **kwargs):
        """Mock execution with fallback."""
        result = {
            "reasoning": "This is mock reasoning",
            "result": {"key": "value"},
            "confidence_score": 0.9
        }
        return result, LLMProvider.OPENAI


# Mock of I18n framework
class MockI18nFramework:
    """Mock I18n framework."""
    
    async def translate(self, text, source_lang=None, target_lang=None):
        """Mock translation."""
        if target_lang == SupportedLanguage.FRENCH:
            return f"[fr] {text}"
        elif target_lang == SupportedLanguage.JAPANESE:
            return f"[ja] {text}"
        return text
    
    async def detect_language(self, text):
        """Mock language detection."""
        if "[fr]" in text.lower():
            return SupportedLanguage.FRENCH
        elif "[ja]" in text.lower():
            return SupportedLanguage.JAPANESE
        return SupportedLanguage.ENGLISH
    
    async def format_ai_prompt(self, template_id, language, variables):
        """Mock prompt formatting."""
        vars_str = ", ".join([f"{k}={v}" for k, v in variables.items()])
        return f"[{language}] Template {template_id} with {vars_str}"


# Now implement the I18nAwareChainOfThought class
class I18nAwareChainOfThought(MockLLMWithChainOfThought):
    """
    Extension of LLMWithChainOfThought with internationalization support.
    
    This class implements Sprint 5 requirements for multilingual AI services,
    enabling chain-of-thought reasoning in all supported languages.
    """
    
    def __init__(
        self,
        llm_manager,
        i18n_framework,
        default_language=SupportedLanguage.ENGLISH
    ):
        """Initialize the internationalized chain of thought service."""
        super().__init__(llm_manager)
        self.i18n_framework = i18n_framework
        self.default_language = default_language
    
    async def execute_multilingual_prompt(
        self,
        template_id,
        language,
        variables,
        report,
        with_chain_of_thought=True,
        confidence_threshold=None,
        **kwargs
    ):
        """
        Execute an AI prompt using a template in the specified language.
        """
        try:
            self._add_reasoning_step(
                "Language selection",
                f"Using specified language: {language}"
            )
            
            # Format the prompt in the target language
            prompt = await self.i18n_framework.format_ai_prompt(
                template_id, language, variables
            )
            
            self._add_reasoning_step(
                "Prompt preparation",
                f"Prepared prompt in {language}"
            )
            
            # Execute the prompt using the base class method
            result, confidence = await self._execute_llm_with_reasoning(
                prompt=prompt,
                report=report,
                with_chain_of_thought=with_chain_of_thought,
                confidence_threshold=confidence_threshold,
                **kwargs
            )
            
            # Store the language in the result
            result["language"] = language
            
            # Add user-friendly information for reporting
            language_names = {
                SupportedLanguage.ENGLISH: "English",
                SupportedLanguage.FRENCH: "French",
                SupportedLanguage.JAPANESE: "Japanese"
            }
            report.metadata["language"] = language_names.get(language, language)
            report.metadata["internationalized"] = True
            
            return result, confidence
            
        except Exception as e:
            error_msg = f"Error executing multilingual prompt: {str(e)}"
            print(error_msg)
            self._add_reasoning_step("Error", error_msg)
            
            # Return empty result with low confidence
            return {"error": error_msg, "language": language}, 0.3
    
    async def translate_llm_result(
        self,
        result,
        target_language
    ):
        """
        Translate an LLM result to the target language.
        """
        if not result:
            return result
        
        try:    
            translated_result = result.copy()
            source_language = result.get("language", SupportedLanguage.ENGLISH)
            
            # Skip translation if already in target language
            if source_language == target_language:
                return result
                
            # Translate reasoning if present
            if "reasoning" in result and isinstance(result["reasoning"], str):
                translated_result["reasoning"] = await self.i18n_framework.translate(
                    result["reasoning"],
                    source_lang=source_language,
                    target_lang=target_language
                )
                
            # Translate result content recursively
            if "result" in result and isinstance(result["result"], dict):
                translated_result["result"] = await self._translate_dict_recursively(
                    result["result"],
                    source_language=source_language,
                    target_language=target_language
                )
                
            # Update language information
            translated_result["language"] = target_language
            translated_result["translated_from"] = source_language
                
            return translated_result
            
        except TranslationError as e:
            print(f"Translation error: {str(e)}")
            # Return original result with error metadata
            result["translation_error"] = str(e)
            return result
            
        except Exception as e:
            print(f"Unexpected error during result translation: {str(e)}")
            # Return original result with error metadata
            result["translation_error"] = f"Unexpected error: {str(e)}"
            return result
    
    async def _translate_dict_recursively(
        self,
        data,
        source_language,
        target_language
    ):
        """
        Recursively translate all string values in a dictionary.
        """
        result = {}
        
        # Skip translation if languages are the same
        if source_language == target_language:
            return data
        
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 2:
                # Translate string values
                try:
                    result[key] = await self.i18n_framework.translate(
                        value,
                        source_lang=source_language,
                        target_lang=target_language
                    )
                except TranslationError:
                    # Keep original text on translation error
                    result[key] = value
                    print(f"Failed to translate value for key '{key}'")
                    
            elif isinstance(value, dict):
                # Recursively translate nested dictionaries
                result[key] = await self._translate_dict_recursively(
                    value,
                    source_language=source_language,
                    target_language=target_language
                )
                
            elif isinstance(value, list):
                # Translate list items
                translated_list = []
                for item in value:
                    if isinstance(item, str) and len(item) > 2:
                        try:
                            translated_item = await self.i18n_framework.translate(
                                item,
                                source_lang=source_language,
                                target_lang=target_language
                            )
                            translated_list.append(translated_item)
                        except TranslationError:
                            # Keep original text on translation error
                            translated_list.append(item)
                            print(f"Failed to translate list item: {item[:50]}...")
                            
                    elif isinstance(item, dict):
                        translated_dict = await self._translate_dict_recursively(
                            item,
                            source_language=source_language,
                            target_language=target_language
                        )
                        translated_list.append(translated_dict)
                        
                    else:
                        # Keep non-string values as-is
                        translated_list.append(item)
                        
                result[key] = translated_list
                
            else:
                # Keep non-string values as-is
                result[key] = value
                
        return result
    
    async def execute_with_language(
        self,
        prompt,
        report,
        language=None,
        with_chain_of_thought=True,
        confidence_threshold=None,
        **kwargs
    ):
        """
        Execute an LLM call with the specified language.
        """
        try:
            # Detect language if not specified
            if language is None:
                language = await self.i18n_framework.detect_language(prompt)
                self._add_reasoning_step(
                    "Language detection",
                    f"Detected language: {language}"
                )
            else:
                self._add_reasoning_step(
                    "Language handling",
                    f"Using specified language: {language}"
                )
                
            # Record original language in report
            language_names = {
                SupportedLanguage.ENGLISH: "English",
                SupportedLanguage.FRENCH: "French",
                SupportedLanguage.JAPANESE: "Japanese"
            }
            report.metadata["original_language"] = language_names.get(language, language)
            report.metadata["internationalized"] = True
                
            # Translate prompt to English for LLM if not already in English
            llm_prompt = prompt
            if language != SupportedLanguage.ENGLISH:
                llm_prompt = await self.i18n_framework.translate(
                    prompt,
                    source_lang=language,
                    target_lang=SupportedLanguage.ENGLISH
                )
                self._add_reasoning_step(
                    "Prompt translation",
                    f"Translated prompt from {language} to English for LLM processing"
                )
                
            # Execute the prompt using the base class method
            result, confidence = await self._execute_llm_with_reasoning(
                prompt=llm_prompt,
                report=report,
                with_chain_of_thought=with_chain_of_thought,
                confidence_threshold=confidence_threshold,
                **kwargs
            )
            
            # Translate result back to original language if needed
            if language != SupportedLanguage.ENGLISH:
                result_before_translation = result.copy()
                result["language"] = SupportedLanguage.ENGLISH
                
                try:
                    result = await self.translate_llm_result(result, language)
                    self._add_reasoning_step(
                        "Result translation",
                        f"Translated result back to {language}"
                    )
                except Exception as e:
                    print(f"Failed to translate result: {str(e)}")
                    # Restore original result with error info
                    result = result_before_translation
                    result["translation_error"] = str(e)
                
            # Ensure language is set in the result
            result["language"] = language
            
            return result, confidence
            
        except Exception as e:
            error_msg = f"Error in execute_with_language: {str(e)}"
            print(error_msg)
            self._add_reasoning_step("Error", error_msg)
            
            # Return empty result with low confidence
            return {"error": error_msg, "language": getattr(language, "value", "unknown")}, 0.3


# Test runner
class TestRunner:
    """Test runner for I18nAwareChainOfThought."""
    
    def __init__(self):
        """Initialize the test runner."""
        self.results = []
    
    async def run_test(self, test_func, description):
        """Run a single test function."""
        print(f"\nRunning test: {description}")
        print("-" * 60)
        
        try:
            await test_func()
            print(f"✅ PASSED: {description}")
            self.results.append({"description": description, "status": "PASSED"})
            return True
        except AssertionError as e:
            print(f"❌ FAILED: {description}")
            print(f"   Error: {str(e)}")
            self.results.append({"description": description, "status": "FAILED", "error": str(e)})
            return False
        except Exception as e:
            print(f"⚠️ ERROR: {description}")
            print(f"   Exception: {str(e)}")
            self.results.append({"description": description, "status": "ERROR", "error": str(e)})
            return False
    
    def print_summary(self):
        """Print a summary of test results."""
        print("\nTest Results:")
        print("-" * 60)
        
        for result in self.results:
            status = result["status"]
            description = result["description"]
            
            if status == "PASSED":
                print(f"✅ {description}")
            elif status == "FAILED":
                print(f"❌ {description} - {result.get('error', 'Unknown error')}")
            else:
                print(f"⚠️ {description} - {result.get('error', 'Unknown error')}")
        
        passed = sum(1 for r in self.results if r["status"] == "PASSED")
        total = len(self.results)
        
        print("\nSummary:")
        print(f"Passed: {passed}/{total} ({passed*100/total:.1f}%)")
        
        return passed == total


# Test functions
async def test_i18n_prompt_translation():
    """Test that prompts are properly translated before being sent to the LLM."""
    # Set up
    fallback_manager = MockFallbackManager()
    i18n_framework = MockI18nFramework()
    service = I18nAwareChainOfThought(fallback_manager, i18n_framework)
    report = MockReport()
    
    # Test execution
    result, confidence = await service.execute_multilingual_prompt(
        template_id="test_template",
        language=SupportedLanguage.JAPANESE,
        variables={"test": "value"},
        report=report
    )
    
    # Assertions
    assert result["language"] == SupportedLanguage.JAPANESE, f"Expected language ja, got {result['language']}"
    assert "internationalized" in report.metadata, "Report metadata should contain internationalized flag"
    assert report.metadata["language"] == "Japanese", f"Expected language name Japanese, got {report.metadata.get('language')}"


async def test_i18n_result_translation():
    """Test that results are properly translated after being received from the LLM."""
    # Set up
    fallback_manager = MockFallbackManager()
    i18n_framework = MockI18nFramework()
    service = I18nAwareChainOfThought(fallback_manager, i18n_framework)
    
    # Test data
    test_result = {
        "reasoning": "This is reasoning",
        "result": {
            "strengths": ["Good product", "Strong team"],
            "weaknesses": ["Limited funding"]
        },
        "confidence_score": 0.9,
        "language": SupportedLanguage.ENGLISH
    }
    
    # Test execution
    translated = await service.translate_llm_result(
        test_result,
        SupportedLanguage.FRENCH
    )
    
    # Assertions
    assert translated["language"] == SupportedLanguage.FRENCH, f"Expected language fr, got {translated['language']}"
    assert translated["translated_from"] == SupportedLanguage.ENGLISH, f"Expected translated_from en, got {translated.get('translated_from')}"
    assert translated["reasoning"].startswith("[fr]"), "Reasoning should be translated to French"


async def test_chain_of_thought_i18n():
    """Test that chain-of-thought reasoning works with different languages."""
    # Set up
    fallback_manager = MockFallbackManager()
    i18n_framework = MockI18nFramework()
    service = I18nAwareChainOfThought(fallback_manager, i18n_framework)
    report = MockReport()
    
    # Test execution with explicit language
    result, confidence = await service.execute_with_language(
        prompt="[ja] Analyze the competition",
        report=report,
        language=SupportedLanguage.JAPANESE
    )
    
    # Assertions
    assert result["language"] == SupportedLanguage.JAPANESE, f"Expected language ja, got {result['language']}"
    assert "original_language" in report.metadata, "Report metadata should contain original_language"
    assert report.metadata["original_language"] == "Japanese", f"Expected original language Japanese, got {report.metadata.get('original_language')}"


async def run_tests():
    """Run all tests."""
    runner = TestRunner()
    
    await runner.run_test(test_i18n_prompt_translation, "I18n prompt translation")
    await runner.run_test(test_i18n_result_translation, "I18n result translation")
    await runner.run_test(test_chain_of_thought_i18n, "Chain of thought with I18n")
    
    success = runner.print_summary()
    return success


if __name__ == "__main__":
    print(f"Starting isolated I18nAwareChainOfThought tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
