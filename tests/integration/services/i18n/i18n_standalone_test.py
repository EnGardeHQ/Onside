"""Standalone integration tests for the OnSide Internationalization Framework.

This module tests the i18n features in isolation to avoid dependency issues
when running the full test suite.
"""
import asyncio
import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

from src.services.i18n.integration import I18nFramework
from src.services.i18n.language_service import SupportedLanguage, TranslationError

class TestI18nStandalone:
    """Standalone tests for the I18nFramework class."""
    
    @pytest.fixture
    def framework(self):
        """Create an I18nFramework instance for testing."""
        framework = I18nFramework()
        
        # Mock the core language service
        mock_language_service = MagicMock()
        
        # Configure async methods
        async def mock_detect_language(text):
            # Simple detection based on language-specific words
            if 'bonjour' in text.lower():
                return SupportedLanguage.FRENCH
            elif 'こんにちは' in text:
                return SupportedLanguage.JAPANESE
            return SupportedLanguage.ENGLISH
            
        async def mock_translate(text, source_lang=None, target_lang=None):
            if target_lang is None:
                target_lang = SupportedLanguage.ENGLISH
                
            # Simple translation that just adds a language prefix
            return f"[{target_lang.value}] {text}"
            
        async def mock_get_all_translations(text, source_lang=None):
            return {
                "en": f"[en] {text}",
                "fr": f"[fr] {text}",
                "ja": f"[ja] {text}"
            }
            
        # Assign mocked methods
        mock_language_service.detect_language = mock_detect_language
        mock_language_service.translate = mock_translate
        mock_language_service.get_all_translations = mock_get_all_translations
        
        framework.language_service = mock_language_service
        
        # Create temp translation files for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock translation files
            en_translations = {
                "test": {
                    "greeting": "Hello",
                    "welcome": "Welcome, {name}!"
                }
            }
            
            fr_translations = {
                "test": {
                    "greeting": "Bonjour",
                    "welcome": "Bienvenue, {name}!"
                }
            }
            
            ja_translations = {
                "test": {
                    "greeting": "こんにちは",
                    "welcome": "{name}さん、ようこそ!"
                }
            }
            
            # Write translation files
            with open(os.path.join(temp_dir, "en.json"), "w", encoding="utf-8") as f:
                json.dump(en_translations, f)
                
            with open(os.path.join(temp_dir, "fr.json"), "w", encoding="utf-8") as f:
                json.dump(fr_translations, f)
                
            with open(os.path.join(temp_dir, "ja.json"), "w", encoding="utf-8") as f:
                json.dump(ja_translations, f)
                
            # Initialize framework with temp directory
            framework.translation_loader = framework.translation_loader.__class__(temp_dir)
            framework.ui = framework.ui.__class__(framework.translation_loader)
        
        return framework
    
    @pytest.mark.asyncio
    async def test_language_detection(self, framework):
        """Test language detection integration."""
        # Test various text samples
        assert await framework.detect_language("Hello world") == SupportedLanguage.ENGLISH
        assert await framework.detect_language("Bonjour le monde") == SupportedLanguage.FRENCH
        assert await framework.detect_language("こんにちは世界") == SupportedLanguage.JAPANESE
    
    @pytest.mark.asyncio
    async def test_translation(self, framework):
        """Test translation integration."""
        # Test translations between languages
        assert await framework.translate("Hello world", target_lang=SupportedLanguage.FRENCH) == "[fr] Hello world"
        assert await framework.translate("Bonjour le monde", target_lang=SupportedLanguage.JAPANESE) == "[ja] Bonjour le monde"
        assert await framework.translate("こんにちは世界", target_lang=SupportedLanguage.ENGLISH) == "[en] こんにちは世界"

    @pytest.mark.asyncio
    async def test_all_translations(self, framework):
        """Test getting translations in all languages."""
        translations = await framework.get_all_translations("Hello world")
        assert translations["en"] == "[en] Hello world"
        assert translations["fr"] == "[fr] Hello world"
        assert translations["ja"] == "[ja] Hello world"

    def test_ui_translation(self, framework):
        """Test UI translation integration."""
        # Test basic UI translations
        assert framework.ui.translate("test.greeting", SupportedLanguage.ENGLISH) == "Hello"
        assert framework.ui.translate("test.greeting", SupportedLanguage.FRENCH) == "Bonjour"
        assert framework.ui.translate("test.greeting", SupportedLanguage.JAPANESE) == "こんにちは"
        
        # Test with variables
        assert framework.ui.translate("test.welcome", SupportedLanguage.ENGLISH, name="User") == "Welcome, User!"
        assert framework.ui.translate("test.welcome", SupportedLanguage.FRENCH, name="User") == "Bienvenue, User!"
        assert framework.ui.translate("test.welcome", SupportedLanguage.JAPANESE, name="User") == "Userさん、ようこそ!"

# For direct execution
if __name__ == "__main__":
    # Create a simple event loop and run the async tests
    test_instance = TestI18nStandalone()
    
    # Create framework instance directly without using the pytest fixture
    framework = I18nFramework()
    
    # Mock the core language service
    mock_language_service = MagicMock()
    
    # Configure async methods
    async def mock_detect_language(text):
        # Simple detection based on language-specific words
        if 'bonjour' in text.lower():
            return SupportedLanguage.FRENCH
        elif 'こんにちは' in text:
            return SupportedLanguage.JAPANESE
        return SupportedLanguage.ENGLISH
        
    async def mock_translate(text, source_lang=None, target_lang=None):
        if target_lang is None:
            target_lang = SupportedLanguage.ENGLISH
            
        # Simple translation that just adds a language prefix
        return f"[{target_lang.value}] {text}"
        
    async def mock_get_all_translations(text, source_lang=None):
        return {
            "en": f"[en] {text}",
            "fr": f"[fr] {text}",
            "ja": f"[ja] {text}"
        }
        
    # Assign mocked methods
    mock_language_service.detect_language = mock_detect_language
    mock_language_service.translate = mock_translate
    mock_language_service.get_all_translations = mock_get_all_translations
    
    framework.language_service = mock_language_service
    
    # Create temp translation files for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mock translation files
        en_translations = {
            "test": {
                "greeting": "Hello",
                "welcome": "Welcome, {name}!"
            }
        }
        
        fr_translations = {
            "test": {
                "greeting": "Bonjour",
                "welcome": "Bienvenue, {name}!"
            }
        }
        
        ja_translations = {
            "test": {
                "greeting": "こんにちは",
                "welcome": "{name}さん、ようこそ!"
            }
        }
        
        # Write translation files
        with open(os.path.join(temp_dir, "en.json"), "w", encoding="utf-8") as f:
            json.dump(en_translations, f)
            
        with open(os.path.join(temp_dir, "fr.json"), "w", encoding="utf-8") as f:
            json.dump(fr_translations, f)
            
        with open(os.path.join(temp_dir, "ja.json"), "w", encoding="utf-8") as f:
            json.dump(ja_translations, f)
            
        # Initialize framework with temp directory
        framework.translation_loader = framework.translation_loader.__class__(temp_dir)
        framework.ui = framework.ui.__class__(framework.translation_loader)
        
        try:
            # Run the actual tests
            async def run_tests():
                print("Running language detection test...")
                await test_instance.test_language_detection(framework)
                print("Running translation test...")
                await test_instance.test_translation(framework)
                print("Running all translations test...")
                await test_instance.test_all_translations(framework)
                
            asyncio.run(run_tests())
            print("Running UI translation test...")
            test_instance.test_ui_translation(framework)
            
            print("\n✅ All standalone i18n tests passed!")
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
