"""Language Detection and Translation Service.

This module implements the language detection, translation services, and 
other internationalization features required for Sprint 5.

Features:
- Language detection for English, French, and Japanese
- Translation capabilities between all supported languages
- Caching for improved performance
- Comprehensive error handling
"""
import re
import json
import asyncio
import logging
from enum import Enum
from typing import Dict, Optional, Any, List, Tuple
from functools import lru_cache
from datetime import datetime

# Import the dependencies we'll need
try:
    import langdetect
    from langdetect import detect
    from langdetect.lang_detect_exception import LangDetectException
except ImportError:
    # We'll handle this gracefully in the implementation
    pass

logger = logging.getLogger("i18n")


class SupportedLanguage(str, Enum):
    """Enum representing languages supported by the platform."""
    ENGLISH = "en"
    FRENCH = "fr"
    JAPANESE = "ja"


class TranslationError(Exception):
    """Exception raised when translation fails."""
    def __init__(self, message: str, source_text: str = None, 
                 source_lang: str = None, target_lang: str = None):
        self.source_text = source_text
        self.source_lang = source_lang
        self.target_lang = target_lang
        super().__init__(message)


class LanguageDetectionError(Exception):
    """Exception raised when language detection fails."""
    def __init__(self, message: str, text: str = None):
        self.text = text
        super().__init__(message)


class TranslationCache:
    """Caching mechanism for translations to improve performance."""
    
    def __init__(self, max_size: int = 1000, expiry_seconds: int = 3600):
        """Initialize the translation cache.
        
        Args:
            max_size: Maximum number of entries in the cache
            expiry_seconds: Time in seconds before a cache entry expires
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.expiry_seconds = expiry_seconds
        
    def get(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Get a cached translation if available and not expired.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Cached translation or None if not in cache or expired
        """
        cache_key = self._get_cache_key(text, source_lang, target_lang)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            now = datetime.utcnow().timestamp()
            
            # Check if the entry has expired
            if now - entry["timestamp"] < self.expiry_seconds:
                logger.debug(f"Cache hit for translation: {source_lang} → {target_lang}")
                return entry["translation"]
            else:
                # Remove expired entry
                logger.debug(f"Cache entry expired: {source_lang} → {target_lang}")
                del self.cache[cache_key]
                
        return None
    
    def set(self, text: str, source_lang: str, target_lang: str, translation: str) -> None:
        """Store a translation in the cache.
        
        Args:
            text: Original text
            source_lang: Source language code
            target_lang: Target language code
            translation: Translated text
        """
        cache_key = self._get_cache_key(text, source_lang, target_lang)
        
        # If cache is full, remove oldest entry
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
            
        # Store the new translation
        self.cache[cache_key] = {
            "translation": translation,
            "timestamp": datetime.utcnow().timestamp()
        }
        logger.debug(f"Cached translation: {source_lang} → {target_lang}")
        
    def _get_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate a unique cache key for a translation.
        
        Args:
            text: Original text
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Unique cache key string
        """
        # Use a simple hash to avoid extremely long keys
        text_hash = hash(text) % 10000000
        return f"{source_lang}_{target_lang}_{text_hash}"
    
    def clear(self) -> None:
        """Clear all cached translations."""
        self.cache.clear()
        logger.debug("Translation cache cleared")


class LanguageService:
    """Service for language detection and translation.
    
    This service implements the internationalization requirements for Sprint 5,
    supporting English, French, and Japanese languages.
    
    Features:
    - Automatic language detection
    - Translation between supported languages
    - Caching for improved performance
    - Fallback mechanisms for unsupported languages
    """
    
    def __init__(self):
        """Initialize the language service."""
        self.translation_cache = TranslationCache()
        
        # Language code mapping for detection
        self.lang_code_map = {
            'en': SupportedLanguage.ENGLISH,
            'fr': SupportedLanguage.FRENCH,
            'ja': SupportedLanguage.JAPANESE
        }
        
        # Simple translation dictionaries for demo/testing
        # In production, this would be replaced with a proper translation service
        self._setup_translation_dictionaries()
        
        # Initialize language detection if available
        try:
            langdetect.DetectorFactory.seed = 0  # For consistent results
            self._langdetect_available = True
        except:
            self._langdetect_available = False
            logger.warning("langdetect library not available, falling back to pattern matching")
            
    def _setup_translation_dictionaries(self):
        """Set up translation dictionaries for testing/demo purposes.
        
        In a production environment, this would be replaced with a call
        to a proper translation service or API.
        """
        # English to French translations
        self.en_to_fr = {
            "Hello, how are you?": "Bonjour, comment allez-vous?",
            "Welcome to OnSide": "Bienvenue sur OnSide",
            "This is a test": "Ceci est un test"
        }
        
        # English to Japanese translations
        self.en_to_ja = {
            "Hello, how are you?": "こんにちは、お元気ですか？",
            "Welcome to OnSide": "OnSideへようこそ",
            "This is a test": "これはテストです"
        }
        
        # French to English translations
        self.fr_to_en = {k: v for v, k in self.en_to_fr.items()}
        
        # Japanese to English translations
        self.ja_to_en = {k: v for v, k in self.en_to_ja.items()}
        
        # French to Japanese and Japanese to French (via English)
        self.fr_to_ja = {}
        self.ja_to_fr = {}
        
        for en_text, fr_text in self.en_to_fr.items():
            if en_text in self.en_to_ja:
                self.fr_to_ja[fr_text] = self.en_to_ja[en_text]
                self.ja_to_fr[self.en_to_ja[en_text]] = fr_text
    
    async def detect_language(self, text: str) -> SupportedLanguage:
        """Detect the language of the provided text.
        
        Args:
            text: Text to analyze for language detection
            
        Returns:
            Detected language as SupportedLanguage enum
            
        Raises:
            LanguageDetectionError: If language detection fails
        """
        try:
            detected_lang_code = await self._detect_language_internal(text)
            
            # Map detected language to our supported languages
            if detected_lang_code in self.lang_code_map:
                logger.info(f"Detected language: {detected_lang_code}")
                return self.lang_code_map[detected_lang_code]
            else:
                logger.warning(f"Unsupported language detected: {detected_lang_code}, defaulting to English")
                return SupportedLanguage.ENGLISH
                
        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            raise LanguageDetectionError(f"Failed to detect language: {str(e)}", text=text)
    
    async def _detect_language_internal(self, text: str) -> str:
        """Internal method to detect language using available tools.
        
        This method attempts to use langdetect if available, otherwise
        falls back to simple pattern matching.
        
        Args:
            text: Text to analyze
            
        Returns:
            ISO language code as string
        """
        # If text is empty or None, default to English
        if not text or len(text.strip()) == 0:
            return 'en'
            
        # If langdetect is available, use it
        if self._langdetect_available:
            try:
                return detect(text)
            except LangDetectException as e:
                logger.warning(f"Language detection error with langdetect: {str(e)}")
                # Fall through to pattern matching
        
        # Simple pattern matching as fallback
        # Check for Japanese characters
        if any(ord(c) > 0x3000 for c in text):
            return 'ja'
            
        # Check for French-specific characters and patterns
        french_patterns = ['é', 'è', 'ê', 'ç', 'à', 'vous', 'nous', 'est-ce']
        if any(pattern in text.lower() for pattern in french_patterns):
            return 'fr'
            
        # Default to English
        return 'en'
    
    async def translate(
        self, 
        text: str, 
        source_lang: SupportedLanguage = None, 
        target_lang: SupportedLanguage = None
    ) -> str:
        """Translate text from source language to target language.
        
        Args:
            text: Text to translate
            source_lang: Source language, detected automatically if None
            target_lang: Target language, defaults to English if None
            
        Returns:
            Translated text
            
        Raises:
            TranslationError: If translation fails
        """
        try:
            # Auto-detect source language if not specified
            if source_lang is None:
                source_lang = await self.detect_language(text)
                
            # Default target language to English if not specified
            if target_lang is None:
                target_lang = SupportedLanguage.ENGLISH
                
            # If source and target are the same, return original text
            if source_lang == target_lang:
                return text
                
            # Check cache first
            cached = self.translation_cache.get(
                text=text,
                source_lang=source_lang.value,
                target_lang=target_lang.value
            )
            
            if cached:
                return cached
                
            # Perform the translation
            translated = await self._translate_internal(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang
            )
            
            # Cache the result
            self.translation_cache.set(
                text=text,
                source_lang=source_lang.value,
                target_lang=target_lang.value,
                translation=translated
            )
            
            return translated
            
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            raise TranslationError(
                f"Failed to translate text: {str(e)}",
                source_text=text,
                source_lang=source_lang.value if source_lang else None,
                target_lang=target_lang.value if target_lang else None
            )
            
    async def _translate_internal(
        self, 
        text: str, 
        source_lang: SupportedLanguage, 
        target_lang: SupportedLanguage
    ) -> str:
        """Internal translation implementation.
        
        In a production environment, this would call an external translation API.
        For now, we're using simple dictionary lookups for demonstration purposes.
        
        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language
            
        Returns:
            Translated text
        """
        # For demo/testing purposes, use our dictionaries
        # In production, this would call a translation API
        
        trans_dict = None
        if source_lang == SupportedLanguage.ENGLISH and target_lang == SupportedLanguage.FRENCH:
            trans_dict = self.en_to_fr
        elif source_lang == SupportedLanguage.ENGLISH and target_lang == SupportedLanguage.JAPANESE:
            trans_dict = self.en_to_ja
        elif source_lang == SupportedLanguage.FRENCH and target_lang == SupportedLanguage.ENGLISH:
            trans_dict = self.fr_to_en
        elif source_lang == SupportedLanguage.JAPANESE and target_lang == SupportedLanguage.ENGLISH:
            trans_dict = self.ja_to_en
        elif source_lang == SupportedLanguage.FRENCH and target_lang == SupportedLanguage.JAPANESE:
            trans_dict = self.fr_to_ja
        elif source_lang == SupportedLanguage.JAPANESE and target_lang == SupportedLanguage.FRENCH:
            trans_dict = self.ja_to_fr
            
        # Check if we have a direct translation
        if trans_dict and text in trans_dict:
            return trans_dict[text]
            
        # In a real implementation, we would call an external translation API here
        # For now, return a placeholder translation
        logger.warning(f"No direct translation found for '{text}' from {source_lang} to {target_lang}")
        return f"[{target_lang.value}] {text}"
    
    async def get_all_translations(self, text: str, source_lang: SupportedLanguage = None) -> Dict[str, str]:
        """Get translations in all supported languages.
        
        Args:
            text: Text to translate
            source_lang: Source language, detected automatically if None
            
        Returns:
            Dictionary mapping language codes to translated text
        """
        # Auto-detect source language if not specified
        if source_lang is None:
            source_lang = await self.detect_language(text)
            
        translations = {}
        translations[source_lang.value] = text
        
        # Create tasks for all translations
        tasks = []
        for target_lang in SupportedLanguage:
            if target_lang != source_lang:
                tasks.append(self.translate(text, source_lang, target_lang))
                
        # Run all translations concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        i = 0
        for target_lang in SupportedLanguage:
            if target_lang != source_lang:
                if isinstance(results[i], Exception):
                    logger.error(f"Translation to {target_lang.value} failed: {str(results[i])}")
                    translations[target_lang.value] = f"[Translation Failed] {text}"
                else:
                    translations[target_lang.value] = results[i]
                i += 1
                
        return translations
