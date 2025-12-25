"""Integration module for the OnSide Internationalization Framework.

This module provides a single entry point for accessing all i18n services,
including language detection, translation, UI localization, and middleware.

Usage:
    # Initialize the i18n framework
    i18n = I18nFramework()
    
    # Get a translated UI string
    welcome_text = i18n.ui.translate("app.welcome", language=SupportedLanguage.FRENCH)
    
    # Translate between languages
    translated = await i18n.translate("Hello world", target_lang=SupportedLanguage.JAPANESE)
    
    # Integrate with Flask
    app = Flask(__name__)
    i18n.init_flask(app)
"""
import logging
from typing import Dict, Any, Optional, List, Tuple, Union, TYPE_CHECKING

from flask import Flask

from .language_service import LanguageService, SupportedLanguage, TranslationError
from .ui_translator import UITranslator, TranslationLoader
from .prompt_translator import PromptTranslator
from .flask_middleware import I18nMiddleware, i18n_response

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from src.services.ai.i18n_chain_of_thought import I18nAwareChainOfThought
    from src.services.llm_provider.fallback_manager import FallbackManager

logger = logging.getLogger("i18n.framework")


class I18nFramework:
    """Main entry point for the OnSide Internationalization Framework.
    
    This class brings together all i18n services and provides a unified interface.
    """
    
    def __init__(
        self,
        default_language: SupportedLanguage = SupportedLanguage.ENGLISH,
        translations_dir: Optional[str] = None
    ):
        """Initialize the i18n framework.
        
        Args:
            default_language: Default language for the application
            translations_dir: Directory containing UI translation files
        """
        # Set up core services
        self.default_language = default_language
        self.language_service = LanguageService()
        
        # Set up derived services
        self.translation_loader = TranslationLoader(translations_dir)
        self.ui = UITranslator(self.translation_loader)
        self.prompts = PromptTranslator(self.language_service)
        
        logger.info(f"Initialized i18n framework with default language: {default_language}")
    
    async def detect_language(self, text: str) -> SupportedLanguage:
        """Detect the language of a text string.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language
        """
        return await self.language_service.detect_language(text)
    
    async def translate(
        self,
        text: str,
        source_lang: Optional[SupportedLanguage] = None,
        target_lang: Optional[SupportedLanguage] = None
    ) -> str:
        """Translate text between languages.
        
        Args:
            text: Text to translate
            source_lang: Source language, auto-detected if None
            target_lang: Target language, defaults to the framework's default language
            
        Returns:
            Translated text
        """
        if target_lang is None:
            target_lang = self.default_language
            
        return await self.language_service.translate(
            text,
            source_lang=source_lang,
            target_lang=target_lang
        )
    
    async def get_all_translations(
        self,
        text: str,
        source_lang: Optional[SupportedLanguage] = None
    ) -> Dict[str, str]:
        """Get translations of text in all supported languages.
        
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
    
    async def format_ai_prompt(
        self,
        template_id: str,
        language: SupportedLanguage,
        variables: Dict[str, Any]
    ) -> str:
        """Format an AI prompt in the specified language.
        
        Args:
            template_id: Prompt template identifier
            language: Target language
            variables: Variables for template substitution
            
        Returns:
            Formatted prompt in the target language
        """
        return await self.prompts.translate_prompt(
            template_id,
            language,
            variables
        )
    
    def init_flask(self, app: Flask) -> None:
        """Initialize a Flask application with i18n support.
        
        This method sets up middleware for language detection
        and response translation in Flask applications.
        
        Args:
            app: Flask application to initialize
        """
        # Create middleware instance
        middleware = I18nMiddleware(default_language=self.default_language)
        middleware.language_service = self.language_service
        
        # Initialize the app
        middleware.init_app(app)
        
        # Add the i18n framework to the app context
        app.i18n = self
        
        logger.info("Initialized Flask application with i18n support")
    
    def create_i18n_ai_service(self, llm_manager: 'FallbackManager') -> 'I18nAwareChainOfThought':
        """Create an internationalized AI service with chain-of-thought reasoning.
        
        This factory method creates an AI service that supports multilingual
        prompts and responses, integrated with the i18n framework.
        
        Args:
            llm_manager: The LLM fallback manager for AI services
            
        Returns:
            An instance of I18nAwareChainOfThought
        """
        # Import here to avoid circular imports
        from src.services.ai.i18n_chain_of_thought import I18nAwareChainOfThought
        
        # Create and return the service
        service = I18nAwareChainOfThought(
            llm_manager=llm_manager,
            i18n_framework=self,
            default_language=self.default_language
        )
        
        logger.info("Created internationalized AI service with chain-of-thought reasoning")
        return service
        
    def get_translator_for_language(
        self, 
        language: SupportedLanguage
    ) -> 'LanguageSpecificTranslator':
        """Get a translator bound to a specific language.
        
        This provides a more convenient interface for accessing translations
        in a specific language without repeatedly specifying the language.
        
        Args:
            language: Language to bind to
            
        Returns:
            A translator specific to the requested language
        """
        return LanguageSpecificTranslator(self, language)


class LanguageSpecificTranslator:
    """Translator bound to a specific language.
    
    This class provides a more convenient interface for accessing translations
    in a specific language without repeatedly specifying the language.
    """
    
    def __init__(self, framework: I18nFramework, language: SupportedLanguage):
        """Initialize a language-specific translator.
        
        Args:
            framework: Parent i18n framework
            language: Language to bind to
        """
        self.framework = framework
        self.language = language
        
    def ui(self, key: str, **variables) -> str:
        """Get a UI translation in the bound language.
        
        Args:
            key: Translation key
            **variables: Variables for substitution
            
        Returns:
            Translated text
        """
        return self.framework.ui.translate(key, self.language, **variables)
    
    async def translate(self, text: str, source_lang: Optional[SupportedLanguage] = None) -> str:
        """Translate text to the bound language.
        
        Args:
            text: Text to translate
            source_lang: Source language, auto-detected if None
            
        Returns:
            Translated text
        """
        return await self.framework.translate(
            text,
            source_lang=source_lang,
            target_lang=self.language
        )
    
    async def format_prompt(self, template_id: str, variables: Dict[str, Any]) -> str:
        """Format an AI prompt in the bound language.
        
        Args:
            template_id: Prompt template identifier
            variables: Variables for template substitution
            
        Returns:
            Formatted prompt in the bound language
        """
        return await self.framework.format_ai_prompt(
            template_id,
            self.language,
            variables
        )
