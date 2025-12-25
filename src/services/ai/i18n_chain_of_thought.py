"""Internationalized Chain of Thought AI Service.

This module provides an extension of the LLMWithChainOfThought base class
with multilingual capabilities for Sprint 5 internationalization requirements.

Following Semantic Seed coding standards with proper error handling,
logging, and type hints.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
from datetime import datetime

from src.models.report import Report
from src.models.llm_fallback import LLMProvider
from src.services.ai.llm_with_chain_of_thought import LLMWithChainOfThought
from src.services.i18n.language_service import SupportedLanguage, TranslationError

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from src.services.llm_provider.fallback_manager import FallbackManager
    from src.services.i18n.integration import I18nFramework


class I18nAwareChainOfThought(LLMWithChainOfThought):
    """
    Extension of LLMWithChainOfThought with internationalization support.
    
    This class implements Sprint 5 requirements for multilingual AI services,
    enabling chain-of-thought reasoning in all supported languages.
    
    Features:
    - All features from LLMWithChainOfThought
    - Support for prompts in English, French, and Japanese
    - Translation of AI responses to the user's preferred language
    - Preservation of reasoning steps across languages
    - Comprehensive error handling for translation failures
    """
    
    def __init__(
        self,
        llm_manager: 'FallbackManager',
        i18n_framework: 'I18nFramework',
        default_language: SupportedLanguage = SupportedLanguage.ENGLISH
    ):
        """Initialize the internationalized chain of thought service.
        
        Args:
            llm_manager: The LLM fallback manager
            i18n_framework: The internationalization framework
            default_language: Default language to use when none specified
        """
        super().__init__(llm_manager)
        self.i18n_framework = i18n_framework
        self.default_language = default_language
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.logger.info(f"Initialized {self.__class__.__name__} with default language {default_language.value}")
    
    async def execute_multilingual_prompt(
        self,
        template_id: str,
        language: SupportedLanguage,
        variables: Dict[str, Any],
        report: Report,
        with_chain_of_thought: bool = True,
        confidence_threshold: Optional[float] = None,
        **kwargs
    ) -> Tuple[Dict[str, Any], float]:
        """
        Execute an AI prompt using a template in the specified language.
        
        Args:
            template_id: ID of the prompt template to use
            language: Target language for the prompt
            variables: Variables to substitute in the template
            report: The report instance for tracking
            with_chain_of_thought: Whether to include chain-of-thought reasoning
            confidence_threshold: Minimum confidence score required
            **kwargs: Additional arguments for the LLM call
            
        Returns:
            Tuple of (result dict, confidence score)
        """
        try:
            self._add_reasoning_step(
                "Language selection",
                f"Using specified language: {language.value}"
            )
            
            # Format the prompt in the target language
            prompt = await self.i18n_framework.format_ai_prompt(
                template_id, language, variables
            )
            
            self._add_reasoning_step(
                "Prompt preparation",
                f"Prepared prompt in {language.value}"
            )
            
            # Execute the prompt using the base class method
            result, confidence = await self._execute_llm_with_reasoning(
                prompt=prompt,
                report=report,
                with_chain_of_thought=with_chain_of_thought,
                confidence_threshold=confidence_threshold,
                **kwargs
            )
            
            # Store the language in the result
            result["language"] = language.value
            
            # Add user-friendly information for reporting
            language_names = {
                SupportedLanguage.ENGLISH: "English",
                SupportedLanguage.FRENCH: "French",
                SupportedLanguage.JAPANESE: "Japanese"
            }
            report.metadata["language"] = language_names.get(language, language.value)
            report.metadata["internationalized"] = True
            
            return result, confidence
            
        except Exception as e:
            error_msg = f"Error executing multilingual prompt: {str(e)}"
            self.logger.error(error_msg)
            self._add_reasoning_step("Error", error_msg)
            
            # Return empty result with low confidence
            return {"error": error_msg, "language": language.value}, 0.3
    
    async def translate_llm_result(
        self,
        result: Dict[str, Any],
        target_language: SupportedLanguage
    ) -> Dict[str, Any]:
        """
        Translate an LLM result to the target language.
        
        Args:
            result: The LLM result dictionary
            target_language: Target language for translation
            
        Returns:
            Translated result dictionary
        """
        if not result:
            return result
        
        try:    
            translated_result = result.copy()
            source_language = SupportedLanguage(result.get("language", SupportedLanguage.ENGLISH))
            
            # Skip translation if already in target language
            if source_language == target_language:
                self.logger.debug(f"Result already in target language {target_language.value}, skipping translation")
                return result
                
            # Translate reasoning if present
            if "reasoning" in result and isinstance(result["reasoning"], str):
                self.logger.debug(f"Translating reasoning from {source_language.value} to {target_language.value}")
                translated_result["reasoning"] = await self.i18n_framework.translate(
                    result["reasoning"],
                    source_lang=source_language,
                    target_lang=target_language
                )
                
            # Translate result content recursively
            if "result" in result and isinstance(result["result"], dict):
                self.logger.debug(f"Translating result content from {source_language.value} to {target_language.value}")
                translated_result["result"] = await self._translate_dict_recursively(
                    result["result"],
                    source_language=source_language,
                    target_language=target_language
                )
                
            # Update language information
            translated_result["language"] = target_language.value
            translated_result["translated_from"] = source_language.value
                
            return translated_result
            
        except TranslationError as e:
            self.logger.error(f"Translation error: {str(e)}")
            # Return original result with error metadata
            result["translation_error"] = str(e)
            return result
            
        except Exception as e:
            self.logger.error(f"Unexpected error during result translation: {str(e)}")
            # Return original result with error metadata
            result["translation_error"] = f"Unexpected error: {str(e)}"
            return result
    
    async def _translate_dict_recursively(
        self,
        data: Dict[str, Any],
        source_language: SupportedLanguage,
        target_language: SupportedLanguage
    ) -> Dict[str, Any]:
        """
        Recursively translate all string values in a dictionary.
        
        Args:
            data: Dictionary with values to translate
            source_language: Source language of the data
            target_language: Target language for translation
            
        Returns:
            Dictionary with translated values
        """
        result = {}
        
        # Skip translation if languages are the same
        if source_language == target_language:
            return data
        
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 2:
                # Translate string values
                try:
                    result[key] = await self.i18n_framework.translate(
                        value,
                        source_lang=source_language,
                        target_lang=target_language
                    )
                except TranslationError:
                    # Keep original text on translation error
                    result[key] = value
                    self.logger.warning(f"Failed to translate value for key '{key}'")
                    
            elif isinstance(value, dict):
                # Recursively translate nested dictionaries
                result[key] = await self._translate_dict_recursively(
                    value,
                    source_language=source_language,
                    target_language=target_language
                )
                
            elif isinstance(value, list):
                # Translate list items
                translated_list = []
                for item in value:
                    if isinstance(item, str) and len(item) > 2:
                        try:
                            translated_item = await self.i18n_framework.translate(
                                item,
                                source_lang=source_language,
                                target_lang=target_language
                            )
                            translated_list.append(translated_item)
                        except TranslationError:
                            # Keep original text on translation error
                            translated_list.append(item)
                            self.logger.warning(f"Failed to translate list item: {item[:50]}...")
                            
                    elif isinstance(item, dict):
                        translated_dict = await self._translate_dict_recursively(
                            item,
                            source_language=source_language,
                            target_language=target_language
                        )
                        translated_list.append(translated_dict)
                        
                    else:
                        # Keep non-string values as-is
                        translated_list.append(item)
                        
                result[key] = translated_list
                
            else:
                # Keep non-string values as-is
                result[key] = value
                
        return result
    
    async def execute_with_language(
        self,
        prompt: str,
        report: Report,
        language: SupportedLanguage = None,
        with_chain_of_thought: bool = True,
        confidence_threshold: Optional[float] = None,
        **kwargs
    ) -> Tuple[Dict[str, Any], float]:
        """
        Execute an LLM call with the specified language.
        
        Args:
            prompt: The prompt in any language
            report: The report instance for tracking
            language: Language of the prompt (detected if None)
            with_chain_of_thought: Whether to include chain-of-thought reasoning
            confidence_threshold: Minimum confidence score required
            **kwargs: Additional arguments for the LLM call
            
        Returns:
            Tuple of (result dict, confidence score)
        """
        try:
            # Detect language if not specified
            if language is None:
                language = await self.i18n_framework.detect_language(prompt)
                self._add_reasoning_step(
                    "Language detection",
                    f"Detected language: {language.value}"
                )
            else:
                self._add_reasoning_step(
                    "Language handling",
                    f"Using specified language: {language.value}"
                )
                
            # Record original language in report
            language_names = {
                SupportedLanguage.ENGLISH: "English",
                SupportedLanguage.FRENCH: "French",
                SupportedLanguage.JAPANESE: "Japanese"
            }
            report.metadata["original_language"] = language_names.get(language, language.value)
            report.metadata["internationalized"] = True
                
            # Translate prompt to English for LLM if not already in English
            llm_prompt = prompt
            if language != SupportedLanguage.ENGLISH:
                llm_prompt = await self.i18n_framework.translate(
                    prompt,
                    source_lang=language,
                    target_lang=SupportedLanguage.ENGLISH
                )
                self._add_reasoning_step(
                    "Prompt translation",
                    f"Translated prompt from {language.value} to English for LLM processing"
                )
                
            # Execute the prompt using the base class method
            result, confidence = await self._execute_llm_with_reasoning(
                prompt=llm_prompt,
                report=report,
                with_chain_of_thought=with_chain_of_thought,
                confidence_threshold=confidence_threshold,
                **kwargs
            )
            
            # Translate result back to original language if needed
            if language != SupportedLanguage.ENGLISH:
                result_before_translation = result.copy()
                result["language"] = SupportedLanguage.ENGLISH.value
                
                try:
                    result = await self.translate_llm_result(result, language)
                    self._add_reasoning_step(
                        "Result translation",
                        f"Translated result back to {language.value}"
                    )
                except Exception as e:
                    self.logger.error(f"Failed to translate result: {str(e)}")
                    # Restore original result with error info
                    result = result_before_translation
                    result["translation_error"] = str(e)
                
            # Ensure language is set in the result
            result["language"] = language.value
            
            return result, confidence
            
        except Exception as e:
            error_msg = f"Error in execute_with_language: {str(e)}"
            self.logger.error(error_msg)
            self._add_reasoning_step("Error", error_msg)
            
            # Return empty result with low confidence
            return {"error": error_msg, "language": getattr(language, "value", "unknown")}, 0.3
