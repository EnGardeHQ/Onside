#!/usr/bin/env python
"""
Enhanced AI Analysis Service for TCS Report

This service provides advanced AI-driven competitor analysis with confidence scoring 
and chain-of-thought reasoning capabilities. It implements its own LLM interaction
logic to ensure operation even when OnSide core services aren't available.

Following Semantic Seed Venture Studio Coding Standards V2.0.
Implements BDD principles with proper error handling and logging.
"""

import os
import json
import logging
import traceback
import asyncio
import aiohttp
import sys
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import datetime as dt
# Python 3.10 compatibility - use timezone.utc instead of UTC
UTC = dt.timezone.utc
import re

# Ensure src directory is properly added to Python path for imports
os.environ['PYTHONPATH'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')) + os.pathsep + os.environ.get('PYTHONPATH', '')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))


# Define local alternatives for OnSide core services
class LocalLLMProvider:
    """Local version of LLMProvider for when the core services aren't available."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    FALLBACK = "fallback"

class LocalReport:
    """Local version of Report for when the core services aren't available."""
    def __init__(self, title, description, metadata=None):
        self.title = title
        self.description = description
        self.metadata = metadata or {}
        self.chain_of_thought = []

# Try to import OnSide core services, but use local alternatives if not available
ONSIDE_CORE_AVAILABLE = False
try:
    from src.models.llm_fallback import LLMProvider
    from src.models.report import Report
    from src.services.llm_provider.fallback_manager import FallbackManager
    from src.services.ai.llm_with_chain_of_thought import LLMWithChainOfThought
    ONSIDE_CORE_AVAILABLE = True
    logging.info("Successfully imported OnSide core services")
except ImportError as e:
    # Use local alternatives if OnSide core services are not available
    logging.warning(f"OnSide core services not available: {str(e)}. Using API-only implementation.")
    LLMProvider = LocalLLMProvider
    Report = LocalReport



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("enhanced_ai_service")

class EnhancedAIService:
    """
    Enhanced AI Analysis Service for TCS Reports
    
    Provides advanced AI-driven analysis with confidence scoring,
    reasoning chains, and fallback support using OnSide's core capabilities.
    """
    
    def __init__(self, api_keys: Dict[str, str] = None):
        """
        Initialize the enhanced AI service.
        
        Args:
            api_keys: Dictionary of API keys for LLM providers
        """
        self.api_keys = api_keys or {
            "openai": os.environ.get("OPENAI_API_KEY", ""),
            "anthropic": os.environ.get("ANTHROPIC_API_KEY", "")
        }
        
        # Initialize a dummy report object if OnSide core is available
        self.report = None
        if ONSIDE_CORE_AVAILABLE:
            try:
                self.report = Report(
                    title="TCS Competitive Intelligence Report",
                    description="Advanced analysis of Tata Consultancy Services",
                    metadata={
                        "analysis_type": "competitive_intelligence",
                        "company": "tcs",
                        "confidence_threshold": 0.75
                    }
                )
                logger.info("OnSide Report object initialized")
            except Exception as e:
                logger.error(f"Error initializing Report: {str(e)}")
        
        # Cache for reused prompts to optimize token usage
        self._prompt_cache = {}
    
    async def generate_competitor_analysis_with_cot(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate competitor analysis with chain-of-thought reasoning using the
        KPMG-style advanced analytical framework.
        
        Args:
            company_data: Basic company information
            
        Returns:
            Enhanced AI analysis with reasoning chains and confidence scores
        """
        logger.info(f"Generating advanced competitor analysis with chain-of-thought for {company_data.get('company', 'TCS')}")
        
        # If OnSide core is available, use LLMWithChainOfThought
        if ONSIDE_CORE_AVAILABLE:
            try:
                # Construct enhanced prompt for chain-of-thought reasoning
                cot_prompt = self._construct_competitor_cot_prompt(company_data)
                
                # Initialize FallbackManager with proper provider configuration
                # First check if the providers need to be properly initialized
                providers = [LLMProvider.OPENAI, LLMProvider.ANTHROPIC]
                
                # Create a fully configured FallbackManager with proper error handling
                try:
                    fallback_manager = FallbackManager(providers)
                    logger.info("Successfully created FallbackManager with OpenAI and Anthropic providers")
                    
                    # Create LLMWithChainOfThought service with the FallbackManager
                    llm_service = LLMWithChainOfThought(fallback_manager)
                    logger.info("Successfully created LLMWithChainOfThought service")
                    
                except Exception as e:
                    logger.error(f"Error initializing FallbackManager: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise e
                
                # Execute with reasoning and fallback support
                result = await llm_service._execute_llm_with_reasoning(
                    prompt=cot_prompt,
                    report=self.report,
                    with_chain_of_thought=True,
                    confidence_threshold=0.8
                )
                
                # Process and structure the result
                enhanced_analysis = self._process_cot_result(result)
                return enhanced_analysis
                
            except Exception as e:
                logger.error(f"Error using OnSide LLMWithChainOfThought: {str(e)}")
                logger.error(traceback.format_exc())
                # Fallback to API-only implementation
        
        # If OnSide core is not available or fails, use API-only implementation
        return await self._generate_analysis_api_only(company_data)

    async def generate_content_pillars_analysis(self, company_data: Dict[str, Any], market_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate content pillars and taxonomy structure analysis following KPMG-style
        framework with hierarchical classification and strategic weighting.
        
        Args:
            company_data: Company information including industry and focus areas
            market_data: Optional market data for context
            
        Returns:
            Structured content pillars analysis with confidence scores
        """
        logger.info(f"Generating content pillars analysis for {company_data.get('company', 'TCS')}")
        
        # Construct prompt for content pillars analysis
        prompt = self._construct_content_pillars_prompt(company_data, market_data)
        
        if ONSIDE_CORE_AVAILABLE:
            try:
                # Use OnSide's LLMWithChainOfThought for advanced reasoning
                fallback_manager = FallbackManager([LLMProvider.OPENAI, LLMProvider.ANTHROPIC])
                llm_service = LLMWithChainOfThought(fallback_manager)
                
                result = await llm_service._execute_llm_with_reasoning(
                    prompt=prompt,
                    report=self.report,
                    with_chain_of_thought=True,
                    confidence_threshold=0.85  # Higher confidence for content strategy
                )
                
                return self._process_cot_result(result)
            except Exception as e:
                logger.error(f"Error generating content pillars analysis: {str(e)}")
                logger.error(traceback.format_exc())
        
        # Fallback implementation
        return await self._generate_content_pillars_api_only(company_data, market_data)
    
    async def generate_engagement_index_analysis(self, company_data: Dict[str, Any], competitor_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate engagement index analysis that quantifies topic engagement intensity,
        format effectiveness, and channel performance with competitive benchmarking.
        
        Args:
            company_data: Company information
            competitor_data: List of competitor information
            
        Returns:
            Engagement index analysis with benchmarks and opportunity gaps
        """
        logger.info(f"Generating engagement index analysis for {company_data.get('company', 'TCS')}")
        
        # Construct prompt for engagement index analysis
        prompt = self._construct_engagement_index_prompt(company_data, competitor_data)
        
        if ONSIDE_CORE_AVAILABLE:
            try:
                # Use OnSide's LLMWithChainOfThought for advanced reasoning
                fallback_manager = FallbackManager([LLMProvider.OPENAI, LLMProvider.ANTHROPIC])
                llm_service = LLMWithChainOfThought(fallback_manager)
                
                result = await llm_service._execute_llm_with_reasoning(
                    prompt=prompt,
                    report=self.report,
                    with_chain_of_thought=True
                )
                
                return self._process_cot_result(result)
            except Exception as e:
                logger.error(f"Error generating engagement index analysis: {str(e)}")
                logger.error(traceback.format_exc())
        
        # Fallback implementation
        return await self._generate_engagement_index_api_only(company_data, competitor_data)
    
    async def generate_opportunity_index(self, company_data: Dict[str, Any], search_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate opportunity index that identifies high-value market segments,
        content gaps, and white space opportunities based on search volume data.
        
        Args:
            company_data: Company information
            search_data: Search volume data from SERPAPI or similar source
            
        Returns:
            Opportunity index with high-value segments, content gaps, and white space map
        """
        logger.info(f"Generating opportunity index analysis for {company_data.get('company', 'TCS')}")
        
        # Construct prompt for opportunity index analysis
        prompt = self._construct_opportunity_index_prompt(company_data, search_data)
        
        if ONSIDE_CORE_AVAILABLE:
            try:
                # Use OnSide's LLMWithChainOfThought for advanced reasoning
                fallback_manager = FallbackManager([LLMProvider.OPENAI, LLMProvider.ANTHROPIC])
                llm_service = LLMWithChainOfThought(fallback_manager)
                
                result = await llm_service._execute_llm_with_reasoning(
                    prompt=prompt,
                    report=self.report,
                    with_chain_of_thought=True
                )
                
                return self._process_cot_result(result)
            except Exception as e:
                logger.error(f"Error generating opportunity index analysis: {str(e)}")
                logger.error(traceback.format_exc())
        
        # Fallback implementation
        return await self._generate_opportunity_index_api_only(company_data, search_data)
    
    async def generate_audience_segmentation(self, company_data: Dict[str, Any], industry_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate audience segmentation and conversion analysis with detailed user personas,
        journey mapping, and conversion funnel metrics.
        
        Args:
            company_data: Company information
            industry_data: Industry-specific data for context
            
        Returns:
            Audience analysis with personas, user journey, and conversion funnel
        """
        logger.info(f"Generating audience segmentation analysis for {company_data.get('company', 'TCS')}")
        
        # Construct prompt for audience segmentation analysis
        prompt = self._construct_audience_segmentation_prompt(company_data, industry_data)
        
        if ONSIDE_CORE_AVAILABLE:
            try:
                # Use OnSide's LLMWithChainOfThought for advanced reasoning
                fallback_manager = FallbackManager([LLMProvider.OPENAI, LLMProvider.ANTHROPIC])
                llm_service = LLMWithChainOfThought(fallback_manager)
                
                result = await llm_service._execute_llm_with_reasoning(
                    prompt=prompt,
                    report=self.report,
                    with_chain_of_thought=True
                )
                
                return self._process_cot_result(result)
            except Exception as e:
                logger.error(f"Error generating audience segmentation analysis: {str(e)}")
                logger.error(traceback.format_exc())
        
        # Fallback implementation
        return await self._generate_audience_segmentation_api_only(company_data, industry_data)
    
    async def generate_strategic_recommendations(self, integrated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate strategic recommendations based on integrated analysis data,
        including content strategy, competitive strategy, and decision tables.
        
        Args:
            integrated_data: Integrated analysis data from all previous analyses
            
        Returns:
            Strategic recommendations with rationale, impact assessment, and implementation guidance
        """
        logger.info("Generating strategic recommendations with decision tables")
        
        # Construct prompt for strategic recommendations
        prompt = self._construct_strategic_recommendations_prompt(integrated_data)
        
        if ONSIDE_CORE_AVAILABLE:
            try:
                # Use OnSide's LLMWithChainOfThought for advanced reasoning
                fallback_manager = FallbackManager([LLMProvider.OPENAI, LLMProvider.ANTHROPIC])
                llm_service = LLMWithChainOfThought(fallback_manager)
                
                result = await llm_service._execute_llm_with_reasoning(
                    prompt=prompt,
                    report=self.report,
                    with_chain_of_thought=True,
                    confidence_threshold=0.9  # Higher threshold for recommendations
                )
                
                return self._process_cot_result(result)
            except Exception as e:
                logger.error(f"Error generating strategic recommendations: {str(e)}")
                logger.error(traceback.format_exc())
        
        # Fallback implementation
        return await self._generate_strategic_recommendations_api_only(integrated_data)
    
    async def generate_comprehensive_analysis(self, company_data: Dict[str, Any], api_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive analysis combining all analytical components for
        an integrated KPMG-level report.
        
        Args:
            company_data: Company information
            api_data: Data from various API sources
            
        Returns:
            Complete integrated analysis with all components
        """
        logger.info(f"Generating comprehensive KPMG-style analysis for {company_data.get('company', 'TCS')}")
        
        # Run all analyses in parallel for efficiency
        competitor_analysis_task = asyncio.create_task(
            self.generate_competitor_analysis_with_cot(company_data)
        )
        
        content_pillars_task = asyncio.create_task(
            self.generate_content_pillars_analysis(company_data, api_data.get('market_data'))
        )
        
        engagement_index_task = asyncio.create_task(
            self.generate_engagement_index_analysis(company_data, api_data.get('competitor_data'))
        )
        
        opportunity_index_task = asyncio.create_task(
            self.generate_opportunity_index(company_data, api_data.get('search_data'))
        )
        
        audience_analysis_task = asyncio.create_task(
            self.generate_audience_segmentation(company_data, api_data.get('industry_data'))
        )
        
        # Wait for all analyses to complete
        competitor_analysis = await competitor_analysis_task
        content_pillars = await content_pillars_task
        engagement_index = await engagement_index_task
        opportunity_index = await opportunity_index_task
        audience_analysis = await audience_analysis_task
        
        # Integrate all analyses
        integrated_data = {
            "competitor_analysis": competitor_analysis.get("content", {}),
            "content_pillars": content_pillars.get("content", {}).get("content_pillars", []),
            "engagement_index": engagement_index.get("content", {}).get("engagement_index", {}),
            "opportunity_index": opportunity_index.get("content", {}).get("opportunity_index", {}),
            "audience_analysis": audience_analysis.get("content", {}).get("audience_analysis", {}),
            "api_data": api_data
        }
        
        # Generate strategic recommendations based on integrated data
        strategic_recommendations = await self.generate_strategic_recommendations(integrated_data)
        
        # Combine everything into a comprehensive analysis
        comprehensive_analysis = {
            "success": True,
            "company_name": company_data.get("company", "Tata Consultancy Services"),
            "analysis_timestamp": datetime.now(UTC).isoformat(),
            "competitor_analysis": competitor_analysis.get("content", {}),
            "content_pillars": content_pillars.get("content", {}).get("content_pillars", []),
            "engagement_index": engagement_index.get("content", {}).get("engagement_index", {}),
            "opportunity_index": opportunity_index.get("content", {}).get("opportunity_index", {}),
            "audience_analysis": audience_analysis.get("content", {}).get("audience_analysis", {}),
            "strategic_recommendations": strategic_recommendations.get("content", {}).get("strategic_recommendations", {}),
            "confidence_metrics": {
                "data_quality": self._calculate_data_quality_score(api_data),
                "analytical_confidence": self._calculate_analytical_confidence([
                    competitor_analysis, content_pillars, engagement_index,
                    opportunity_index, audience_analysis, strategic_recommendations
                ]),
                "recommendation_confidence": strategic_recommendations.get("content", {}).get("confidence_metrics", {}).get("recommendation_confidence", 0.75),
                "overall_confidence": self._calculate_overall_confidence([
                    competitor_analysis, content_pillars, engagement_index,
                    opportunity_index, audience_analysis, strategic_recommendations
                ])
            },
            "reasoning_chains": {
                "competitor_analysis": competitor_analysis.get("reasoning_chains", {}),
                "content_pillars": content_pillars.get("content", {}).get("reasoning_process", {}),
                "engagement_index": engagement_index.get("content", {}).get("reasoning_process", {}),
                "opportunity_index": opportunity_index.get("content", {}).get("reasoning_process", {}),
                "audience_analysis": audience_analysis.get("content", {}).get("reasoning_process", {}),
                "strategic_recommendations": strategic_recommendations.get("content", {}).get("reasoning_process", {})
            },
            "metadata": {
                "api_sources_used": list(api_data.keys()),
                "llm_providers_used": self._get_llm_providers_used([
                    competitor_analysis, content_pillars, engagement_index,
                    opportunity_index, audience_analysis, strategic_recommendations
                ]),
                "timestamp": datetime.now(UTC).isoformat()
            }
        }
        
        return comprehensive_analysis
    
    def _construct_competitor_cot_prompt(self, company_data: Dict[str, Any]) -> str:
        """
        Construct an advanced prompt for chain-of-thought competitor analysis following
        KPMG-style reporting standards with enhanced data structure and analytical methods.
        
        Args:
            company_data: Basic company information
            
        Returns:
            Enhanced prompt for LLM with structured data requirements
        """
        company_name = company_data.get("company", "Tata Consultancy Services")
        domain = company_data.get("domain", "tcs.com")
        industry = company_data.get("industry", "IT Services")
        
        # Check if this prompt is already in cache
        cache_key = f"competitor_cot_{company_name}"
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        # Construct enhanced KPMG-style prompt with advanced analytics
        prompt = f"""
        # Advanced Enterprise Competitive Analysis with Multi-layered Reasoning
        
        ## Subject Entity
        - Company: {company_name}
        - Domain: {domain}
        - Primary Industry: {industry}
        
        ## Analysis Requirements
        Perform a comprehensive competitive analysis using a hierarchical analytical framework
        that demonstrates advanced reasoning capabilities with confidence scoring.
        
        ### 1. Content Pillars & Taxonomy Structure
        Identify and analyze {company_name}'s strategic content pillars by examining:
        - Core business segments and service offerings
        - Market positioning pillars (value, innovation, expertise)
        - Content taxonomy with strategic weighting
        
        For each content pillar, provide:
        - Name and description
        - Sub-pillars with categorical breakdown
        - Strategic priority level (High/Medium/Low)
        - Content type classification (Evergreen/Timely/Tactical)
        - Content weighting percentage (importance to overall strategy)
        
        ### 2. Engagement Index Analysis
        Create a detailed engagement index that measures:
        - Topic engagement intensity (0-100) compared to competitors
        - Format effectiveness metrics across content types
        - Channel performance indicators
        - Conversion potential scoring
        
        ### 3. Market Position & Competitive Matrix
        Construct a multi-dimensional competitive analysis including:
        - Share-of-voice metrics in key industry segments
        - Comparative strengths and weaknesses matrix
        - Strategic positioning relative to 5 major competitors
        - Innovation index and future trajectory assessment
        
        ### 4. Search Volume & Opportunity Index
        Develop an opportunity index framework that identifies:
        - High-value market segments based on search volume
        - Content gaps relative to search demand
        - White space opportunity mapping
        - Competitive saturation levels by topic area
        
        ### 5. Audience Segmentation & Conversion Analysis
        Create an advanced audience analysis with:
        - Detailed user personas by industry role
        - Journey mapping across the conversion funnel
        - Content targeting logic by audience segment
        - Engagement triggers and conversion pathway analysis
        
        ### 6. Strategic Recommendations
        Generate data-driven recommendations based on all analyses above, including:
        - Content strategy optimization guidance
        - Channel prioritization framework
        - Format diversification strategy
        - Competitive differentiation tactics
        - Opportunity sizing and prioritization
        
        ## Output Format
        Structure your response as a valid JSON object following this exact schema:
        
        ```json
        {{
          "content_pillars": [
            {{
              "pillar": "[Pillar Name]",
              "description": "[Brief description of this strategic pillar]",
              "sub_pillars": [
                "[Sub-pillar 1]",
                "[Sub-pillar 2]"
              ],
              "priority": "High/Medium/Low",
              "content_type": "Evergreen/Timely/Tactical",
              "content_weighting": [0-100]
            }}
          ],
          "engagement_index": {{
            "topics": [
              {{
                "name": "[Topic Name]",
                "engagement_score": [0-100],
                "competitor_average": [0-100],
                "opportunity_gap": [Difference between scores]
              }}
            ],
            "formats": [
              {{
                "format": "[Format Name]",
                "effectiveness": [0-100],
                "industry_benchmark": [0-100]
              }}
            ],
            "overall_engagement_rating": "[Rating with justification]"
          }},
          "competitive_matrix": {{
            "positioning": "[Overall positioning statement]",
            "share_of_voice": [0-100],
            "competitors": [
              {{
                "name": "[Competitor Name]",
                "share_of_voice": [0-100],
                "strengths": [
                  {{
                    "area": "[Strength Area]",
                    "description": "[Description]",
                    "comparative_rating": [0-100]
                  }}
                ],
                "weaknesses": [
                  {{
                    "area": "[Weakness Area]",
                    "description": "[Description]",
                    "comparative_rating": [0-100]
                  }}
                ],
                "threat_level": "High/Medium/Low",
                "opportunity_areas": ["[Area 1]", "[Area 2]"],
                "relationship_type": "Direct/Indirect/Potential Competitor"
              }}
            ]
          }},
          "opportunity_index": {{
            "high_value_segments": [
              {{
                "segment": "[Segment Name]",
                "search_volume": [Numerical value],
                "current_coverage": [0-100],
                "opportunity_score": [0-100],
                "recommendation": "[Specific recommendation]"
              }}
            ],
            "content_gaps": [
              {{
                "topic": "[Topic with Gap]",
                "gap_severity": [0-100],
                "competitor_coverage": [0-100],
                "priority_level": "High/Medium/Low"
              }}
            ],
            "white_space_map": "[Description of untapped market areas]"
          }},
          "audience_analysis": {{
            "personas": [
              {{
                "role": "[Job Role/Persona]",
                "needs": ["[Need 1]", "[Need 2]"],
                "pain_points": ["[Pain Point 1]", "[Pain Point 2]"],
                "content_preferences": ["[Preference 1]", "[Preference 2]"],
                "conversion_triggers": ["[Trigger 1]", "[Trigger 2]"]
              }}
            ],
            "user_journey": [
              {{
                "stage": "Awareness/Consideration/Conversion/Retention",
                "content_types": ["[Content Type 1]", "[Content Type 2]"],
                "channels": ["[Channel 1]", "[Channel 2]"],
                "key_metrics": ["[Metric 1]", "[Metric 2]"]
              }}
            ],
            "conversion_funnel": {{
              "top_funnel_rate": [0-100],
              "mid_funnel_rate": [0-100],
              "bottom_funnel_rate": [0-100],
              "overall_conversion": [0-100],
              "industry_benchmark": [0-100]
            }}
          }},
          "strategic_recommendations": {{
            "content_strategy": [
              {{
                "recommendation": "[Specific recommendation]",
                "rationale": "[Data-driven justification]",
                "implementation_complexity": "High/Medium/Low",
                "expected_impact": "High/Medium/Low",
                "priority": [0-100]
              }}
            ],
            "competitive_strategy": [
              {{
                "recommendation": "[Specific recommendation]",
                "target_competitors": ["[Competitor 1]", "[Competitor 2]"],
                "opportunity_size": "Large/Medium/Small",
                "implementation_timeline": "Short/Medium/Long-term"
              }}
            ],
            "decision_tables": [
              {{
                "decision_area": "[Area of Decision]",
                "recommendation": "[Recommended Action]",
                "alternatives": ["[Alternative 1]", "[Alternative 2]"],
                "justification": "[Justification for recommendation]"
              }}
            ]
          }},
          "reasoning_process": {{
            "content_pillar_analysis": "[Detailed reasoning about content pillars]",
            "engagement_index_methodology": "[Explanation of engagement calculations]",
            "opportunity_assessment_approach": "[Method for identifying opportunities]",
            "competitive_matrix_development": "[Process for comparative analysis]",
            "strategic_recommendation_logic": "[Decision framework for recommendations]"
          }},
          "confidence_metrics": {{
            "data_quality": [0-100],
            "analytical_confidence": [0-100],
            "recommendation_confidence": [0-100],
            "overall_confidence": [0-100]
          }}
        }}
        ```
        
        Please provide comprehensive analysis with quantitative metrics wherever possible.
        All scoring should be data-driven with clear reasoning.
        Ensure your response meets enterprise-grade standards for strategic competitive analysis.
        """
        
        # Cache the prompt
        self._prompt_cache[cache_key] = prompt
        return prompt
    
    def _process_cot_result(self, llm_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the result from LLM chain-of-thought reasoning.
        
        Args:
            llm_result: Raw result from LLM service
            
        Returns:
            Enhanced result with confidence and reasoning metadata
        """
        logger.info("Processing LLM chain-of-thought result")
        
        try:
            content = llm_result.get("content", "{}")
            metadata = llm_result.get("metadata", {})
            
            if isinstance(content, str):
                try:
                    parsed_content = json.loads(content)
                except json.JSONDecodeError:
                    # Extract JSON from text if not valid JSON
                    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    if json_match:
                        try:
                            parsed_content = json.loads(json_match.group(1))
                        except:
                            parsed_content = {}
                    else:
                        parsed_content = {}
            else:
                parsed_content = content
            
            # Add reasoning metadata
            enhanced_result = {
                "success": True,
                "provider": llm_result.get("provider", "AI Service"),
                "model": llm_result.get("model", "Unknown"),
                "content": parsed_content,
                "reasoning_chains": parsed_content.get("reasoning_process", {}),
                "overall_confidence": parsed_content.get("overall_confidence", 0.75),
                "metadata": {
                    "finish_reason": metadata.get("finish_reason", "unknown"),
                    "tokens": metadata.get("tokens", 0),
                    "confidence_threshold": 0.8,
                    "reasoning_enabled": True,
                    "fallback_triggered": llm_result.get("fallback_triggered", False),
                    "timestamp": datetime.now(UTC).isoformat()
                }
            }
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error processing LLM result: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return a minimal valid result on error
            return {
                "success": False,
                "error": str(e),
                "provider": llm_result.get("provider", "AI Service"),
                "content": {},
                "overall_confidence": 0.0,
                "metadata": {
                    "error": str(e),
                    "timestamp": datetime.now(UTC).isoformat()
                }
            }
    
    def _construct_content_pillars_prompt(self, company_data: Dict[str, Any], market_data: Dict[str, Any] = None) -> str:
        """
        Construct a prompt for content pillars and taxonomy structure analysis following KPMG-style reporting.
        
        Args:
            company_data: Company information including industry and focus areas
            market_data: Optional market data for context
            
        Returns:
            Prompt for LLM to generate content pillars analysis
        """
        company_name = company_data.get("company", "Tata Consultancy Services")
        domain = company_data.get("domain", "tcs.com")
        industry = company_data.get("industry", "IT Services")
        
        # Check if this prompt is already in cache
        cache_key = f"content_pillars_{company_name}"
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        # Construct prompt for content pillars analysis
        prompt = f"""
        # Content Pillars & Taxonomy Structure Analysis
        
        ## Subject Entity
        - Company: {company_name}
        - Domain: {domain}
        - Primary Industry: {industry}
        
        ## Analysis Requirements
        Perform a comprehensive content pillar analysis to identify and categorize {company_name}'s
        strategic content taxonomy and information architecture. This analysis should identify
        the underlying structure of their content strategy and how it supports business goals.
        
        ### Core Analysis Tasks
        1. Identify 4-6 primary content pillars that form the foundation of {company_name}'s strategy
        2. For each pillar, determine sub-pillars and categorical breakdown
        3. Assign strategic priority level (High/Medium/Low) to each pillar
        4. Classify content as Evergreen (always relevant), Timely (seasonal/trend-based), or Tactical (campaign-specific)
        5. Determine content weighting percentage (importance to overall strategy)
        
        ### Focus Areas
        - Core business segments and service offerings
        - Market positioning pillars (value, innovation, expertise)
        - Content taxonomy with strategic weighting
        - Industry leadership topics
        - Technical capabilities and solutions
        
        ## Output Format
        Structure your response as a valid JSON object following this exact schema:
        
        ```json
        {{
          "content_pillars": [
            {{
              "pillar": "[Pillar Name]",
              "description": "[Brief description of this strategic pillar]",
              "sub_pillars": [
                "[Sub-pillar 1]",
                "[Sub-pillar 2]"
              ],
              "priority": "High/Medium/Low",
              "content_type": "Evergreen/Timely/Tactical",
              "content_weighting": [0-100]
            }}
          ],
          "reasoning_process": {{
            "content_pillar_analysis": "[Detailed reasoning about content pillars]",
            "taxonomic_structure_logic": "[Explanation of taxonomy development]"
          }},
          "confidence_metrics": {{
            "data_quality": [0-100],
            "analytical_confidence": [0-100],
            "overall_confidence": [0-100]
          }}
        }}
        ```
        
        Please provide a comprehensive analysis with quantitative metrics wherever possible.
        All scoring should be data-driven with clear reasoning.
        """
        
        # Cache the prompt
        self._prompt_cache[cache_key] = prompt
        return prompt
    
    def _construct_engagement_index_prompt(self, company_data: Dict[str, Any], competitor_data: List[Dict[str, Any]] = None) -> str:
        """
        Construct a prompt for engagement index analysis that measures topic engagement
        intensity, format effectiveness, and channel performance with competitive benchmarking.
        
        Args:
            company_data: Company information
            competitor_data: Optional list of competitor information for benchmarking
            
        Returns:
            Prompt for LLM to generate engagement index analysis
        """
        company_name = company_data.get("company", "Tata Consultancy Services")
        domain = company_data.get("domain", "tcs.com")
        industry = company_data.get("industry", "IT Services")
        
        # Check if this prompt is already in cache
        cache_key = f"engagement_index_{company_name}"
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        # Prepare competitor names for prompt
        competitor_names = []
        if competitor_data:
            competitor_names = [comp.get("company", f"Competitor {i+1}") for i, comp in enumerate(competitor_data)]
        else:
            competitor_names = ["Infosys", "Wipro", "Accenture", "IBM", "Cognizant"]
        
        competitors_str = ", ".join(competitor_names[:5])  # Limit to 5 competitors
        
        # Construct prompt for engagement index analysis
        prompt = f"""
        # Engagement Index Analysis
        
        ## Subject Entity
        - Company: {company_name}
        - Domain: {domain}
        - Primary Industry: {industry}
        - Key Competitors: {competitors_str}
        
        ## Analysis Requirements
        Create a detailed engagement index that measures how {company_name} performs across
        different topics, content formats, and channels compared to competitors. This analysis
        should quantify engagement effectiveness and identify opportunity gaps.
        
        ### Core Analysis Tasks
        1. Evaluate topic engagement intensity (0-100) for key industry topics
        2. Assess format effectiveness metrics across content types
        3. Analyze channel performance indicators
        4. Calculate opportunity gaps compared to competitors
        5. Provide an overall engagement effectiveness rating
        
        ### Topics to Analyze
        - Digital Transformation
        - Cloud Services
        - Artificial Intelligence/Machine Learning
        - Cybersecurity
        - Business Process Optimization
        - Enterprise Solutions
        - Industry-Specific Offerings
        - Innovation & Research
        
        ### Formats to Assess
        - White Papers/Research Reports
        - Case Studies
        - Blog Posts
        - Webinars/Virtual Events
        - Video Content
        - Interactive Tools
        - Social Media Posts
        - Podcasts
        
        ## Output Format
        Structure your response as a valid JSON object following this exact schema:
        
        ```json
        {{
          "engagement_index": {{
            "topics": [
              {{
                "name": "[Topic Name]",
                "engagement_score": [0-100],
                "competitor_average": [0-100],
                "opportunity_gap": [Difference between scores]
              }}
            ],
            "formats": [
              {{
                "format": "[Format Name]",
                "effectiveness": [0-100],
                "industry_benchmark": [0-100]
              }}
            ],
            "channels": [
              {{
                "channel": "[Channel Name]",
                "performance_score": [0-100],
                "competitive_position": "Leader/Strong/Average/Below Average"
              }}
            ],
            "overall_engagement_rating": "[Rating with justification]"
          }},
          "reasoning_process": {{
            "engagement_metrics_methodology": "[Detailed explanation of how engagement scores were calculated]",
            "comparative_analysis_approach": "[Process for benchmarking against competitors]",
            "opportunity_identification_logic": "[Method for identifying gaps and opportunities]"
          }},
          "confidence_metrics": {{
            "data_quality": [0-100],
            "comparative_accuracy": [0-100],
            "overall_confidence": [0-100]
          }}
        }}
        ```
        
        Please provide a comprehensive analysis with quantitative metrics wherever possible.
        All scoring should be data-driven with clear reasoning.
        """
        
        # Cache the prompt
        self._prompt_cache[cache_key] = prompt
        return prompt
    
    def _construct_opportunity_index_prompt(self, company_data: Dict[str, Any], search_data: Dict[str, Any] = None) -> str:
        """
        Construct a prompt for opportunity index analysis that identifies high-value market segments,
        content gaps, and white space opportunities based on search volume data.
        
        Args:
            company_data: Company information
            search_data: Optional search volume data from SERPAPI or similar source
            
        Returns:
            Prompt for LLM to generate opportunity index analysis
        """
        company_name = company_data.get("company", "Tata Consultancy Services")
        domain = company_data.get("domain", "tcs.com")
        industry = company_data.get("industry", "IT Services")
        
        # Check if this prompt is already in cache
        cache_key = f"opportunity_index_{company_name}"
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        # Process search data if available
        search_trends = ""
        if search_data and isinstance(search_data, dict):
            trend_items = []
            for topic, volume in search_data.items()[:5]:  # Just use top 5 topics if available
                trend_items.append(f"{topic}: {volume} monthly searches")
            if trend_items:
                search_trends = "\n        - " + "\n        - ".join(trend_items)
        
        # Construct prompt for opportunity index analysis
        prompt = f"""
        # Search Volume & Opportunity Index Analysis
        
        ## Subject Entity
        - Company: {company_name}
        - Domain: {domain}
        - Primary Industry: {industry}
        
        ## Search Trends{search_trends}
        
        ## Analysis Requirements
        Develop an opportunity index framework that identifies high-value market segments,
        content gaps, and white space opportunities for {company_name} based on search volume
        data and competitive saturation levels.
        
        ### Core Analysis Tasks
        1. Identify high-value market segments based on search volume and business relevance
        2. Analyze content gaps relative to search demand
        3. Create a white space opportunity map for underserved areas
        4. Assess competitive saturation levels by topic area
        5. Recommend priority areas based on opportunity size and competitive position
        
        ### Focus Areas
        - Industry-specific IT solutions
        - Digital transformation services
        - Cloud migration and management
        - Business process optimization
        - Cybersecurity services
        - Emerging technology implementation
        - Industry-specific compliance solutions
        - Enterprise software implementation
        
        ## Output Format
        Structure your response as a valid JSON object following this exact schema:
        
        ```json
        {{
          "opportunity_index": {{
            "high_value_segments": [
              {{
                "segment": "[Segment Name]",
                "search_volume": [Numerical value],
                "current_coverage": [0-100],
                "opportunity_score": [0-100],
                "recommendation": "[Specific recommendation]"
              }}
            ],
            "content_gaps": [
              {{
                "topic": "[Topic with Gap]",
                "gap_severity": [0-100],
                "competitor_coverage": [0-100],
                "priority_level": "High/Medium/Low"
              }}
            ],
            "white_space_map": "[Description of untapped market areas]",
            "competitive_saturation": [
              {{
                "area": "[Topic Area]",
                "saturation_level": [0-100],
                "difficulty_to_compete": [0-100],
                "opportunity_despite_saturation": [0-100]
              }}
            ]
          }},
          "reasoning_process": {{
            "opportunity_assessment_approach": "[Method for identifying opportunities]",
            "search_volume_analysis": "[Process for evaluating search trends]",
            "gap_identification_method": "[How content gaps were determined]"
          }},
          "confidence_metrics": {{
            "data_quality": [0-100],
            "opportunity_sizing_confidence": [0-100],
            "overall_confidence": [0-100]
          }}
        }}
        ```
        
        Please provide a comprehensive analysis with quantitative metrics wherever possible.
        All scoring should be data-driven with clear reasoning.
        """
        
        # Cache the prompt
        self._prompt_cache[cache_key] = prompt
        return prompt
    
    def _construct_audience_segmentation_prompt(self, company_data: Dict[str, Any], industry_data: Dict[str, Any] = None) -> str:
        """
        Construct a prompt for audience segmentation and conversion analysis with detailed
        user personas, journey mapping, and conversion funnel metrics.
        
        Args:
            company_data: Company information
            industry_data: Optional industry-specific data for context
            
        Returns:
            Prompt for LLM to generate audience segmentation analysis
        """
        company_name = company_data.get("company", "Tata Consultancy Services")
        domain = company_data.get("domain", "tcs.com")
        industry = company_data.get("industry", "IT Services")
        
        # Check if this prompt is already in cache
        cache_key = f"audience_segmentation_{company_name}"
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        # Construct prompt for audience segmentation analysis
        prompt = f"""
        # Audience Segmentation & Conversion Analysis
        
        ## Subject Entity
        - Company: {company_name}
        - Domain: {domain}
        - Primary Industry: {industry}
        
        ## Analysis Requirements
        Create an advanced audience segmentation analysis for {company_name} with detailed
        user personas, journey mapping across the conversion funnel, content targeting logic,
        and engagement trigger identification. This analysis should help optimize content
        strategy and conversion pathways for different audience segments.
        
        ### Core Analysis Tasks
        1. Develop detailed user personas for key audience segments
        2. Map user journeys across awareness, consideration, conversion, and retention stages
        3. Identify content targeting logic and preferences by audience segment
        4. Analyze conversion triggers and pathway optimization
        5. Calculate conversion funnel metrics at each stage
        
        ### Key Audience Segments to Consider
        - Enterprise IT Decision Makers
        - C-Suite Executives
        - Technology Implementation Managers
        - Industry-specific Stakeholders
        - Procurement Specialists
        - Digital Transformation Leaders
        
        ## Output Format
        Structure your response as a valid JSON object following this exact schema:
        
        ```json
        {{
          "audience_analysis": {{
            "personas": [
              {{
                "role": "[Job Role/Persona]",
                "needs": ["[Need 1]", "[Need 2]"],
                "pain_points": ["[Pain Point 1]", "[Pain Point 2]"],
                "content_preferences": ["[Preference 1]", "[Preference 2]"],
                "conversion_triggers": ["[Trigger 1]", "[Trigger 2]"]
              }}
            ],
            "user_journey": [
              {{
                "stage": "Awareness/Consideration/Conversion/Retention",
                "content_types": ["[Content Type 1]", "[Content Type 2]"],
                "channels": ["[Channel 1]", "[Channel 2]"],
                "key_metrics": ["[Metric 1]", "[Metric 2]"]
              }}
            ],
            "conversion_funnel": {{
              "top_funnel_rate": [0-100],
              "mid_funnel_rate": [0-100],
              "bottom_funnel_rate": [0-100],
              "overall_conversion": [0-100],
              "industry_benchmark": [0-100]
            }},
            "content_targeting_matrix": [
              {{
                "segment": "[Audience Segment]",
                "top_content_formats": ["[Format 1]", "[Format 2]"],
                "preferred_channels": ["[Channel 1]", "[Channel 2]"],
                "messaging_themes": ["[Theme 1]", "[Theme 2]"]
              }}
            ]
          }},
          "reasoning_process": {{
            "persona_development_methodology": "[Method for creating personas]",
            "journey_mapping_approach": "[Approach to mapping the user journey]",
            "conversion_analysis_technique": "[Technique for analyzing conversion paths]"
          }},
          "confidence_metrics": {{
            "persona_accuracy": [0-100],
            "journey_map_confidence": [0-100],
            "conversion_data_quality": [0-100],
            "overall_confidence": [0-100]
          }}
        }}
        ```
        
        Please provide a comprehensive analysis with quantitative metrics wherever possible.
        All scoring should be data-driven with clear reasoning.
        """
        
        # Cache the prompt
        self._prompt_cache[cache_key] = prompt
        return prompt
    
    def _construct_strategic_recommendations_prompt(self, integrated_data: Dict[str, Any]) -> str:
        """
        Construct a prompt for strategic recommendations based on integrated analysis data,
        including content strategy, competitive strategy, and decision tables.
        
        Args:
            integrated_data: Integrated analysis data from all previous analyses
            
        Returns:
            Prompt for LLM to generate strategic recommendations
        """
        # Extract company information from integrated data
        company_name = integrated_data.get("company_name", "Tata Consultancy Services")
        
        # Check if this prompt is already in cache
        cache_key = f"strategic_recommendations_{company_name}"
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        # Prepare summary of integrated data for context
        strengths = ""
        if "competitor_analysis" in integrated_data and "strengths" in integrated_data["competitor_analysis"]:
            strength_items = []
            for strength in integrated_data["competitor_analysis"]["strengths"][:3]:  # Top 3 strengths
                if isinstance(strength, dict) and "strength" in strength:
                    strength_items.append(strength["strength"])
                elif isinstance(strength, str):
                    strength_items.append(strength)
            if strength_items:
                strengths = "\n        - " + "\n        - ".join(strength_items)
                
        # Extract content pillars if available
        content_pillars = ""
        if "content_pillars" in integrated_data:
            pillar_items = []
            for pillar in integrated_data["content_pillars"][:3]:  # Top 3 pillars
                if isinstance(pillar, dict) and "pillar" in pillar:
                    pillar_items.append(pillar["pillar"])
                elif isinstance(pillar, str):
                    pillar_items.append(pillar)
            if pillar_items:
                content_pillars = "\n        - " + "\n        - ".join(pillar_items)
        
        # Extract opportunity segments if available
        opportunity_segments = ""
        if "opportunity_index" in integrated_data and "high_value_segments" in integrated_data["opportunity_index"]:
            segment_items = []
            for segment in integrated_data["opportunity_index"]["high_value_segments"][:3]:  # Top 3 segments
                if isinstance(segment, dict) and "segment" in segment:
                    segment_items.append(segment["segment"])
                elif isinstance(segment, str):
                    segment_items.append(segment)
            if segment_items:
                opportunity_segments = "\n        - " + "\n        - ".join(segment_items)
        
        # Construct prompt for strategic recommendations
        prompt = f"""
        # Strategic Recommendations Analysis
        
        ## Subject Entity
        - Company: {company_name}
        
        ## Analysis Summary
        Based on the comprehensive analysis of {company_name}, I need you to develop data-driven
        strategic recommendations that integrate insights from competitive analysis, content pillar
        structure, engagement metrics, opportunity identification, and audience segmentation.
        
        ### Key Strengths{strengths}
        
        ### Content Pillars{content_pillars}
        
        ### High-Value Opportunity Segments{opportunity_segments}
        
        ## Recommendation Requirements
        Develop comprehensive strategic recommendations for {company_name} across the following areas:
        
        1. Content Strategy
           - Content pillar optimization
           - Format diversification
           - Topic prioritization
           - Content gap remediation
        
        2. Competitive Strategy
           - Differentiation tactics
           - Market positioning enhancement
           - Threat mitigation
           - Opportunity leverage against competitors
        
        3. Channel Strategy
           - Channel prioritization
           - Cross-channel integration
           - Channel-specific content optimization
        
        4. Audience Engagement Strategy
           - Persona-targeted content approach
           - Conversion pathway optimization
           - Engagement trigger implementation
        
        5. Strategic Decision Tables
           - Priority matrices for implementation
           - Resource allocation guidance
           - Timeline recommendations
           - Expected impact assessments
        
        ## Output Format
        Structure your response as a valid JSON object following this exact schema:
        
        ```json
        {{
          "strategic_recommendations": {{
            "content_strategy": [
              {{
                "recommendation": "[Specific recommendation]",
                "rationale": "[Data-driven justification]",
                "implementation_complexity": "High/Medium/Low",
                "expected_impact": "High/Medium/Low",
                "priority": [0-100]
              }}
            ],
            "competitive_strategy": [
              {{
                "recommendation": "[Specific recommendation]",
                "target_competitors": ["[Competitor 1]", "[Competitor 2]"],
                "opportunity_size": "Large/Medium/Small",
                "implementation_timeline": "Short/Medium/Long-term"
              }}
            ],
            "channel_strategy": [
              {{
                "channel": "[Channel Name]",
                "recommendation": "[Specific recommendation]",
                "current_performance": [0-100],
                "potential_performance": [0-100],
                "priority": [0-100]
              }}
            ],
            "audience_engagement": [
              {{
                "target_persona": "[Persona Name]",
                "recommendation": "[Specific recommendation]",
                "engagement_tactic": "[Specific tactic]",
                "expected_outcome": "[Specific outcome]"
              }}
            ],
            "decision_tables": [
              {{
                "decision_area": "[Area of Decision]",
                "recommendation": "[Recommended Action]",
                "alternatives": ["[Alternative 1]", "[Alternative 2]"],
                "justification": "[Justification for recommendation]"
              }}
            ],
            "implementation_roadmap": {{
              "immediate_actions": ["[Action 1]", "[Action 2]"],
              "mid_term_actions": ["[Action 1]", "[Action 2]"],
              "long_term_actions": ["[Action 1]", "[Action 2]"],
              "key_milestones": ["[Milestone 1]", "[Milestone 2]"]
            }}
          }},
          "reasoning_process": {{
            "strategic_recommendation_logic": "[Decision framework for recommendations]",
            "prioritization_methodology": "[How priorities were determined]",
            "impact_assessment_approach": "[Method for estimating impact]"
          }},
          "confidence_metrics": {{
            "data_quality": [0-100],
            "recommendation_confidence": [0-100],
            "impact_prediction_confidence": [0-100],
            "overall_confidence": [0-100]
          }}
        }}
        ```
        
        Please provide comprehensive recommendations with clear implementation guidance.
        All recommendations should be data-driven with quantitative metrics where possible.
        """
        
        # Cache the prompt
        self._prompt_cache[cache_key] = prompt
        return prompt
    
    def _calculate_data_quality_score(self, api_data: Dict[str, Any]) -> float:
        """
        Calculate the data quality score based on API data completeness and freshness.
        
        Args:
            api_data: Data from various API sources
            
        Returns:
            Data quality score between 0 and 100
        """
        # Default base score
        base_score = 65.0
        
        if not api_data:
            return base_score
        
        # Count available data sources
        data_source_count = len(api_data.keys())
        
        # Bonus for having more data sources
        if data_source_count >= 5:
            base_score += 20.0
        elif data_source_count >= 3:
            base_score += 15.0
        elif data_source_count >= 1:
            base_score += 10.0
        
        # Check for key data sources
        if "market_data" in api_data:
            base_score += 5.0
        if "competitor_data" in api_data:
            base_score += 5.0
        if "search_data" in api_data:
            base_score += 5.0
        
        # Cap at 100
        return min(base_score, 100.0)
    
    def _calculate_analytical_confidence(self, analysis_results: List[Dict[str, Any]]) -> float:
        """
        Calculate the analytical confidence based on the confidence scores of individual analyses.
        
        Args:
            analysis_results: List of analysis results
            
        Returns:
            Analytical confidence score between 0 and 100
        """
        if not analysis_results:
            return 70.0
        
        # Extract confidence scores from all analyses
        confidence_scores = []
        for result in analysis_results:
            # Try to get overall_confidence directly
            if "overall_confidence" in result:
                score = result["overall_confidence"]  
                if isinstance(score, float) and 0 <= score <= 1: 
                    confidence_scores.append(score * 100)  # Convert 0-1 to 0-100 scale
                elif isinstance(score, (int, float)) and 0 <= score <= 100:
                    confidence_scores.append(score)
            # Try to get from content.confidence_metrics
            elif "content" in result and isinstance(result["content"], dict):
                content = result["content"]
                if "confidence_metrics" in content and "overall_confidence" in content["confidence_metrics"]:
                    score = content["confidence_metrics"]["overall_confidence"]
                    if isinstance(score, (int, float)) and 0 <= score <= 100:
                        confidence_scores.append(score)
        
        # If no valid confidence scores found, use default
        if not confidence_scores:
            return 70.0
        
        # Calculate weighted average based on provider reliability
        return sum(confidence_scores) / len(confidence_scores)
    
    def _calculate_overall_confidence(self, analysis_results: List[Dict[str, Any]]) -> float:
        """
        Calculate the overall confidence score for the comprehensive analysis.
        
        Args:
            analysis_results: List of analysis results
            
        Returns:
            Overall confidence score between 0 and 100
        """
        if not analysis_results:
            return 70.0
            
        # Count successful analyses
        success_count = sum(1 for result in analysis_results if result.get("success", False))
        success_ratio = success_count / len(analysis_results) if analysis_results else 0
        
        # Base confidence starts from analytical confidence
        analytical_confidence = self._calculate_analytical_confidence(analysis_results)
        
        # Adjust based on success ratio
        adjusted_confidence = analytical_confidence * (0.5 + 0.5 * success_ratio)
        
        # Cap at 100
        return min(adjusted_confidence, 100.0)
    
    def _get_llm_providers_used(self, analysis_results: List[Dict[str, Any]]) -> List[str]:
        """
        Get the list of LLM providers used in the analyses.
        
        Args:
            analysis_results: List of analysis results
            
        Returns:
            List of unique LLM provider names
        """
        providers = set()
        for result in analysis_results:
            provider = result.get("provider")
            if provider:
                providers.add(provider)
        
        return list(providers) if providers else ["Unknown"]
    
    async def _generate_analysis_api_only(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI analysis with simulated reasoning chains.
        
        Args:
            company_data: Basic company information
            
        Returns:
            AI analysis with simulated reasoning chains
        """
        logger.info("Using API-only implementation for AI analysis")
        
        # Direct API implementation similar to our original implementation
        # but with enhanced prompting for reasoning chains
        
        company_name = company_data.get("company", "Tata Consultancy Services")
        prompt = self._construct_competitor_cot_prompt(company_data)
        
        # Check if OpenAI API key is available
        if not self.api_keys["openai"]:
            logger.warning("No OpenAI API key found. Using fallback response.")
            return self._generate_fallback_analysis(company_name)
        
        try:
            import aiohttp
            
            # Make OpenAI API request with enhanced prompt
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_keys['openai']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4",
                        "messages": [
                            {"role": "system", "content": "You are an expert in competitive intelligence with advanced analytical skills."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.2
                    },
                    timeout=60  # Longer timeout for complex analysis
                ) as response:
                    # Check if the request was successful
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract the response content
                        choices = data.get("choices", [])
                        if choices:
                            message = choices[0].get("message", {})
                            content = message.get("content", "{}")
                            finish_reason = choices[0].get("finish_reason")
                            
                            # Process the result to add reasoning chains
                            return self._process_cot_result({
                                "provider": "OpenAI",
                                "model": "gpt-4",
                                "content": content,
                                "metadata": {
                                    "finish_reason": finish_reason,
                                    "tokens": data.get("usage", {}).get("total_tokens", 0)
                                }
                            })
                    
                    # Handle API error
                    error_text = await response.text()
                    logger.error(f"OpenAI API error: {response.status} - {error_text}")
                    
                    # Try fallback to Anthropic if available
                    if self.api_keys["anthropic"]:
                        logger.info("Falling back to Anthropic API...")
                        return await self._anthropic_fallback(prompt)
                    
                    return self._generate_fallback_analysis(company_name)
        
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Try fallback to Anthropic if available
            if self.api_keys["anthropic"]:
                logger.info("Falling back to Anthropic API due to error...")
                return await self._anthropic_fallback(prompt)
            
            return self._generate_fallback_analysis(company_name)
    
    async def _anthropic_fallback(self, prompt: str) -> Dict[str, Any]:
        """
        Anthropic API fallback implementation.
        
        Args:
            prompt: Analysis prompt
            
        Returns:
            AI analysis from Anthropic
        """
        # Check if API key is available
        if not self.api_keys["anthropic"]:
            logger.warning("No Anthropic API key found. Using fallback response.")
            return self._generate_fallback_analysis("Tata Consultancy Services")
        
        try:
            import aiohttp
            
            # Make Anthropic API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_keys["anthropic"],
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "claude-2",
                        "max_tokens": 4000,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2
                    },
                    timeout=60
                ) as response:
                    # Check if the request was successful
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract the response content
                        content = data.get("content", [{}])[0].get("text", "{}")
                        
                        # Process the result to add reasoning chains
                        return self._process_cot_result({
                            "provider": "Anthropic",
                            "model": "claude-2",
                            "content": content,
                            "metadata": {
                                "finish_reason": "stop",
                                "tokens": 0
                            },
                            "fallback_triggered": True
                        })
                    
                    # Handle API error
                    error_text = await response.text()
                    logger.error(f"Anthropic API error: {response.status} - {error_text}")
                    
                    return self._generate_fallback_analysis("Tata Consultancy Services")
        
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {str(e)}")
            logger.error(traceback.format_exc())
            
            return self._generate_fallback_analysis("Tata Consultancy Services")
    
    def _generate_fallback_analysis(self, company_name: str) -> Dict[str, Any]:
        """
        Generate a fallback analysis when API calls fail.
        Includes simulated reasoning chains for structure.
        
        Args:
        
        return self._generate_fallback_analysis(company_name)
    
async def _anthropic_fallback(self, prompt: str) -> Dict[str, Any]:
    """
    Anthropic API fallback implementation.
    
    Args:
        prompt: Analysis prompt
        
    Returns:
        AI analysis from Anthropic
    """
    # Check if API key is available
    if not self.api_keys["anthropic"]:
        logger.warning("No Anthropic API key found. Using fallback response.")
        return self._generate_fallback_analysis("Tata Consultancy Services")
    
    try:
        import aiohttp
        
        # Make Anthropic API request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_keys["anthropic"],
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "claude-2",
                    "max_tokens": 4000,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2
                },
                timeout=60
            ) as response:
                # Check if the request was successful
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract the response content
                    content = data.get("content", [{}])[0].get("text", "{}")
                    
                    # Process the result to add reasoning chains
                    return self._process_cot_result({
                        "provider": "Anthropic",
                        "model": "claude-2",
                        "content": content,
                        "metadata": {
                            "finish_reason": "stop",
                            "tokens": 0
                        },
                        "fallback_triggered": True
                    })
            
                # Handle API error
                error_text = await response.text()
                logger.error(f"Anthropic API error: {response.status} - {error_text}")
                
                return self._generate_fallback_analysis("Tata Consultancy Services")
    
    except Exception as e:
        logger.error(f"Error calling Anthropic API: {str(e)}")
        logger.error(traceback.format_exc())
        
        return self._generate_fallback_analysis("Tata Consultancy Services")
    
def _generate_fallback_analysis(self, company_name: str) -> Dict[str, Any]:
    """
    Generate a fallback analysis when API calls fail.
    Includes simulated reasoning chains for structure.
    
    Args:
        company_name: Name of the company
        
    Returns:
        Fallback analysis with reasoning structure
    """
    logger.info(f"Generating fallback analysis for {company_name}")
    
    # Create a structured fallback response with reasoning chains
    fallback_content = {
        "reasoning_process": {
            "market_position_analysis": f"Based on publicly available information, {company_name} is positioned as a leading global IT services provider with significant presence in key markets.",
            "strengths_evaluation": f"{company_name} demonstrates strong capabilities in digital transformation, cloud services, and strategic consulting, supported by a large global workforce.",
            "weaknesses_assessment": f"Potential challenges for {company_name} include intense competition in the IT services sector and the rapid pace of technological change.",
            "competitor_research": f"Major competitors include Infosys, Wipro, and Cognizant, with varying degrees of specialty in different market segments."
        },
        "competitive_positioning": f"{company_name} is a global leader in IT services, consulting, and business solutions with a strong market presence supported by diverse service offerings and global delivery capabilities.",
        "strengths": [
            {"strength": "Strong global presence", "confidence": 0.92, "evidence": "Operations in multiple countries with diverse client base"},
            {"strength": "Comprehensive service portfolio", "confidence": 0.88, "evidence": "Wide range of IT and business services"},
            {"strength": "Strong brand recognition", "confidence": 0.90, "evidence": "Well-established industry reputation"}
        ],
        "weaknesses": [
            {"weakness": "Market concentration risk", "confidence": 0.85, "evidence": "Potential over-reliance on specific geographic markets"},
            {"weakness": "Talent acquisition challenges", "confidence": 0.82, "evidence": "Industry-wide competition for specialized skills"}
        ],
        "market_share": f"{company_name} holds significant market share in the global IT services sector, particularly in key industry verticals such as banking, finance, and manufacturing.",
        "industry_rank": f"{company_name} consistently ranks among the top IT service providers globally based on revenue and market presence.",
        "competitor_analysis": [
            {
                "competitor_name": "Infosys",
                "strengths": ["Digital transformation expertise", "Strong financial position"],
                "weaknesses": ["Geographic concentration", "Service diversification"],
                "threat_level": "High",
                "threat_justification": "Direct competitor in core markets with similar service offerings and aggressive growth strategy."
            },
            {
                "competitor_name": "Wipro",
                "strengths": ["Technical capabilities", "Growing market presence"],
                "weaknesses": ["Brand recognition", "Scale compared to larger competitors"],
                "threat_level": "Medium",
                "threat_justification": "Significant competitor but with smaller scale and market share in key segments."
            }
        ],
        "overall_confidence": 0.75
    }
    
    return {
        "success": True,
        "provider": "Fallback Service",
        "model": "Statistical Analyzer",
        "content": fallback_content,
        "reasoning_chains": fallback_content.get("reasoning_process", {}),
        "overall_confidence": 0.75,
        "metadata": {
            "finish_reason": "fallback",
            "tokens": 0,
            "confidence_threshold": 0.7,
            "reasoning_enabled": True,
            "fallback_triggered": True,
            "timestamp": datetime.now(UTC).isoformat()
        }
    }


    def analyze_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Primary entry point for analyzing API data and generating a comprehensive TCS report.
        
        This method coordinates all specialized analysis methods to produce a complete
        KPMG-style analytical report with confidence metrics and reasoning chains.
        
        Args:
            api_data: Combined API data including domain info, search data, competitive data, etc.
            
        Returns:
            Comprehensive AI analysis with all components required for the TCS report
        """
        logger.info("Analyzing API data for enhanced TCS report")
        
        try:
            # Extract company data and metadata
            company_data = {
                "company": "Tata Consultancy Services",
                "domain": api_data.get("domain_info", {}).get("domain", "tcs.com"),
                "industry": "IT Services"
            }
            
            # Run comprehensive analysis using all available data
            result = self.generate_comprehensive_analysis(company_data, api_data)
            
            # If comprehensive analysis fails, fall back to individual analyses
            if not result.get("success"):
                logger.warning("Comprehensive analysis failed, falling back to individual analyses")
                result = self._run_individual_analyses(company_data, api_data)
            
            # Add quality and confidence metrics
            result["quality_metrics"] = self._calculate_quality_metrics(api_data, result)
            
            # Add timestamp and metadata
            result["metadata"] = {
                "timestamp": datetime.now(UTC).isoformat(),
                "data_freshness": self._calculate_data_freshness(api_data),
                "analysis_version": "2.0",
                "analysis_type": "kpmg_style"
            }
            
            logger.info("AI analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return a basic fallback analysis
            return {
                "success": False,
                "error": str(e),
                "content": self._get_fallback_analysis(),
                "metadata": {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "fallback": True,
                    "analysis_version": "2.0"
                }
            }
    
    def _run_individual_analyses(self, company_data: Dict[str, Any], api_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run individual analysis components as a fallback strategy.
        
        Args:
            company_data: Basic company information
            api_data: Complete API data
            
        Returns:
            Combined results from individual analyses
        """
        results = {"success": True}
        
        try:
            # Run competitor analysis
            competitor_result = self.generate_competitor_analysis_with_cot(company_data)
            if competitor_result.get("success"):
                results["competitor_analysis"] = competitor_result.get("content", {})
            
            # Extract specific data for other analyses
            search_data = api_data.get("search", {})
            market_data = {**api_data.get("search", {}), **api_data.get("news", {})}
            competitor_data = api_data.get("competitive", {}).get("competitors", [])
            
            # Run content pillars analysis
            content_result = self.generate_content_pillars_analysis(company_data, market_data)
            if content_result.get("success"):
                results["content_pillars"] = content_result.get("content", {})
            
            # Run engagement index analysis
            engagement_result = self.generate_engagement_index_analysis(company_data, competitor_data)
            if engagement_result.get("success"):
                results["engagement_index"] = engagement_result.get("content", {})
            
            # Run opportunity index analysis
            opportunity_result = self.generate_opportunity_index(company_data, search_data)
            if opportunity_result.get("success"):
                results["opportunity_index"] = opportunity_result.get("content", {})
            
            # Run audience segmentation
            audience_result = self.generate_audience_segmentation(company_data, market_data)
            if audience_result.get("success"):
                results["audience_segmentation"] = audience_result.get("content", {})
            
            # Generate strategic recommendations based on all analyses
            results["strategic_recommendations"] = self.generate_strategic_recommendations(results).get("content", {})
            
            return results
            
        except Exception as e:
            logger.error(f"Error in individual analyses: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _calculate_quality_metrics(self, api_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate quality and confidence metrics for the analysis.
        
        Args:
            api_data: Source API data
            analysis_result: Generated analysis
            
        Returns:
            Quality and confidence metrics
        """
        # Calculate data completeness
        data_sources = ["search", "news", "competitive", "social", "engagement", "domain_info"]
        available_sources = sum(1 for source in data_sources if source in api_data and api_data[source])
        data_completeness = min(available_sources / len(data_sources), 1.0)
        
        # Calculate analysis completeness
        analysis_components = ["competitor_analysis", "content_pillars", "engagement_index", 
                              "opportunity_index", "audience_segmentation", "strategic_recommendations"]
        available_components = sum(1 for comp in analysis_components if comp in analysis_result and analysis_result[comp])
        analysis_completeness = min(available_components / len(analysis_components), 1.0)
        
        # Extract confidence scores from analyses
        confidence_scores = []
        for comp in analysis_components:
            if comp in analysis_result and analysis_result[comp]:
                confidence = analysis_result[comp].get("overall_confidence", 0)
                if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                    confidence_scores.append(confidence)
        
        # Calculate overall confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.6
        
        # Apply weighting factors
        overall_confidence = (0.4 * data_completeness + 0.3 * analysis_completeness + 0.3 * avg_confidence)
        
        return {
            "data_completeness": round(data_completeness, 2),
            "analysis_completeness": round(analysis_completeness, 2),
            "component_confidence": round(avg_confidence, 2),
            "overall_confidence": round(overall_confidence, 2)
        }
    
    def _calculate_data_freshness(self, api_data: Dict[str, Any]) -> float:
        """
        Calculate data freshness based on timestamps in the API data.
        
        Args:
            api_data: API data
            
        Returns:
            Data freshness score (0-1)
        """
        try:
            # Look for timestamp fields in the data
            now = datetime.now(UTC)
            timestamps = []
            
            # Check for news article dates
            news_articles = api_data.get("news", {}).get("articles", [])
            for article in news_articles:
                date_str = article.get("publishedAt", "")
                if date_str:
                    try:
                        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        timestamps.append(date)
                    except ValueError:
                        pass
            
            # If no timestamps found, return a neutral score
            if not timestamps:
                return 0.7
            
            # Find the most recent timestamp
            most_recent = max(timestamps)
            days_diff = (now - most_recent).days
            
            # Calculate freshness score (1.0 = very fresh, 0.0 = very stale)
            if days_diff <= 1:  # Today or yesterday
                return 1.0
            elif days_diff <= 7:  # Within a week
                return 0.9
            elif days_diff <= 30:  # Within a month
                return 0.7
            elif days_diff <= 90:  # Within quarter
                return 0.5
            else:
                return 0.3
                
        except Exception:
            # Return a default value on error
            return 0.5
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Provide a complete fallback analysis when AI services fail."""
        return {
            "competitor_analysis": self._get_fallback_competitor_analysis(),
            "content_pillars": self._get_fallback_content_pillars(),
            "engagement_index": self._get_fallback_engagement_index(),
            "opportunity_index": self._get_fallback_opportunity_index(),
            "audience_segmentation": self._get_fallback_audience_segmentation(),
            "strategic_recommendations": self._get_fallback_strategic_recommendations()
        }
            
    def _get_fallback_content_pillars(self) -> Dict[str, Any]:
        """Generate fallback content pillars."""
        return {
            "pillars": [
                {"name": "Digital Transformation", "relevance": 85},
                {"name": "Cloud Services", "relevance": 82},
                {"name": "AI & Automation", "relevance": 78},
                {"name": "Business Solutions", "relevance": 75},
                {"name": "Cybersecurity", "relevance": 72}
            ],
            "taxonomy": {
                "primary": ["IT Services", "Consulting", "Digital Solutions"],
                "secondary": ["Cloud", "AI", "Security", "Enterprise Software"]
            },
            "overall_confidence": 0.7
        }
    
    def _get_fallback_engagement_index(self) -> Dict[str, Any]:
        """Generate fallback engagement index."""
        return {
            "overall_engagement_score": 68,
            "engagement_by_channel": {
                "website": 72,
                "social_media": 65,
                "email": 58,
                "events": 74
            },
            "top_performing_content": [
                {"type": "Case Studies", "engagement": 82},
                {"type": "Whitepapers", "engagement": 75},
                {"type": "Blog Posts", "engagement": 68}
            ],
            "audience_segments": [
                {"segment": "Enterprise IT", "engagement": 79},
                {"segment": "C-Suite", "engagement": 72},
                {"segment": "IT Managers", "engagement": 68}
            ],
            "overall_confidence": 0.7
        }
        
    def _get_fallback_opportunity_index(self) -> Dict[str, Any]:
        """Generate fallback opportunity index."""
        return {
            "overall_opportunity_score": 74,
            "high_value_segments": [
                {"segment": "Banking & Finance", "opportunity": 85},
                {"segment": "Healthcare", "opportunity": 78},
                {"segment": "Manufacturing", "opportunity": 72}
            ],
            "content_gaps": [
                {"topic": "Edge Computing", "gap_score": 76},
                {"topic": "Sustainability IT", "gap_score": 72},
                {"topic": "Quantum Computing", "gap_score": 68}
            ],
            "white_space_map": {
                "emerging_technologies": 82,
                "industry_specific_solutions": 75,
                "integration_services": 68
            },
            "overall_confidence": 0.7
        }
    
    def _get_fallback_audience_segmentation(self) -> Dict[str, Any]:
        """Generate fallback audience segmentation."""
        return {
            "primary_personas": [
                {
                    "name": "Enterprise IT Director",
                    "attributes": {
                        "needs": ["Cost efficiency", "Digital transformation"],
                        "pain_points": ["Legacy systems", "Security concerns"],
                        "content_preferences": ["Case studies", "ROI calculators"]
                    },
                    "engagement_level": 78
                },
                {
                    "name": "CIO/CTO",
                    "attributes": {
                        "needs": ["Strategic insights", "Innovation"],
                        "pain_points": ["Talent shortage", "Rapid technological change"],
                        "content_preferences": ["Whitepapers", "Industry reports"]
                    },
                    "engagement_level": 72
                }
            ],
            "conversion_funnel": {
                "awareness": 85,
                "consideration": 72,
                "decision": 65,
                "loyalty": 78
            },
            "overall_confidence": 0.7
        }
    
    def _get_fallback_strategic_recommendations(self) -> Dict[str, Any]:
        """Generate fallback strategic recommendations."""
        return {
            "content_strategy": [
                {
                    "recommendation": "Develop industry-specific case studies",
                    "impact": "High",
                    "implementation_difficulty": "Medium",
                    "priority": 8
                },
                {
                    "recommendation": "Create thought leadership on emerging technologies",
                    "impact": "High",
                    "implementation_difficulty": "Medium",
                    "priority": 7
                }
            ],
            "competitive_strategy": [
                {
                    "recommendation": "Emphasize AI and automation expertise",
                    "impact": "High",
                    "implementation_difficulty": "Medium",
                    "priority": 8
                },
                {
                    "recommendation": "Highlight client success stories in digital transformation",
                    "impact": "High",
                    "implementation_difficulty": "Low",
                    "priority": 9
                }
            ],
            "overall_confidence": 0.7
        }

# Test the enhanced AI service
async def test_service():
    """Test the enhanced AI service."""
    service = EnhancedAIService()
    result = await service.generate_competitor_analysis_with_cot({
        "company": "Tata Consultancy Services",
        "domain": "tcs.com"
    })
    
    print(f"\nEnhanced AI Analysis Result:")
    print(f"Provider: {result.get('provider')}")
    print(f"Success: {result.get('success')}")
    print(f"Overall Confidence: {result.get('overall_confidence')}")
    
    # Print sample of reasoning chains
    reasoning = result.get("reasoning_chains", {})
    if reasoning:
        print("\nSample Reasoning Chain:")
        for key, value in list(reasoning.items())[:1]:  # Just show first reasoning chain
            print(f"- {key}: {value[:100]}...")
    
    # Print sample strengths with confidence
    content = result.get("content", {})
    strengths = content.get("strengths", [])
    if strengths:
        print("\nSample Strengths with Confidence:")
        for strength in strengths[:2]:  # Just show two strengths
            print(f"- {strength.get('strength')}: {strength.get('confidence')} confidence")
    
    return result


if __name__ == "__main__":
    try:
        asyncio.run(test_service())
    except Exception as e:
        print(f"Error testing service: {str(e)}")
        print(traceback.format_exc())

    def analyze_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Primary entry point for analyzing API data and generating a comprehensive TCS report.
