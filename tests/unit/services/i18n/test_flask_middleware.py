"""Unit tests for the Flask i18n Middleware.

This module tests the Flask middleware for language detection
and API response translation capabilities.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify, g, request

from src.services.i18n.flask_middleware import I18nMiddleware, i18n_response
from src.services.i18n.language_service import SupportedLanguage, LanguageService


@pytest.fixture
def app():
    """Create a test Flask application."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Create a mock language service
    mock_service = MagicMock(spec=LanguageService)
    
    # Configure translate method to add language prefix
    async def mock_translate(text, source_lang=None, target_lang=None):
        lang_code = target_lang.value if target_lang else "en"
        return f"[{lang_code}] {text}"
        
    mock_service.translate = mock_translate
    
    # Initialize the middleware with the mock service
    middleware = I18nMiddleware(app)
    middleware.language_service = mock_service
    
    # Create test routes
    @app.route('/test-plain')
    def test_plain():
        return "Hello World"
        
    @app.route('/test-json')
    def test_json():
        return jsonify({"message": "Hello World", "status": "success"})
        
    @app.route('/test-nested')
    def test_nested():
        return jsonify({
            "message": "Hello World",
            "details": {
                "greeting": "Welcome to OnSide",
                "items": ["Item 1", "Item 2"]
            }
        })
        
    @app.route('/test-i18n')
    @i18n_response
    def test_i18n():
        return jsonify({
            "message": "This should be translated",
            "count": 42,
            "details": {
                "note": "This nested text should also be translated"
            }
        })
    
    return app


class TestI18nMiddleware:
    """Test suite for the I18nMiddleware class."""
    
    def test_language_detection_default(self, app):
        """Test default language when no preference is specified."""
        # Given a request with no language header
        with app.test_request_context('/'):
            # When the middleware processes the request
            app.preprocess_request()
            
            # Then the default language should be set
            assert hasattr(g, 'language')
            assert g.language == SupportedLanguage.ENGLISH
    
    def test_language_detection_from_header(self, app):
        """Test language detection from Accept-Language header."""
        # Given a request with French language preference
        headers = {'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'}
        with app.test_request_context('/', headers=headers):
            # When the middleware processes the request
            app.preprocess_request()
            
            # Then French should be detected
            assert g.language == SupportedLanguage.FRENCH
    
    def test_language_detection_from_query(self, app):
        """Test language detection from query parameter."""
        # Given a request with Japanese language in query parameter
        with app.test_request_context('/?lang=ja'):
            # When the middleware processes the request
            app.preprocess_request()
            
            # Then Japanese should be detected
            assert g.language == SupportedLanguage.JAPANESE
    
    def test_language_detection_query_overrides_header(self, app):
        """Test that query parameter overrides header preference."""
        # Given a request with French header but Japanese query parameter
        headers = {'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'}
        with app.test_request_context('/?lang=ja', headers=headers):
            # When the middleware processes the request
            app.preprocess_request()
            
            # Then Japanese should be detected (query param priority)
            assert g.language == SupportedLanguage.JAPANESE
    
    def test_language_detection_unsupported(self, app):
        """Test handling of unsupported languages."""
        # Given a request with an unsupported language
        headers = {'Accept-Language': 'de-DE,de;q=0.9'}
        with app.test_request_context('/', headers=headers):
            # When the middleware processes the request
            app.preprocess_request()
            
            # Then the default language should be used
            assert g.language == SupportedLanguage.ENGLISH


class TestI18nResponseDecorator:
    """Test suite for the i18n_response decorator."""
    
    def test_plain_text_response_not_modified(self, app):
        """Test that non-JSON responses are not modified."""
        # Given a request to a route returning plain text
        with app.test_client() as client:
            # When we make the request
            response = client.get('/test-plain')
            
            # Then the response should not be modified
            assert response.data.decode('utf-8') == "Hello World"
    
    def test_json_response_with_english(self, app):
        """Test that English responses are not translated."""
        # Given a request with English language preference
        with app.test_client() as client:
            # When we make the request
            response = client.get('/test-json')
            
            # Then the response should not be translated
            data = json.loads(response.data)
            assert data["message"] == "Hello World"
    
    @patch('flask.g')
    def test_i18n_response_with_translation(self, mock_g, app):
        """Test that responses are translated with the decorator."""
        # Given a request with French language preference
        mock_g.language = SupportedLanguage.FRENCH
        
        # Use a patched version of the language detection
        with patch('src.services.i18n.flask_middleware._translate_dict',
                  return_value={
                      "_original": "en",
                      "message": "[fr] This should be translated",
                      "count": 42,
                      "details": {
                          "note": "[fr] This nested text should also be translated"
                      }
                  }):
            with app.test_client() as client:
                # When we make the request with the decorator
                response = client.get('/test-i18n')
                
                # Then the response should be translated
                data = json.loads(response.data)
                assert data["_original"] == "en"
                assert data["message"] == "[fr] This should be translated"
                assert data["count"] == 42
                assert data["details"]["note"] == "[fr] This nested text should also be translated"
    
    def test_translate_dict_function(self, app):
        """Test the _translate_dict function directly."""
        from src.services.i18n.flask_middleware import _translate_dict
        
        # Given a dictionary with various types of values
        test_data = {
            "string": "Hello World",
            "number": 42,
            "boolean": True,
            "null": None,
            "list": ["Item 1", "Item 2"],
            "nested": {
                "message": "Nested message",
                "count": 10
            }
        }
        
        # When we translate it using a mock language service
        mock_service = MagicMock()
        mock_service.translate = MagicMock(side_effect=lambda text, **kwargs: f"[fr] {text}")
        
        result = _translate_dict(mock_service, test_data, SupportedLanguage.FRENCH)
        
        # Then string values should be translated
        assert result["_original"] == "en"
        assert result["string"] == "[fr] Hello World"
        assert result["number"] == 42
        assert result["boolean"] is True
        assert result["null"] is None
        assert result["list"] == ["[fr] Item 1", "[fr] Item 2"]
        assert result["nested"]["message"] == "[fr] Nested message"
        assert result["nested"]["count"] == 10
