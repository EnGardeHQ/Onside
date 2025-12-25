"""Flask middleware for internationalization support.

This module provides middleware components that integrate language detection
and translation capabilities into Flask API endpoints.
"""
import json
import logging
from functools import wraps
from typing import Dict, Any, Callable, Optional, Union

from flask import request, Response, g, current_app
import flask

from .language_service import LanguageService, SupportedLanguage, TranslationError

logger = logging.getLogger("i18n.middleware")


class I18nMiddleware:
    """Middleware for adding internationalization support to Flask applications.
    
    This middleware detects the user's preferred language from HTTP headers and
    provides utilities for translating API responses automatically.
    """
    
    def __init__(self, app=None, default_language: SupportedLanguage = SupportedLanguage.ENGLISH):
        """Initialize the middleware.
        
        Args:
            app: Flask application to initialize with
            default_language: Default language to use when preference can't be determined
        """
        self.default_language = default_language
        self.language_service = LanguageService()
        
        if app is not None:
            self.init_app(app)
            
    def init_app(self, app: flask.Flask) -> None:
        """Initialize a Flask application with i18n support.
        
        Args:
            app: Flask application to initialize
        """
        # Register a before_request handler to detect language
        app.before_request(self._detect_language)
        
        # Store middleware instance
        app.i18n_middleware = self
        
        # Register helper functions with the app
        app.translate = self.translate
        app.get_translations = self.get_translations
        
        # Provide method to get current language
        app.get_language = lambda: self._get_current_language()
        
        logger.info("Initialized i18n middleware for Flask app")
        
    def _detect_language(self) -> None:
        """Detect the user's preferred language from HTTP headers.
        
        This method runs before each request and sets g.language.
        """
        # Check the Accept-Language header
        accept_language = request.headers.get('Accept-Language', '')
        
        # Parse the Accept-Language header
        # Format example: 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'
        language_preference = None
        
        if accept_language:
            # Extract language codes and quality values
            parts = accept_language.split(',')
            for part in parts:
                # Split language and quality
                lang_parts = part.strip().split(';q=')
                lang = lang_parts[0].split('-')[0].lower()  # Get primary language code
                
                # Check if this is a supported language
                try:
                    language_preference = SupportedLanguage(lang)
                    break
                except ValueError:
                    continue
        
        # Check for language query parameter override
        lang_param = request.args.get('lang')
        if lang_param:
            try:
                language_preference = SupportedLanguage(lang_param.lower())
            except ValueError:
                logger.warning(f"Unsupported language in query parameter: {lang_param}")
        
        # Set current language in the Flask global context
        g.language = language_preference or self.default_language
        logger.debug(f"Detected language: {g.language}")
        
    def _get_current_language(self) -> SupportedLanguage:
        """Get the current language from Flask's g object.
        
        Returns:
            Current language preference
        """
        return getattr(g, 'language', self.default_language)
    
    async def translate(
        self,
        text: str,
        target_lang: Optional[SupportedLanguage] = None
    ) -> str:
        """Translate text to the target language.
        
        Args:
            text: Text to translate
            target_lang: Target language, defaults to current detected language
            
        Returns:
            Translated text
        """
        if target_lang is None:
            target_lang = self._get_current_language()
            
        return await self.language_service.translate(
            text,
            target_lang=target_lang
        )
    
    async def get_translations(
        self,
        text: str,
        source_lang: Optional[SupportedLanguage] = None
    ) -> Dict[str, str]:
        """Get translations for all supported languages.
        
        Args:
            text: Text to translate
            source_lang: Source language, auto-detected if None
            
        Returns:
            Dictionary mapping language codes to translations
        """
        return await self.language_service.get_all_translations(
            text,
            source_lang=source_lang
        )


def i18n_response(f: Callable) -> Callable:
    """Decorator for Flask view functions to automatically translate JSON responses.
    
    This decorator will detect the user's preferred language and translate
    the response content accordingly. The original English content is preserved
    under an '_original' key if needed.
    
    Args:
        f: Flask view function to decorate
        
    Returns:
        Decorated function that provides translated responses
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the original response
        response = f(*args, **kwargs)
        
        # Skip translation for non-JSON responses
        if not isinstance(response, (dict, Response)) or \
           (isinstance(response, Response) and not response.is_json):
            return response
            
        # Get current language preference
        language = getattr(g, 'language', SupportedLanguage.ENGLISH)
        
        # Skip translation if language is already English
        if language == SupportedLanguage.ENGLISH:
            return response
            
        # For Response objects, extract the JSON data
        if isinstance(response, Response):
            data = response.get_json()
        else:
            data = response
            
        # Translate the response data
        middleware = current_app.i18n_middleware
        translated_data = _translate_dict(middleware.language_service, data, language)
        
        # Return the translated data
        if isinstance(response, Response):
            return Response(
                json.dumps(translated_data),
                status=response.status_code,
                content_type='application/json'
            )
        else:
            return translated_data
    
    return decorated_function


def _translate_dict(
    language_service: LanguageService,
    data: Union[Dict[str, Any], list, str, int, float, bool, None],
    target_lang: SupportedLanguage
) -> Any:
    """Recursively translate all string values in a dictionary or list.
    
    Args:
        language_service: Language service for translations
        data: Data structure to translate
        target_lang: Target language
        
    Returns:
        Translated data structure
    """
    if isinstance(data, dict):
        result = {}
        # Save original data for reference
        result['_original'] = 'en'
        
        # Translate each value
        for key, value in data.items():
            if key.startswith('_'):  # Skip metadata keys
                result[key] = value
                continue
                
            result[key] = _translate_dict(language_service, value, target_lang)
        return result
    elif isinstance(data, list):
        return [_translate_dict(language_service, item, target_lang) for item in data]
    elif isinstance(data, str) and len(data) > 3:  # Only translate non-trivial strings
        try:
            return language_service.translate(data, target_lang=target_lang)
        except TranslationError:
            return data
    else:
        return data
