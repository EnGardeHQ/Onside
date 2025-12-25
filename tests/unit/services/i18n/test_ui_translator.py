"""Unit tests for the UI Translator Service.

This module tests the UI translation capabilities including
translation loading, retrieval, and formatting.
"""
import pytest
import os
import json
from unittest.mock import patch, mock_open, MagicMock

from src.services.i18n.ui_translator import TranslationLoader, UITranslator
from src.services.i18n.language_service import SupportedLanguage


class TestTranslationLoader:
    """Test suite for the TranslationLoader class."""
    
    @pytest.fixture
    def mock_translations(self):
        """Create mock translation data for testing."""
        return {
            "en": {
                "app": {
                    "title": "OnSide",
                    "welcome": "Welcome to OnSide"
                },
                "reports": {
                    "title": "Reports",
                    "new_report": "New Report"
                }
            },
            "fr": {
                "app": {
                    "title": "OnSide",
                    "welcome": "Bienvenue sur OnSide"
                },
                "reports": {
                    "title": "Rapports",
                    "new_report": "Nouveau Rapport"
                }
            },
            "ja": {
                "app": {
                    "title": "OnSide",
                    "welcome": "OnSideへようこそ"
                },
                "reports": {
                    "title": "レポート",
                    "new_report": "新規レポート"
                }
            }
        }
    
    @patch('os.path.join')
    @patch('json.load')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_translations(self, mock_file, mock_json_load, mock_path_join, mock_translations):
        """Test loading translations from files."""
        # Setup mocks
        mock_path_join.side_effect = lambda *args: '/'.join(args)
        mock_json_load.side_effect = lambda f: mock_translations.get(
            os.path.basename(f.name).split('.')[0], {}
        )
        
        # Given a translation loader
        loader = TranslationLoader()
        
        # When translations are loaded
        # (this happens in __init__, so we don't need to call it explicitly)
        
        # Then the loader should have translations for all languages
        assert set(loader.translations.keys()) == set(["en", "fr", "ja"])
        assert mock_file.call_count == 3  # One for each language
    
    def test_get_translation_existing(self):
        """Test retrieving an existing translation."""
        # Given a loader with mock translations
        loader = TranslationLoader()
        loader.translations = {
            "en": {
                "app": {
                    "title": "OnSide"
                }
            }
        }
        
        # When we get a translation that exists
        result = loader.get_translation("app.title")
        
        # Then we should get the correct translation
        assert result == "OnSide"
    
    def test_get_translation_nested(self):
        """Test retrieving a deeply nested translation."""
        # Given a loader with nested translations
        loader = TranslationLoader()
        loader.translations = {
            "en": {
                "reports": {
                    "status": {
                        "completed": "Completed"
                    }
                }
            }
        }
        
        # When we get a deeply nested translation
        result = loader.get_translation("reports.status.completed")
        
        # Then we should get the correct translation
        assert result == "Completed"
    
    def test_get_translation_missing_key(self):
        """Test behavior when translation key is missing."""
        # Given a loader with some translations
        loader = TranslationLoader()
        loader.translations = {
            "en": {
                "app": {
                    "title": "OnSide"
                }
            }
        }
        
        # When we get a non-existent translation
        result = loader.get_translation("app.nonexistent")
        
        # Then we should get the key back as fallback
        assert result == "app.nonexistent"
    
    def test_get_translation_fallback_to_english(self):
        """Test fallback to English when translation missing in target language."""
        # Given a loader with English but incomplete French translations
        loader = TranslationLoader()
        loader.translations = {
            "en": {
                "app": {
                    "title": "OnSide",
                    "subtitle": "Competitive Intelligence"
                }
            },
            "fr": {
                "app": {
                    "title": "OnSide"
                    # subtitle missing
                }
            }
        }
        
        # When we request a French translation that doesn't exist
        result = loader.get_translation("app.subtitle", SupportedLanguage.FRENCH)
        
        # Then it should fall back to English
        assert result == "Competitive Intelligence"
    
    def test_get_all_translations(self):
        """Test getting translations in all languages."""
        # Given a loader with translations in multiple languages
        loader = TranslationLoader()
        loader.translations = {
            "en": {
                "app": {
                    "title": "OnSide"
                }
            },
            "fr": {
                "app": {
                    "title": "OnSide"
                }
            },
            "ja": {
                "app": {
                    "title": "OnSide"
                }
            }
        }
        
        # When we get all translations for a key
        result = loader.get_all_translations("app.title")
        
        # Then we should get translations for all languages
        assert set(result.keys()) == set(["en", "fr", "ja"])
        assert all(v == "OnSide" for v in result.values())


class TestUITranslator:
    """Test suite for the UITranslator class."""
    
    @pytest.fixture
    def mock_loader(self):
        """Create a mock translation loader."""
        loader = MagicMock(spec=TranslationLoader)
        
        # Set up get_translation to return mock translations
        def mock_get_translation(key, language=SupportedLanguage.ENGLISH):
            translations = {
                "app.title": {
                    "en": "OnSide",
                    "fr": "OnSide",
                    "ja": "OnSide"
                },
                "app.welcome": {
                    "en": "Welcome to OnSide",
                    "fr": "Bienvenue sur OnSide",
                    "ja": "OnSideへようこそ"
                },
                "reports.title": {
                    "en": "Reports",
                    "fr": "Rapports",
                    "ja": "レポート"
                },
                "reports.count": {
                    "en": "You have {count} reports",
                    "fr": "Vous avez {count} rapports",
                    "ja": "{count}件のレポートがあります"
                }
            }
            
            lang_code = language.value
            if key in translations and lang_code in translations[key]:
                return translations[key][lang_code]
            return key
            
        loader.get_translation.side_effect = mock_get_translation
        
        # Set up get_all_translations to return all language variants
        def mock_get_all_translations(key):
            translations = {
                "app.title": {
                    "en": "OnSide",
                    "fr": "OnSide",
                    "ja": "OnSide"
                },
                "app.welcome": {
                    "en": "Welcome to OnSide",
                    "fr": "Bienvenue sur OnSide",
                    "ja": "OnSideへようこそ"
                }
            }
            
            if key in translations:
                return translations[key]
            return {lang.value: key for lang in SupportedLanguage}
            
        loader.get_all_translations.side_effect = mock_get_all_translations
        
        return loader
    
    def test_translate_simple(self, mock_loader):
        """Test simple translation without variables."""
        # Given a translator with a mock loader
        translator = UITranslator(loader=mock_loader)
        
        # When we translate a simple key
        result = translator.translate("app.welcome")
        
        # Then we should get the correct translation
        assert result == "Welcome to OnSide"
    
    def test_translate_with_language(self, mock_loader):
        """Test translation with specific language."""
        # Given a translator with a mock loader
        translator = UITranslator(loader=mock_loader)
        
        # When we translate with a specific language
        result = translator.translate("app.welcome", SupportedLanguage.JAPANESE)
        
        # Then we should get the translation in that language
        assert result == "OnSideへようこそ"
    
    def test_translate_with_variables(self, mock_loader):
        """Test translation with variable substitution."""
        # Given a translator with a mock loader
        translator = UITranslator(loader=mock_loader)
        
        # When we translate with variables
        result = translator.translate("reports.count", variables={"count": 5})
        
        # Then the variables should be substituted
        assert result == "You have 5 reports"
    
    def test_translate_many(self, mock_loader):
        """Test translating multiple keys at once."""
        # Given a translator with a mock loader
        translator = UITranslator(loader=mock_loader)
        
        # When we translate multiple keys
        result = translator.translate_many(["app.title", "reports.title"])
        
        # Then we should get translations for all keys
        assert result == {
            "app.title": "OnSide",
            "reports.title": "Reports"
        }
    
    def test_get_all(self, mock_loader):
        """Test getting all language translations for a key."""
        # Given a translator with a mock loader
        translator = UITranslator(loader=mock_loader)
        
        # When we get all translations for a key
        result = translator.get_all("app.welcome")
        
        # Then we should get translations in all languages
        assert result == {
            "en": "Welcome to OnSide",
            "fr": "Bienvenue sur OnSide",
            "ja": "OnSideへようこそ"
        }
