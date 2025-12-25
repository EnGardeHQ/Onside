"""Unit tests for the Language Detection and Translation Service.

This module tests the language detection, translation capabilities,
and overall internationalization framework following BDD practices.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch

from src.services.i18n.language_service import (
    LanguageService,
    SupportedLanguage,
    TranslationError,
    LanguageDetectionError
)


class TestLanguageService:
    """Test suite for the LanguageService implementation.
    
    This follows BDD-style testing as specified in the Semantic Seed coding standards.
    """
    
    @pytest.fixture
    def language_service(self):
        """Create a language service instance for testing."""
        return LanguageService()
    
    @pytest.mark.asyncio
    async def test_detect_language_english(self, language_service):
        """Test that English text is correctly identified."""
        # Given an English text
        text = "This is a sample English text for testing language detection."
        
        # When we detect the language
        detected = await language_service.detect_language(text)
        
        # Then the detected language should be English
        assert detected == SupportedLanguage.ENGLISH
        
    @pytest.mark.asyncio
    async def test_detect_language_french(self, language_service):
        """Test that French text is correctly identified."""
        # Given a French text
        text = "Ceci est un exemple de texte français pour tester la détection de langue."
        
        # When we detect the language
        detected = await language_service.detect_language(text)
        
        # Then the detected language should be French
        assert detected == SupportedLanguage.FRENCH
        
    @pytest.mark.asyncio
    async def test_detect_language_japanese(self, language_service):
        """Test that Japanese text is correctly identified."""
        # Given a Japanese text
        text = "これは言語検出をテストするためのサンプル日本語テキストです。"
        
        # When we detect the language
        detected = await language_service.detect_language(text)
        
        # Then the detected language should be Japanese
        assert detected == SupportedLanguage.JAPANESE
        
    @pytest.mark.asyncio
    async def test_detect_language_unsupported(self, language_service):
        """Test that unsupported language detection falls back to English."""
        # Given a text in an unsupported language (German)
        text = "Dies ist ein deutscher Text, der nicht unterstützt wird."
        
        # When we detect the language
        detected = await language_service.detect_language(text)
        
        # Then the detected language should default to English
        assert detected == SupportedLanguage.ENGLISH
        
    @pytest.mark.asyncio
    async def test_language_detection_error_handling(self, language_service):
        """Test error handling in language detection."""
        # Given a mocked detection service that fails
        with patch.object(
            language_service, '_detect_language_internal', 
            side_effect=Exception("Detection service unavailable")
        ):
            # When we try to detect the language
            # Then it should raise a LanguageDetectionError
            with pytest.raises(LanguageDetectionError):
                await language_service.detect_language("Any text")
                
    @pytest.mark.asyncio
    async def test_translate_text_english_to_french(self, language_service):
        """Test translation from English to French."""
        # Given an English text and target language French
        text = "Hello, how are you?"
        source_lang = SupportedLanguage.ENGLISH
        target_lang = SupportedLanguage.FRENCH
        
        # When we translate the text
        translated = await language_service.translate(
            text, source_lang=source_lang, target_lang=target_lang
        )
        
        # Then we should get proper French translation
        assert translated == "Bonjour, comment allez-vous?"
        
    @pytest.mark.asyncio
    async def test_translate_text_english_to_japanese(self, language_service):
        """Test translation from English to Japanese."""
        # Given an English text and target language Japanese
        text = "Hello, how are you?"
        source_lang = SupportedLanguage.ENGLISH
        target_lang = SupportedLanguage.JAPANESE
        
        # When we translate the text
        translated = await language_service.translate(
            text, source_lang=source_lang, target_lang=target_lang
        )
        
        # Then we should get proper Japanese translation
        assert translated == "こんにちは、お元気ですか？"
        
    @pytest.mark.asyncio
    async def test_translation_caching(self, language_service):
        """Test that translations are properly cached."""
        # Given a text to translate
        text = "This is a test"
        source_lang = SupportedLanguage.ENGLISH
        target_lang = SupportedLanguage.FRENCH
        
        # When we translate the same text twice
        with patch.object(
            language_service, '_translate_internal', 
            wraps=language_service._translate_internal
        ) as mock_translate:
            await language_service.translate(text, source_lang=source_lang, target_lang=target_lang)
            await language_service.translate(text, source_lang=source_lang, target_lang=target_lang)
            
            # Then the internal translation function should be called only once
            assert mock_translate.call_count == 1
            
    @pytest.mark.asyncio
    async def test_translation_error_handling(self, language_service):
        """Test error handling in translation."""
        # Given a mocked translation service that fails
        with patch.object(
            language_service, '_translate_internal', 
            side_effect=Exception("Translation service unavailable")
        ):
            # When we try to translate text
            # Then it should raise a TranslationError
            with pytest.raises(TranslationError):
                await language_service.translate(
                    "Test text", 
                    source_lang=SupportedLanguage.ENGLISH, 
                    target_lang=SupportedLanguage.FRENCH
                )
                
    @pytest.mark.asyncio
    async def test_get_all_translations(self, language_service):
        """Test that we can get translations in all supported languages."""
        # Given a text to translate
        text = "Welcome to OnSide"
        
        # When we get all translations
        translations = await language_service.get_all_translations(text)
        
        # Then we should get translations for all supported languages
        assert len(translations) == len(SupportedLanguage) - 1  # Exclude the original language
        assert SupportedLanguage.ENGLISH.value in translations
        assert SupportedLanguage.FRENCH.value in translations
        assert SupportedLanguage.JAPANESE.value in translations
