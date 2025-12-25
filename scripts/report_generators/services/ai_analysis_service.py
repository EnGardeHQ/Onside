#!/usr/bin/env python
"""
AI Analysis Service - Integrates with OpenAI/Anthropic LLMs via LLMWithChainOfThought.

This service implements the Sprint 4 AI/ML capabilities requirements:
- Chain-of-thought reasoning
- Confidence scoring
- Fallback support
- Comprehensive logging

Following Semantic Seed coding standards.
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

# Use absolute imports with proper model initialization
from src.services.ai.llm_with_chain_of_thought import LLMWithChainOfThought
from src.services.llm_provider.fallback_manager import FallbackManager
from src.models.llm_fallback import LLMProvider

# Import Report using a string literal for the type hint to avoid circular imports
if TYPE_CHECKING:
    from src.models.report import Report as ReportModel
else:
    ReportModel = 'ReportModel'  # type: ignore

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ai_analysis_service")

class AIAnalysisService(LLMWithChainOfThought):
    """
    Service for AI-driven analysis using LLMs with chain-of-thought reasoning.
    
    This class extends LLMWithChainOfThought to provide comprehensive AI-driven
    analysis for the TCS report, integrating with OpenAI and Anthropic with
    fallback support.
    """
    
    def __init__(self, db_session: AsyncSession):
        """Initialize the AI Analysis Service.
        
        Args:
            db_session: SQLAlchemy async session for database operations
        """
        # Configure LLM providers based on environment variables
        # OpenAI as primary, Anthropic as fallback
        providers = [LLMProvider.OPENAI]
        if os.getenv("ENABLE_AI_FALLBACK", "false").lower() == "true":
            providers.append(LLMProvider.ANTHROPIC)
        
        # Initialize fallback manager with configured providers
        fallback_manager = FallbackManager(providers=providers, db_session=db_session)
        
        # Initialize the base LLMWithChainOfThought class
        super().__init__(llm_manager=fallback_manager)
        
        self.db_session = db_session
        self.logger = logger
        
        # Track API call statistics
        self.api_calls = {
            "llm": 0,
            "success": 0,
            "fallback": 0
        }
    
    async def analyze_competitor(self, company_name: str, report: ReportModel) -> Dict[str, Any]:
        """Analyze a competitor using AI with chain-of-thought reasoning.
        
        Args:
            company_name: Name of the company to analyze
            report: Report instance for tracking
            
        Returns:
            Analysis results with confidence scores
        """
        prompt = self._build_competitor_analysis_prompt(company_name)
        result, confidence = await self._execute_llm_with_reasoning(
            prompt=prompt,
            report=report,
            with_chain_of_thought=True,
            confidence_threshold=0.75
        )
        
        self.api_calls["llm"] += 1
        if confidence >= 0.75:
            self.api_calls["success"] += 1
        else:
            self.api_calls["fallback"] += 1
        
        return {
            "result": result,
            "confidence_score": confidence,
            "metadata": {
                "model": os.getenv("OPENAI_MODEL", "gpt-4"),
                "provider": "OpenAI",
                "api_version": "v1",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def analyze_market(self, industry: str, report: ReportModel) -> Dict[str, Any]:
        """Analyze market trends using AI with chain-of-thought reasoning.
        
        Args:
            industry: Industry to analyze
            report: Report instance for tracking
            
        Returns:
            Analysis results with confidence scores
        """
        prompt = self._build_market_analysis_prompt(industry)
        result, confidence = await self._execute_llm_with_reasoning(
            prompt=prompt,
            report=report,
            with_chain_of_thought=True,
            confidence_threshold=0.75
        )
        
        self.api_calls["llm"] += 1
        if confidence >= 0.75:
            self.api_calls["success"] += 1
        else:
            self.api_calls["fallback"] += 1
        
        return {
            "result": result,
            "confidence_score": confidence,
            "metadata": {
                "model": os.getenv("OPENAI_MODEL", "gpt-4"),
                "provider": "OpenAI",
                "api_version": "v1",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def analyze_audience(self, company_name: str, report: ReportModel) -> Dict[str, Any]:
        """Analyze target audience using AI with chain-of-thought reasoning.
        
        Args:
            company_name: Name of the company
            report: Report instance for tracking
            
        Returns:
            Analysis results with confidence scores
        """
        prompt = self._build_audience_analysis_prompt(company_name)
        result, confidence = await self._execute_llm_with_reasoning(
            prompt=prompt,
            report=report,
            with_chain_of_thought=True,
            confidence_threshold=0.75
        )
        
        self.api_calls["llm"] += 1
        if confidence >= 0.75:
            self.api_calls["success"] += 1
        else:
            self.api_calls["fallback"] += 1
        
        return {
            "result": result,
            "confidence_score": confidence,
            "metadata": {
                "model": os.getenv("OPENAI_MODEL", "gpt-4"),
                "provider": "OpenAI",
                "api_version": "v1",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _build_competitor_analysis_prompt(self, company_name: str) -> str:
        """Build a prompt for competitor analysis.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Formatted prompt for competitor analysis
        """
        return f"""
        Perform a comprehensive competitor analysis for {company_name}.
        
        Analyze the company's:
        1. Market position and competitive advantages
        2. Strengths and weaknesses compared to key competitors
        3. Key products, services, and value propositions
        4. Recent strategic initiatives and trends
        
        Structure your response as a JSON object with the following fields:
        - competitive_positioning: Overview of the company's market position
        - strengths: List of the company's key strengths
        - weaknesses: List of the company's key weaknesses
        - market_share: Estimated market share if available
        - industry_rank: Estimated industry rank if available
        - competitor_analysis: List of key competitors with their strengths, weaknesses, and threat level
        
        Detail level: {os.getenv('COT_DETAIL_LEVEL', 'comprehensive')}
        """
    
    def _build_market_analysis_prompt(self, industry: str) -> str:
        """Build a prompt for market analysis.
        
        Args:
            industry: Industry to analyze
            
        Returns:
            Formatted prompt for market analysis
        """
        return f"""
        Perform a comprehensive market analysis for the {industry} industry.
        
        Analyze the following:
        1. Current market size and growth projections
        2. Key trends and innovations driving the industry
        3. Major opportunities and threats
        4. Regulatory and economic factors affecting the industry
        
        Structure your response as a JSON object with the following fields:
        - market_size: Estimated market size
        - growth_rate: Projected growth rate (CAGR)
        - trends: List of key industry trends
        - opportunities: List of major market opportunities
        - threats: List of significant market threats
        
        Detail level: {os.getenv('COT_DETAIL_LEVEL', 'comprehensive')}
        """
    
    def _build_audience_analysis_prompt(self, company_name: str) -> str:
        """Build a prompt for audience analysis.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Formatted prompt for audience analysis
        """
        return f"""
        Perform a comprehensive audience analysis for {company_name}.
        
        Create detailed customer personas:
        1. Primary customer segments and decision makers
        2. Key needs, motivations, and pain points
        3. Typical engagement patterns and buyer journey
        4. Demographic and firmographic profiles
        
        Structure your response as a JSON object with the following fields:
        - primary_personas: List of detailed customer personas with name, description, 
          engagement_patterns, and key_needs
        - decision_factors: Key factors influencing purchasing decisions
        - engagement_channels: Preferred channels for engagement
        - customer_satisfaction: Assessment of customer satisfaction if available
        
        Detail level: {os.getenv('COT_DETAIL_LEVEL', 'comprehensive')}
        """
    
    def get_api_call_stats(self) -> Dict[str, int]:
        """Get statistics about API calls made by this service.
        
        Returns:
            Dictionary with API call statistics
        """
        return self.api_calls
