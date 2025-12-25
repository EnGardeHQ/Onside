"""Audience Analysis Service with AI/ML capabilities.

This module implements Sprint 4's audience analysis features with AI-driven
persona insights, chain-of-thought reasoning, and LLM fallback support.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
from src.services.llm_provider import FallbackManager, LLMProvider
from src.services.ai.llm_with_chain_of_thought import LLMWithChainOfThought
from src.models.report import Report
from src.services.data.audience_data import AudienceDataService
from src.services.data.engagement_metrics import EngagementMetricsService


class AudienceAnalysisService(LLMWithChainOfThought):
    """Service for AI-powered audience analysis and persona generation."""
    
    def __init__(
        self,
        llm_manager: FallbackManager,
        audience_data_service: AudienceDataService,
        engagement_metrics_service: EngagementMetricsService
    ):
        """Initialize the service with required dependencies.
        
        Args:
            llm_manager: Fallback manager for LLM operations
            audience_data_service: Service for fetching audience data
            engagement_metrics_service: Service for engagement metrics
        """
        super().__init__(llm_manager)
        self.llm_manager = llm_manager
        self.audience_data = audience_data_service
        self.engagement_metrics = engagement_metrics_service
        self.logger = logging.getLogger(__name__)

    async def _fetch_audience_data(
        self,
        company_id: int,
        segment_id: Optional[int],
        timeframe: str,
        demographic_filters: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], float]:
        """Fetch and validate audience data.
        
        Args:
            company_id: ID of the company to analyze
            segment_id: Optional specific segment to analyze
            timeframe: Time range for analysis
            demographic_filters: Filters for demographic analysis
            
        Returns:
            Tuple of (data, confidence_score)
        """
        try:
            # Log reasoning step
            self._add_reasoning_step(
                "Audience Data Collection",
                f"Fetching audience data for company ID: {company_id}, segment ID: {segment_id}, timeframe: {timeframe}"
            )
            
            # Fetch raw data
            raw_data = await self.audience_data.get_audience_data(
                company_id,
                segment_id,
                timeframe,
                demographic_filters
            )
            
            # Calculate data quality score
            data_quality = self.audience_data.calculate_data_quality(raw_data)
            
            self._add_reasoning_step(
                "Data Validation",
                f"Raw data size: {len(raw_data)}, data quality score: {data_quality}"
            )
            
            return raw_data, data_quality
            
        except Exception as e:
            self.logger.error(f"Error fetching audience data: {str(e)}")
            raise

    async def _analyze_engagement(
        self,
        data: Dict[str, Any],
        timeframe: str
    ) -> Tuple[Dict[str, Any], float]:
        """Analyze engagement patterns and behaviors.
        
        Args:
            data: Raw audience data
            timeframe: Time range for analysis
            
        Returns:
            Tuple of (engagement_analysis, confidence_score)
        """
        try:
            self._add_reasoning_step(
                "Engagement Analysis",
                f"Analyzing engagement patterns and behaviors for timeframe: {timeframe}"
            )
            
            # Process engagement metrics
            engagement_analysis = await self.engagement_metrics.analyze_patterns(
                data,
                timeframe
            )
            
            self._add_reasoning_step(
                "Pattern Recognition",
                f"Engagement analysis complete with confidence score: {engagement_analysis['confidence']}"
            )
            
            return engagement_analysis, engagement_analysis["confidence"]
            
        except Exception as e:
            self.logger.error(f"Error analyzing engagement: {str(e)}")
            raise

    async def _generate_personas(
        self,
        data: Dict[str, Any],
        engagement_analysis: Dict[str, Any],
        report: Report
    ) -> Tuple[List[Dict[str, Any]], float]:
        """Generate audience personas using AI/ML.
        
        Args:
            data: Raw audience data
            engagement_analysis: Results from engagement analysis
            report: Associated report object for tracking
            
        Returns:
            Tuple of (personas, confidence_score)
        """
        try:
            self._add_reasoning_step(
                "Persona Generation",
                "Generating audience personas using AI/ML based on audience data and engagement analysis"
            )
            
            # Prepare prompt for LLM
            prompt = self._prepare_persona_prompt(data, engagement_analysis)
            
            # Get personas with fallback support
            llm_response = await self.llm_manager.execute_with_fallback(
                prompt,
                report,
                initial_provider=LLMProvider.OPENAI
            )
            
            personas = self._parse_llm_response(llm_response)
            
            self._add_reasoning_step(
                "Persona Validation",
                f"Processed personas with confidence score"
            )
            
            # Extract confidence score from LLM response
            confidence_score = 0.7  # Default if not available
            if isinstance(llm_response, dict) and "confidence_score" in llm_response:
                confidence_score = llm_response["confidence_score"]
            
            return personas, confidence_score
            
        except Exception as e:
            self.logger.error(f"Error generating personas: {str(e)}")
            raise

    def _prepare_persona_prompt(self, data: Dict[str, Any], engagement_analysis: Dict[str, Any]) -> str:
        """Prepare prompt for LLM persona generation."""
        return json.dumps({
            "task": "audience_persona_generation",
            "data": {
                "audience_data": data,
                "engagement_patterns": engagement_analysis
            },
            "requirements": {
                "format": "structured_personas",
                "attributes": [
                    "demographics",
                    "behaviors",
                    "preferences",
                    "engagement_patterns"
                ],
                "insights": [
                    "content_preferences",
                    "communication_channels",
                    "engagement_triggers",
                    "growth_opportunities"
                ]
            }
        })

    def _parse_llm_response(
        self,
        llm_response: Any
    ) -> List[Dict[str, Any]]:
        """Parse and validate LLM response."""
        try:
            response_data = json.loads(llm_response.content)
            return response_data.get("personas", [])
        except json.JSONDecodeError:
            self.logger.error("Failed to parse LLM response")
            return []

    async def analyze(
        self,
        company_id: int,
        segment_id: Optional[int],
        timeframe: str,
        demographic_filters: Dict[str, Any],
        with_chain_of_thought: bool = True
    ) -> Dict[str, Any]:
        """Analyze audience segments and generate persona insights.
        
        Args:
            company_id: ID of the company to analyze
            segment_id: Optional specific segment to analyze
            timeframe: Time range for analysis
            demographic_filters: Filters for demographic analysis
            with_chain_of_thought: Whether to include AI reasoning steps
            
        Returns:
            Dict containing analysis results, confidence metrics, and reasoning
        """
        try:
            # Reset reasoning chain
            self.reset_reasoning()
            
            # Create a report object for tracking
            report = Report(
                type="audience_analysis",
                parameters={
                    "company_id": company_id,
                    "segment_id": segment_id,
                    "timeframe": timeframe,
                    "demographic_filters": demographic_filters
                }
            )
            
            # Fetch and validate data
            data, data_quality = await self._fetch_audience_data(
                company_id,
                segment_id,
                timeframe,
                demographic_filters
            )
            
            # Analyze engagement patterns
            engagement_analysis, engagement_confidence = await self._analyze_engagement(
                data,
                timeframe
            )
            
            # Generate personas
            personas, persona_confidence = await self._generate_personas(
                data,
                engagement_analysis,
                report
            )
            
            # Calculate overall confidence
            confidence_score = (
                data_quality * 0.3 +
                engagement_confidence * 0.35 +
                persona_confidence * 0.35
            )
            
            result = {
                "analysis": {
                    "company_id": company_id,
                    "segment_id": segment_id,
                    "timeframe": timeframe,
                    "demographics": demographic_filters,
                    "personas": personas,
                    "engagement_patterns": engagement_analysis["patterns"],
                    "recommendations": engagement_analysis["recommendations"]
                },
                "confidence_score": confidence_score,
                "confidence_metrics": {
                    "data_quality": data_quality,
                    "engagement_confidence": engagement_confidence,
                    "persona_confidence": persona_confidence
                }
            }
            
            # Include reasoning chain if requested
            if with_chain_of_thought:
                result["reasoning"] = self.get_reasoning()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in audience analysis: {str(e)}")
            # Use fallback analysis in case of errors
            return self._generate_fallback_analysis(
                company_id,
                segment_id,
                str(e)
            )

    def _generate_fallback_analysis(
        self,
        company_id: int,
        segment_id: Optional[int],
        error: str
    ) -> Dict[str, Any]:
        """Generate basic analysis when AI processing fails."""
        self.log_step(
            "Fallback Analysis",
            {"error": error},
            "Using fallback due to AI processing failure"
        )
        
        return {
            "analysis": {
                "company_id": company_id,
                "segment_id": segment_id,
                "error": error,
                "personas": [],
                "engagement_patterns": [],
                "recommendations": []
            },
            "confidence_score": 0.5,
            "confidence_metrics": {
                "fallback_quality": 0.5
            },
            "reasoning": self.get_reasoning()
        }
