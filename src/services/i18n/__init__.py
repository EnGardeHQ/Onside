"""Internationalization (i18n) service package.

This package provides internationalization capabilities for the OnSide platform,
supporting multiple languages for report generation and user interfaces.
"""

from .language_service import (
    LanguageService,
    SupportedLanguage,
    TranslationError,
    LanguageDetectionError
)

__all__ = [
    'LanguageService',
    'SupportedLanguage',
    'TranslationError',
    'LanguageDetectionError'
]
