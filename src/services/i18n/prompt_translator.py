"""Prompt Translation Service for internationalized AI interactions.

This module provides services for translating AI prompts and responses
to support multilingual capabilities in the OnSide platform.
"""
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from .language_service import LanguageService, SupportedLanguage, TranslationError

logger = logging.getLogger("i18n.prompt")


class PromptTemplate:
    """Container for multilingual prompt templates.
    
    This class manages prompt templates across multiple languages,
    supporting variable substitution and format strings.
    """
    
    def __init__(self, template_id: str, templates: Dict[str, str]):
        """Initialize a prompt template.
        
        Args:
            template_id: Unique identifier for this template
            templates: Dictionary mapping language codes to templates
        """
        self.template_id = template_id
        self.templates = templates
        
    def get_template(self, language: SupportedLanguage) -> str:
        """Get the template for a specific language.
        
        Args:
            language: Language to get template for
            
        Returns:
            Template string for the requested language
            
        Raises:
            KeyError: If no template exists for the language
        """
        lang_code = language.value
        if lang_code in self.templates:
            return self.templates[lang_code]
        elif SupportedLanguage.ENGLISH.value in self.templates:
            logger.warning(
                f"No template found for language {lang_code}, "
                f"falling back to English for template {self.template_id}"
            )
            return self.templates[SupportedLanguage.ENGLISH.value]
        else:
            raise KeyError(f"No template found for template_id: {self.template_id}")
            
    def format(self, language: SupportedLanguage, **kwargs) -> str:
        """Format a template with the provided variables.
        
        Args:
            language: Language to format template for
            **kwargs: Variables to substitute in the template
            
        Returns:
            Formatted template string
        """
        template = self.get_template(language)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing variable in template: {e}")
            # Return template with error markers
            return f"ERROR({e}) - {template}"
        except Exception as e:
            logger.error(f"Error formatting template: {e}")
            return f"ERROR - {template}"


class PromptTranslator:
    """Service for translating AI prompts and responses.
    
    This service manages prompt templates, translates variables,
    and ensures all AI interactions can be multilingual.
    """
    
    def __init__(self, language_service: Optional[LanguageService] = None):
        """Initialize the prompt translator.
        
        Args:
            language_service: Language service for translations
        """
        self.language_service = language_service or LanguageService()
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_built_in_templates()
        
    def _load_built_in_templates(self):
        """Load built-in prompt templates for AI services."""
        # Competitor Analysis prompts
        self.register_template(
            "competitor_analysis",
            {
                "en": (
                    "Analyze the following competitor data and provide insights:\n\n"
                    "Company: {company_name}\n"
                    "Industry: {industry}\n"
                    "Key metrics: {metrics}\n\n"
                    "Please provide a detailed analysis of strengths, weaknesses, "
                    "opportunities, and threats. Include your chain-of-thought reasoning."
                ),
                "fr": (
                    "Analysez les données concurrentielles suivantes et fournissez des perspectives :\n\n"
                    "Entreprise : {company_name}\n"
                    "Industrie : {industry}\n"
                    "Indicateurs clés : {metrics}\n\n"
                    "Veuillez fournir une analyse détaillée des forces, faiblesses, "
                    "opportunités et menaces. Incluez votre raisonnement détaillé."
                ),
                "ja": (
                    "以下の競合他社データを分析し、洞察を提供してください：\n\n"
                    "企業：{company_name}\n"
                    "業界：{industry}\n"
                    "主要指標：{metrics}\n\n"
                    "強み、弱み、機会、脅威の詳細な分析を提供してください。思考過程も含めてください。"
                )
            }
        )
        
        # Market Analysis prompts
        self.register_template(
            "market_analysis",
            {
                "en": (
                    "Provide market analysis for the following parameters:\n\n"
                    "Industry: {industry}\n"
                    "Region: {region}\n"
                    "Time period: {time_period}\n\n"
                    "Focus on market trends, growth opportunities, and key players. "
                    "Include your chain-of-thought reasoning."
                ),
                "fr": (
                    "Fournir une analyse de marché pour les paramètres suivants :\n\n"
                    "Industrie : {industry}\n"
                    "Région : {region}\n"
                    "Période : {time_period}\n\n"
                    "Concentrez-vous sur les tendances du marché, les opportunités de croissance "
                    "et les acteurs clés. Incluez votre raisonnement détaillé."
                ),
                "ja": (
                    "以下のパラメータに基づく市場分析を提供してください：\n\n"
                    "業界：{industry}\n"
                    "地域：{region}\n"
                    "期間：{time_period}\n\n"
                    "市場トレンド、成長機会、主要プレーヤーに焦点を当ててください。思考過程も含めてください。"
                )
            }
        )
        
        # Audience Analysis prompts
        self.register_template(
            "audience_analysis",
            {
                "en": (
                    "Analyze the audience data for {company_name} and provide insights:\n\n"
                    "Demographics: {demographics}\n"
                    "Engagement metrics: {engagement}\n"
                    "Content preferences: {preferences}\n\n"
                    "Generate detailed audience personas and recommendations. "
                    "Include your chain-of-thought reasoning."
                ),
                "fr": (
                    "Analysez les données d'audience pour {company_name} et fournissez des perspectives :\n\n"
                    "Démographie : {demographics}\n"
                    "Métriques d'engagement : {engagement}\n"
                    "Préférences de contenu : {preferences}\n\n"
                    "Générez des personas d'audience détaillés et des recommandations. "
                    "Incluez votre raisonnement détaillé."
                ),
                "ja": (
                    "{company_name}のオーディエンスデータを分析し、洞察を提供してください：\n\n"
                    "人口統計：{demographics}\n"
                    "エンゲージメント指標：{engagement}\n"
                    "コンテンツ設定：{preferences}\n\n"
                    "詳細なオーディエンスペルソナと推奨事項を生成してください。思考過程も含めてください。"
                )
            }
        )
        
    def register_template(self, template_id: str, templates: Dict[str, str]) -> None:
        """Register a new prompt template.
        
        Args:
            template_id: Unique identifier for the template
            templates: Dictionary mapping language codes to templates
        """
        self.templates[template_id] = PromptTemplate(template_id, templates)
        logger.info(f"Registered prompt template: {template_id}")
        
    def get_template(self, template_id: str) -> PromptTemplate:
        """Get a registered template by ID.
        
        Args:
            template_id: Template identifier
            
        Returns:
            PromptTemplate object
            
        Raises:
            KeyError: If template does not exist
        """
        if template_id in self.templates:
            return self.templates[template_id]
        raise KeyError(f"Template not found: {template_id}")
    
    async def translate_prompt(
        self,
        template_id: str,
        language: SupportedLanguage,
        variables: Dict[str, Any]
    ) -> str:
        """Generate a prompt in the specified language.
        
        This method handles both template selection and variable translation.
        
        Args:
            template_id: Template identifier
            language: Target language
            variables: Variables for template substitution
            
        Returns:
            Formatted prompt in the target language
        """
        template = self.get_template(template_id)
        
        # Translate variables if they are strings
        translated_vars = {}
        for key, value in variables.items():
            if isinstance(value, str):
                try:
                    # Translate the variable content
                    translated_vars[key] = await self.language_service.translate(
                        value,
                        target_lang=language
                    )
                except TranslationError as e:
                    logger.warning(f"Failed to translate variable {key}: {e}")
                    translated_vars[key] = value
            else:
                translated_vars[key] = value
                
        # Format the template with translated variables
        return template.format(language, **translated_vars)
    
    async def translate_response(
        self,
        response: str,
        source_lang: Optional[SupportedLanguage] = None,
        target_lang: SupportedLanguage = None
    ) -> str:
        """Translate an AI response to the target language.
        
        Args:
            response: AI response text
            source_lang: Source language, auto-detected if None
            target_lang: Target language, defaults to English
            
        Returns:
            Translated response
        """
        return await self.language_service.translate(
            response,
            source_lang=source_lang,
            target_lang=target_lang
        )
    
    async def format_multilingual_response(
        self,
        response: str,
        source_lang: Optional[SupportedLanguage] = None
    ) -> Dict[str, str]:
        """Generate responses in all supported languages.
        
        Args:
            response: Original AI response text
            source_lang: Source language, auto-detected if None
            
        Returns:
            Dictionary mapping language codes to translated responses
        """
        # Get translations for all supported languages
        return await self.language_service.get_all_translations(
            response,
            source_lang=source_lang
        )
