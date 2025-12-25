"""UI Translation Service for internationalized user interfaces.

This module provides services for translating UI components and loading
translation files for the OnSide platform.
"""
import json
import logging
import os
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from .language_service import SupportedLanguage

logger = logging.getLogger("i18n.ui")


class TranslationLoader:
    """Utility for loading translation files and providing UI translations."""
    
    def __init__(self, translations_dir: Optional[str] = None):
        """Initialize the translation loader.
        
        Args:
            translations_dir: Directory containing translation JSON files
        """
        self.translations_dir = translations_dir or os.path.join(
            os.path.dirname(__file__), 'translations'
        )
        self.translations: Dict[str, Dict[str, Any]] = {}
        self._load_translations()
        
    def _load_translations(self) -> None:
        """Load all translation files from the translations directory."""
        logger.info(f"Loading translations from {self.translations_dir}")
        
        for lang in [lang.value for lang in SupportedLanguage]:
            file_path = os.path.join(self.translations_dir, f"{lang}.json")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.translations[lang] = json.load(f)
                logger.info(f"Loaded translations for {lang}")
            except FileNotFoundError:
                logger.warning(f"Translation file not found: {file_path}")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in translation file: {file_path}")
                # Initialize with empty dict to avoid further errors
                self.translations[lang] = {}
    
    def get_translation(self, key: str, language: SupportedLanguage = SupportedLanguage.ENGLISH) -> str:
        """Get a translation for a UI text key.
        
        Args:
            key: Dotted path to the translation key (e.g. "app.title")
            language: Language to get translation for
            
        Returns:
            Translated text or key if translation not found
        """
        lang_code = language.value
        
        # Try to get translation for requested language
        translation = self._get_nested_value(self.translations.get(lang_code, {}), key)
        
        # Fall back to English if translation not found
        if translation is None and lang_code != SupportedLanguage.ENGLISH.value:
            translation = self._get_nested_value(
                self.translations.get(SupportedLanguage.ENGLISH.value, {}),
                key
            )
            if translation is not None:
                logger.debug(f"Falling back to English for {key} in {lang_code}")
        
        # Return key as fallback if no translation found
        if translation is None:
            logger.warning(f"No translation found for key {key} in {lang_code}")
            return key
            
        return translation
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Optional[str]:
        """Get a value from a nested dictionary using a dotted key.
        
        Args:
            data: Nested dictionary
            key: Dotted path to the value (e.g. "app.title")
            
        Returns:
            Value if found, None otherwise
        """
        if not key or not data:
            return None
            
        parts = key.split('.')
        current = data
        
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
            
        return current if isinstance(current, str) else None
        
    def get_all_translations(self, key: str) -> Dict[str, str]:
        """Get translations for a key in all available languages.
        
        Args:
            key: Dotted path to the translation key
            
        Returns:
            Dictionary mapping language codes to translations
        """
        result = {}
        
        for lang in SupportedLanguage:
            translation = self.get_translation(key, lang)
            result[lang.value] = translation
            
        return result


class UITranslator:
    """Service for translating UI components.
    
    This class provides a convenient interface for translating UI text,
    formatting with variables, and handling pluralization.
    """
    
    def __init__(self, loader: Optional[TranslationLoader] = None):
        """Initialize the UI translator.
        
        Args:
            loader: Translation loader for accessing translations
        """
        self.loader = loader or TranslationLoader()
        
    def translate(
        self,
        key: str,
        language: SupportedLanguage = SupportedLanguage.ENGLISH,
        **variables
    ) -> str:
        """Translate a UI text key with optional variable substitution.
        
        Args:
            key: Translation key (e.g. "app.title")
            language: Target language
            **variables: Variables to substitute in the translation
            
        Returns:
            Translated and formatted text
        """
        translation = self.loader.get_translation(key, language)
        
        # Handle variable substitution if needed
        if variables and '{' in translation:
            try:
                return translation.format(**variables)
            except KeyError as e:
                logger.error(f"Missing variable in translation format: {e}")
                return translation
            except Exception as e:
                logger.error(f"Error formatting translation: {e}")
                return translation
                
        return translation
    
    def get_all(self, key: str, **variables) -> Dict[str, str]:
        """Get translations in all languages for a key.
        
        Args:
            key: Translation key
            **variables: Variables to substitute
            
        Returns:
            Dictionary mapping language codes to translations
        """
        translations = self.loader.get_all_translations(key)
        
        # Apply variable substitution to all translations
        if variables:
            for lang, text in translations.items():
                if '{' in text:
                    try:
                        translations[lang] = text.format(**variables)
                    except (KeyError, ValueError):
                        # Keep original if formatting fails
                        pass
                        
        return translations
        
    def translate_many(
        self,
        keys: List[str],
        language: SupportedLanguage = SupportedLanguage.ENGLISH
    ) -> Dict[str, str]:
        """Translate multiple keys at once.
        
        Args:
            keys: List of translation keys
            language: Target language
            
        Returns:
            Dictionary mapping keys to translations
        """
        return {key: self.translate(key, language) for key in keys}
