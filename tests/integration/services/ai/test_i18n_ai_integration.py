"""Integration tests for internationalized AI services.

This module tests the integration between the i18n framework and the AI services
using LLMWithChainOfThought for multilingual AI capabilities.
"""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from src.services.i18n.integration import I18nFramework
from src.services.i18n.language_service import SupportedLanguage
from src.services.ai.i18n_chain_of_thought import I18nAwareChainOfThought
from src.services.llm_provider.fallback_manager import FallbackManager
from src.models.report import Report
from src.models.llm_fallback import LLMProvider


class TestI18nAIIntegration:
    """Test suite for integrating i18n with AI services."""
    
    @pytest.fixture
    def mock_fallback_manager(self):
        """Create a mock LLM fallback manager."""
        mock_manager = MagicMock(spec=FallbackManager)
        
        # Set up the execute_with_fallback method as an AsyncMock
        mock_manager.execute_with_fallback = AsyncMock()
        mock_manager.execute_with_fallback.return_value = (
            {
                "reasoning": "This is the reasoning step",
                "result": {"key": "value"},
                "confidence_score": 0.8
            },
            LLMProvider.OPENAI
        )
        
        return mock_manager
    
    @pytest.fixture
    def i18n_framework(self):
        """Create an i18n framework instance."""
        framework = I18nFramework()
        
        # Mock the translation methods so we don't need to make actual API calls
        framework.translate = AsyncMock()
        framework.translate.return_value = "Translated text"
        
        framework.detect_language = AsyncMock()
        framework.detect_language.return_value = SupportedLanguage.JAPANESE
        
        framework.format_ai_prompt = AsyncMock()
        framework.format_ai_prompt.return_value = "Formatted prompt in Japanese"
        
        return framework
    
    @pytest.fixture
    def i18n_llm_service(self, mock_fallback_manager, i18n_framework):
        """Create an internationalized LLM service."""
        return i18n_framework.create_i18n_ai_service(mock_fallback_manager)
    
    @pytest.mark.asyncio
    async def test_i18n_prompt_translation(self, i18n_llm_service, i18n_framework):
        """Test that prompts are properly translated before being sent to the LLM."""
        # Given a report
        report = Report(id=1, title="Test Report")
        
        # And a prompt template
        prompt_vars = {"company_name": "Acme Corp", "industry": "Technology"}
        
        # When we execute the prompt with Japanese as target language
        result, confidence = await i18n_llm_service.execute_multilingual_prompt(
            template_id="competitor_analysis",
            language=SupportedLanguage.JAPANESE,
            variables=prompt_vars,
            report=report
        )
        
        # Then the i18n framework should have been called to format the prompt
        i18n_framework.format_ai_prompt.assert_called_once_with(
            "competitor_analysis", 
            SupportedLanguage.JAPANESE,
            prompt_vars
        )
        
        # And the result should include the language
        assert result["language"] == "ja"
        
        # And the confidence score should be from the mock
        assert confidence == 0.8
    
    @pytest.mark.asyncio
    async def test_i18n_result_translation(self, i18n_llm_service, i18n_framework):
        """Test that results are properly translated after being received from the LLM."""
        # Given a report
        report = Report(id=1, title="Test Report")
        
        # And an LLM result in English
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
        translated_result = await i18n_llm_service.translate_llm_result(
            result=llm_result,
            target_language=SupportedLanguage.FRENCH
        )
        
        # Then the result should be translated
        assert translated_result["language"] == "fr"
        assert translated_result["translated_from"] == "en"
        
        # And at least one call to translate should have been made
        i18n_framework.translate.assert_called()
    
    @pytest.mark.asyncio
    async def test_chain_of_thought_i18n(self, i18n_llm_service, mock_fallback_manager, i18n_framework):
        """Test that chain-of-thought reasoning works with different languages."""
        # Given a report
        report = Report(id=1, title="Test Report")
        
        # When we execute a chain of thought in Japanese
        result, confidence = await i18n_llm_service.execute_with_language(
            prompt="競合他社の分析を行う",  # "Perform competitor analysis" in Japanese
            report=report,
            language=SupportedLanguage.JAPANESE
        )
        
        # Then the language detection should be skipped (since we provided it)
        i18n_framework.detect_language.assert_not_called()
        
        # And the prompt should be translated to English for the LLM
        i18n_framework.translate.assert_called()
        
        # And the result should include the language
        assert result["language"] == "ja"
