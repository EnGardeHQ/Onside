"""Unit tests for the Prompt Translator Service.

This module tests the prompt translation and internationalization capabilities
for AI interactions, following BDD practices.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch

from src.services.i18n.language_service import (
    LanguageService,
    SupportedLanguage,
    TranslationError
)
from src.services.i18n.prompt_translator import PromptTranslator, PromptTemplate


class TestPromptTemplate:
    """Test suite for the PromptTemplate class."""
    
    @pytest.fixture
    def template(self):
        """Create a sample prompt template for testing."""
        return PromptTemplate(
            "test_template",
            {
                "en": "Hello, {name}! Welcome to {service}.",
                "fr": "Bonjour, {name}! Bienvenue sur {service}.",
                "ja": "こんにちは、{name}さん！{service}へようこそ。"
            }
        )
    
    def test_get_template_english(self, template):
        """Test retrieving an English template."""
        # Given a template with multiple languages
        # When we request the English version
        result = template.get_template(SupportedLanguage.ENGLISH)
        
        # Then we should get the English template
        assert result == "Hello, {name}! Welcome to {service}."
        
    def test_get_template_french(self, template):
        """Test retrieving a French template."""
        # Given a template with multiple languages
        # When we request the French version
        result = template.get_template(SupportedLanguage.FRENCH)
        
        # Then we should get the French template
        assert result == "Bonjour, {name}! Bienvenue sur {service}."
        
    def test_get_template_japanese(self, template):
        """Test retrieving a Japanese template."""
        # Given a template with multiple languages
        # When we request the Japanese version
        result = template.get_template(SupportedLanguage.JAPANESE)
        
        # Then we should get the Japanese template
        assert result == "こんにちは、{name}さん！{service}へようこそ。"
        
    def test_get_template_fallback(self):
        """Test fallback to English when a language is missing."""
        # Given a template with only English and French
        template = PromptTemplate(
            "partial_template",
            {
                "en": "Hello, {name}!",
                "fr": "Bonjour, {name}!"
            }
        )
        
        # When we request the Japanese version (which doesn't exist)
        # Then it should fall back to English
        assert template.get_template(SupportedLanguage.JAPANESE) == "Hello, {name}!"
        
    def test_format_template(self, template):
        """Test formatting a template with variables."""
        # Given a template and variables
        variables = {"name": "John", "service": "OnSide"}
        
        # When we format the template
        result = template.format(SupportedLanguage.ENGLISH, **variables)
        
        # Then the variables should be substituted correctly
        assert result == "Hello, John! Welcome to OnSide."
        
    def test_format_template_missing_variable(self, template):
        """Test formatting with a missing variable."""
        # Given an incomplete set of variables
        variables = {"name": "John"}
        
        # When we format the template
        # Then it should include an error marker
        result = template.format(SupportedLanguage.ENGLISH, **variables)
        assert "ERROR" in result


class TestPromptTranslator:
    """Test suite for the PromptTranslator service."""
    
    @pytest.fixture
    def mock_language_service(self):
        """Create a mock language service."""
        mock_service = MagicMock(spec=LanguageService)
        
        # Set up translate method to echo input with language prefix
        async def mock_translate(text, source_lang=None, target_lang=None):
            lang_code = target_lang.value if target_lang else "en"
            return f"[{lang_code}] {text}"
            
        # Set up get_all_translations to return translations for all languages
        async def mock_get_all_translations(text, source_lang=None):
            if source_lang is None:
                source_lang = SupportedLanguage.ENGLISH
            
            return {
                "en": f"[en] {text}",
                "fr": f"[fr] {text}",
                "ja": f"[ja] {text}"
            }
            
        # Configure the mock
        mock_service.translate = mock_translate
        mock_service.get_all_translations = mock_get_all_translations
        
        return mock_service
    
    @pytest.fixture
    def translator(self, mock_language_service):
        """Create a prompt translator with a mock language service."""
        return PromptTranslator(language_service=mock_language_service)
    
    def test_register_template(self, translator):
        """Test registering a new template."""
        # Given a translator
        # When we register a new template
        translator.register_template(
            "test_template",
            {
                "en": "Test template {variable}",
                "fr": "Modèle de test {variable}",
                "ja": "テストテンプレート {variable}"
            }
        )
        
        # Then the template should be available
        template = translator.get_template("test_template")
        assert template.template_id == "test_template"
        assert "en" in template.templates
        assert "fr" in template.templates
        assert "ja" in template.templates
        
    def test_get_nonexistent_template(self, translator):
        """Test error handling when getting a non-existent template."""
        # Given a translator
        # When we try to get a non-existent template
        # Then it should raise a KeyError
        with pytest.raises(KeyError):
            translator.get_template("nonexistent_template")
    
    @pytest.mark.asyncio
    async def test_translate_prompt(self, translator):
        """Test translating a prompt with variables."""
        # Given a registered template
        translator.register_template(
            "test_prompt",
            {
                "en": "Analyze {company} in the {industry} sector.",
                "fr": "Analysez {company} dans le secteur {industry}.",
                "ja": "{industry}セクターの{company}を分析します。"
            }
        )
        
        # And variables to substitute
        variables = {
            "company": "Acme Corp",
            "industry": "Technology"
        }
        
        # When we translate the prompt to French
        result = await translator.translate_prompt(
            "test_prompt",
            SupportedLanguage.FRENCH,
            variables
        )
        
        # Then the result should be the French template with translated variables
        assert result == "Analysez [fr] Acme Corp dans le secteur [fr] Technology."
        
    @pytest.mark.asyncio
    async def test_translate_response(self, translator):
        """Test translating an AI response."""
        # Given an AI response in English
        response = "The company shows strong growth potential."
        
        # When we translate it to Japanese
        result = await translator.translate_response(
            response,
            source_lang=SupportedLanguage.ENGLISH,
            target_lang=SupportedLanguage.JAPANESE
        )
        
        # Then the result should be the translated response
        assert result == "[ja] The company shows strong growth potential."
        
    @pytest.mark.asyncio
    async def test_format_multilingual_response(self, translator):
        """Test generating responses in all supported languages."""
        # Given an AI response
        response = "Market analysis complete."
        
        # When we request all translations
        results = await translator.format_multilingual_response(
            response,
            source_lang=SupportedLanguage.ENGLISH
        )
        
        # Then we should get translations for all languages
        assert "en" in results
        assert "fr" in results
        assert "ja" in results
        assert results["en"] == "[en] Market analysis complete."
        assert results["fr"] == "[fr] Market analysis complete."
        assert results["ja"] == "[ja] Market analysis complete."
        
    @pytest.mark.asyncio
    async def test_built_in_templates(self, translator):
        """Test that built-in templates are properly loaded."""
        # Given a translator with built-in templates
        # When we check for specific template IDs
        competitor_template = translator.get_template("competitor_analysis")
        market_template = translator.get_template("market_analysis")
        audience_template = translator.get_template("audience_analysis")
        
        # Then they should exist and have appropriate content
        assert "en" in competitor_template.templates
        assert "fr" in market_template.templates
        assert "ja" in audience_template.templates
        
        # And the templates should contain expected content markers
        assert "company_name" in competitor_template.get_template(SupportedLanguage.ENGLISH)
        assert "industry" in market_template.get_template(SupportedLanguage.FRENCH)
        assert "company_name" in audience_template.get_template(SupportedLanguage.JAPANESE)
