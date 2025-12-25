"""Integration tests for the OnSide Internationalization Framework.

This module tests the complete i18n integration with all components
working together, including language detection, translation, and middleware.
"""
import pytest
import asyncio
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify, request, g

from src.services.i18n.integration import I18nFramework
from src.services.i18n.language_service import SupportedLanguage, TranslationError


class TestI18nFrameworkIntegration:
    """Integration test suite for the I18nFramework class."""
    
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
    async def test_language_detection_integration(self, framework):
        """Test language detection integration."""
        # Test various text samples
        assert await framework.detect_language("Hello world") == SupportedLanguage.ENGLISH
        assert await framework.detect_language("Bonjour le monde") == SupportedLanguage.FRENCH
        assert await framework.detect_language("こんにちは世界") == SupportedLanguage.JAPANESE
    
    @pytest.mark.asyncio
    async def test_translation_integration(self, framework):
        """Test translation integration."""
        # Test translation to different languages
        assert await framework.translate("Hello", target_lang=SupportedLanguage.FRENCH) == "[fr] Hello"
        assert await framework.translate("Hello", target_lang=SupportedLanguage.JAPANESE) == "[ja] Hello"
        
        # Test translation with auto-detection
        assert await framework.translate("Bonjour", target_lang=SupportedLanguage.ENGLISH) == "[en] Bonjour"
    
    @pytest.mark.asyncio
    async def test_all_translations_integration(self, framework):
        """Test getting translations in all languages."""
        result = await framework.get_all_translations("Hello")
        assert "en" in result
        assert "fr" in result
        assert "ja" in result
    
    def test_ui_translation_integration(self, framework):
        """Test UI translation integration."""
        # Test basic UI translation
        assert framework.ui.translate("test.greeting") == "Hello"
        assert framework.ui.translate("test.greeting", SupportedLanguage.FRENCH) == "Bonjour"
        assert framework.ui.translate("test.greeting", SupportedLanguage.JAPANESE) == "こんにちは"
        
        # Test UI translation with variables
        assert framework.ui.translate("test.welcome", variables={"name": "User"}) == "Welcome, User!"
        assert framework.ui.translate(
            "test.welcome", SupportedLanguage.FRENCH, variables={"name": "User"}
        ) == "Bienvenue, User!"
    
    @pytest.mark.asyncio
    async def test_language_specific_translator(self, framework):
        """Test the language-specific translator."""
        # Create language-specific translators
        fr_translator = framework.get_translator_for_language(SupportedLanguage.FRENCH)
        ja_translator = framework.get_translator_for_language(SupportedLanguage.JAPANESE)
        
        # Test UI translation with language-specific translator
        assert fr_translator.ui("test.greeting") == "Bonjour"
        assert ja_translator.ui("test.greeting") == "こんにちは"
        
        # Test text translation with language-specific translator
        assert await fr_translator.translate("Hello") == "[fr] Hello"
        assert await ja_translator.translate("Hello") == "[ja] Hello"
    
    @pytest.mark.asyncio
    async def test_prompt_translation_integration(self, framework):
        """Test AI prompt translation and formatting."""
        # Register a test prompt template
        framework.prompts.register_template(
            "test_prompt",
            {
                "en": "Analyze the company {company_name}",
                "fr": "Analysez l'entreprise {company_name}",
                "ja": "企業{company_name}を分析する"
            }
        )
        
        # Test prompt formatting in different languages
        en_prompt = await framework.format_ai_prompt(
            "test_prompt",
            SupportedLanguage.ENGLISH,
            {"company_name": "Acme Corp"}
        )
        assert en_prompt == "Analyze the company [en] Acme Corp"
        
        fr_prompt = await framework.format_ai_prompt(
            "test_prompt",
            SupportedLanguage.FRENCH,
            {"company_name": "Acme Corp"}
        )
        assert fr_prompt == "Analysez l'entreprise [fr] Acme Corp"


class TestFlaskIntegration:
    """Test suite for Flask integration with the i18n framework."""
    
    @pytest.fixture
    def app(self, framework):
        """Create a Flask app with i18n integration."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # Initialize with i18n
        framework.init_flask(app)
        
        # Register test routes
        @app.route('/test')
        def test_route():
            return jsonify({
                "message": "Welcome to OnSide",
                "status": "success"
            })
        
        @app.route('/test-i18n')
        @app.i18n_middleware.i18n_response
        def test_i18n_route():
            return jsonify({
                "greeting": "Hello",
                "message": "Welcome to OnSide",
                "data": {
                    "items": ["Item 1", "Item 2"],
                    "count": 2
                }
            })
        
        @app.route('/current-language')
        def current_language():
            return jsonify({
                "language": g.language.value
            })
        
        @app.route('/translate/<text>')
        async def translate_text(text):
            translation = await app.i18n.translate(
                text,
                target_lang=g.language
            )
            return jsonify({
                "original": text,
                "translated": translation
            })
        
        return app
    
    def test_language_detection_middleware(self, app):
        """Test language detection from HTTP headers."""
        # Test default language (English)
        with app.test_client() as client:
            response = client.get('/current-language')
            assert response.json["language"] == "en"
        
        # Test French from Accept-Language header
        with app.test_client() as client:
            headers = {'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'}
            response = client.get('/current-language', headers=headers)
            assert response.json["language"] == "fr"
        
        # Test language from query parameter
        with app.test_client() as client:
            response = client.get('/current-language?lang=ja')
            assert response.json["language"] == "ja"
    
    @patch('src.services.i18n.flask_middleware._translate_dict')
    def test_i18n_response_decorator(self, mock_translate_dict, app):
        """Test the i18n_response decorator for translating responses."""
        # Set up mock translation
        mock_translate_dict.return_value = {
            "_original": "en",
            "greeting": "[fr] Hello",
            "message": "[fr] Welcome to OnSide",
            "data": {
                "items": ["[fr] Item 1", "[fr] Item 2"],
                "count": 2
            }
        }
        
        # Make request with French language
        with app.test_client() as client:
            headers = {'Accept-Language': 'fr-FR,fr;q=0.9'}
            response = client.get('/test-i18n', headers=headers)
            
            # Check that translation was applied
            data = response.json
            assert data["_original"] == "en"
            assert data["greeting"] == "[fr] Hello"
            assert data["message"] == "[fr] Welcome to OnSide"
            assert data["data"]["items"][0] == "[fr] Item 1"
            
    @pytest.mark.asyncio
    async def test_translation_with_flask(self, app):
        """Test translation within a Flask route."""
        # Mock the route handling to make it synchronous for testing
        with patch('src.services.i18n.integration.I18nFramework.translate', 
                  return_value="[fr] Hello"):
            # Make request with French language
            with app.test_client() as client:
                headers = {'Accept-Language': 'fr-FR,fr;q=0.9'}
                response = client.get('/translate/Hello', headers=headers)
                
                # Check the translation
                data = response.json
                assert data["original"] == "Hello"
                assert data["translated"] == "[fr] Hello"
