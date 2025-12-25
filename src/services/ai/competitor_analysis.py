"""Competitor Analysis Service with AI/ML capabilities.

This module implements Sprint 4's competitor analysis features using
chain-of-thought reasoning and LLM fallback support.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
import time
from src.services.llm_provider import FallbackManager, LLMProvider
from src.services.ai.llm_with_chain_of_thought import LLMWithChainOfThought
from src.models.report import Report
from src.services.data.competitor_data import CompetitorDataService
from src.services.data.metrics import MetricsService


class CompetitorAnalysisService(LLMWithChainOfThought):
    """Service for AI-powered competitor analysis with chain-of-thought reasoning."""
    
    def __init__(
        self,
        llm_manager: FallbackManager,
        competitor_data_service: CompetitorDataService,
        metrics_service: MetricsService
    ):
        """Initialize the service with required dependencies.
        
        Args:
            llm_manager: Fallback manager for LLM operations
            competitor_data_service: Service for fetching competitor data
            metrics_service: Service for processing metrics
        """
        super().__init__(llm_manager)
        self.llm_manager = llm_manager
        self.competitor_data = competitor_data_service
        self.metrics = metrics_service
        self.logger = logging.getLogger(__name__)
        self.processing_times = {
            "data_fetch": 0.0,
            "metrics_analysis": 0.0,
            "insights_generation": 0.0,
            "positioning_analysis": 0.0,
            "total": 0.0
        }

    async def _fetch_competitor_data(
        self,
        competitor_ids: List[int],
        metrics: List[str],
        timeframe: str
    ) -> Tuple[Dict[str, Any], float]:
        start_time = time.time()
        """Fetch and validate competitor data.
        
        Args:
            competitor_ids: List of competitor IDs to analyze
            metrics: List of metrics to analyze
            timeframe: Time period for analysis
            
        Returns:
            Tuple of (data, confidence_score)
        """
        try:
            # Log reasoning step
            self._add_reasoning_step(
                "Data Collection",
                f"Fetching competitor data for IDs: {competitor_ids}, metrics: {metrics}, timeframe: {timeframe}"
            )
            
            # Fetch raw data
            raw_data = await self.competitor_data.get_bulk_data(
                competitor_ids,
                metrics,
                timeframe
            )
            
            # Calculate data quality score
            data_quality = self.metrics.calculate_data_quality(raw_data)
            
            self._add_reasoning_step(
                "Data Validation",
                f"Raw data size: {len(raw_data)}, data quality score: {data_quality}"
            )
            
            # Track processing time
            self.processing_times["data_fetch"] = time.time() - start_time
            
            return raw_data, data_quality
            
        except Exception as e:
            self.logger.error(f"Error fetching competitor data: {str(e)}")
            raise

    async def _analyze_metrics(
        self,
        data: Dict[str, Any],
        metrics: List[str]
    ) -> Tuple[Dict[str, Any], float]:
        start_time = time.time()
        """Analyze metrics and identify trends.
        
        Args:
            data: Raw competitor data
            metrics: List of metrics to analyze
            
        Returns:
            Tuple of (analysis_results, confidence_score)
        """
        try:
            self._add_reasoning_step(
                "Metric Analysis",
                f"Processing metrics: {metrics} and identifying trends"
            )
            
            # Process each metric
            analysis_results = {}
            confidence_scores = []
            
            for metric in metrics:
                metric_data = self.metrics.analyze_metric(
                    data,
                    metric
                )
                analysis_results[metric] = metric_data
                confidence_scores.append(metric_data["confidence"])
            
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            
            self._add_reasoning_step(
                "Trend Identification",
                f"Analysis complete with confidence score: {avg_confidence}"
            )
            
            # Track processing time
            self.processing_times["metrics_analysis"] = time.time() - start_time
            
            return analysis_results, avg_confidence
            
        except Exception as e:
            self.logger.error(f"Error analyzing metrics: {str(e)}")
            raise

    async def _generate_insights(
        self,
        analysis_results: Dict[str, Any],
        report: Report
    ) -> Tuple[List[Dict[str, Any]], float]:
        start_time = time.time()
        """Generate insights using LLM with fallback support.
        
        Args:
            analysis_results: Results from metric analysis
            report: Associated report object for tracking
            
        Returns:
            Tuple of (insights, confidence_score)
        """
        try:
            self._add_reasoning_step(
                "Insight Generation",
                "Generating insights using LLM based on analysis results"
            )
            
            # Prepare prompt for LLM
            prompt = self._prepare_insight_prompt(analysis_results)
            
            # Get insights with fallback support
            llm_response = await self.llm_manager.execute_with_fallback(
                prompt,
                report,
                initial_provider=LLMProvider.OPENAI
            )
            
            # Parse insights and get confidence score
            insights = self._parse_llm_response(llm_response)
            
            # Calculate confidence based on insight quality
            if len(insights) > 0:
                # Start with base confidence
                insight_confidence = 0.75
                
                # Count total insights
                total_insights = len(insights)
                
                # Adjust confidence based on number of insights
                if total_insights >= 8:
                    insight_confidence += 0.15
                elif total_insights >= 5:
                    insight_confidence += 0.1
                elif total_insights <= 2:
                    insight_confidence -= 0.2
                
                # Cap confidence at 0.95
                insight_confidence = min(insight_confidence, 0.95)
            else:
                insight_confidence = 0.0
                
            self.logger.info(f"Calculated insight confidence: {insight_confidence:.2f}")
            
            # Track processing time
            self.processing_times["insights_generation"] = time.time() - start_time
            
            self._add_reasoning_step(
                "Insight Validation",
                f"Processed insights with confidence score: {insight_confidence}"
            )
            
            # Structure and validate insights
            structured_insights = {
                "trends": [],
                "opportunities": [],
                "threats": [],
                "recommendations": []
            }
            
            # Handle both list and dict response formats
            if isinstance(insights, dict):
                insights_list = insights.get("insights", [])
            elif isinstance(insights, list):
                insights_list = insights
            else:
                self.logger.error(f"Unexpected insights format: {type(insights)}")
                return structured_insights, 0.0
            
            # Process each insight
            for insight in insights_list:
                if not isinstance(insight, dict):
                    continue
                    
                insight_type = insight.get("type", "general")
                if insight_type in structured_insights:
                    # Ensure required fields and proper types
                    processed_insight = {
                        "type": insight_type,
                        "content": str(insight.get("content", "")),
                        "confidence": float(insight.get("confidence", 0.7)),
                        "supporting_data": insight.get("supporting_data", {}),
                        "action_items": insight.get("action_items", [])
                    }
                    structured_insights[insight_type].append(processed_insight)
            
            # Calculate confidence based on insight quality and coverage
            if len(structured_insights) > 0:
                # Calculate average confidence across all insights
                total_confidence = 0.0
                total_insights = 0
                
                for category in structured_insights.values():
                    for insight in category:
                        total_confidence += insight.get('confidence', 0.0)
                        total_insights += 1
                
                # Calculate weighted confidence score
                insight_confidence = total_confidence / max(total_insights, 1)
                
                # Apply category coverage penalty if missing important categories
                category_coverage = len([k for k, v in structured_insights.items() if len(v) > 0]) / 4.0
                insight_confidence *= (0.7 + (0.3 * category_coverage))
                
                # Cap confidence at 0.95
                insight_confidence = min(insight_confidence, 0.95)
            else:
                insight_confidence = 0.0
                
            self.logger.info(f"Calculated insight confidence: {insight_confidence:.2f}")
            return structured_insights, insight_confidence
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {str(e)}")
            raise

    def _prepare_insight_prompt(self, analysis_results: Dict[str, Any]) -> str:
        """Prepare prompt for LLM insight generation."""
        return (
            "You are an AI analyst helping generate insights for a competitor analysis report. "
            "Analyze the following data and generate structured insights:\n\n"
            f"DATA: {json.dumps(analysis_results, indent=2)}\n\n"
            "REQUIREMENTS:\n"
            "1. Structure your response as a valid JSON object\n"
            "2. Include an 'insights' array containing insight objects\n"
            "3. Each insight object must have:\n"
            "   - type: one of [trend, opportunity, threat, recommendation]\n"
            "   - content: detailed description of the insight\n"
            "   - confidence: float between 0-1 indicating confidence\n"
            "   - supporting_data: object with relevant metrics/data points\n"
            "   - action_items: array of specific actions to take\n\n"
            "4. Use chain-of-thought reasoning to explain your analysis\n"
            "5. Focus on actionable insights that can drive business decisions\n\n"
            "EXAMPLE RESPONSE FORMAT:\n"
            "{"
            "  \"insights\": ["
            "    {"
            "      \"type\": \"trend\","
            "      \"content\": \"Detailed insight description\","
            "      \"confidence\": 0.85,"
            "      \"supporting_data\": {\"metric1\": \"value1\"},"
            "      \"action_items\": [\"Action 1\", \"Action 2\"]"
            "    }"
            "  ]"
            "}"
        )

    def _parse_llm_response(
        self,
        llm_response: Any
    ) -> List[Dict[str, Any]]:
        """Parse and validate LLM response following Sprint 4 implementation."""
        try:
            # Extract content from response
            self.logger.debug(f"Raw LLM response type: {type(llm_response)}")
            
            # Handle different response types
            if isinstance(llm_response, tuple):
                # Typically (content, provider) from FallbackManager
                response_content = llm_response[0]
            elif isinstance(llm_response, str):
                # String response from LLM
                response_content = llm_response
            elif hasattr(llm_response, 'content'):
                # Object with content attribute
                response_content = llm_response.content
            elif isinstance(llm_response, dict):
                # Already a dictionary, use directly
                insights_data = llm_response
                self.logger.info("LLM response already in dictionary format, skipping JSON parsing")
            else:
                raise ValueError(f"Unexpected LLM response type: {type(llm_response)}")
            
            # Parse JSON response if not already a dict
            if not isinstance(llm_response, dict):
                try:
                    insights_data = json.loads(response_content) if isinstance(response_content, str) else response_content
                except json.JSONDecodeError:
                    self.logger.error(f"Failed to parse LLM response: {response_content[:200]}...")
                    return []
                
            # Handle different response formats
            if isinstance(insights_data, list):
                insights_list = insights_data
            elif isinstance(insights_data, dict):
                insights_list = insights_data.get("insights", [])
                if not insights_list:
                    # Try to extract from response directly if no insights field
                    insights_list = []
                    for key in ["trends", "opportunities", "threats", "recommendations"]:
                        items = insights_data.get(key, [])
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict):
                                    item["type"] = key
                                    insights_list.append(item)
            else:
                self.logger.error(f"Invalid insights format: {type(insights_data)}")
                return []
                
            # Validate and structure insights
            structured_insights = []
            for insight in insights_list:
                if not isinstance(insight, dict):
                    continue
                    
                try:
                    structured_insights.append({
                        "type": str(insight.get("type", "general")),
                        "content": str(insight.get("content", "")),
                        "confidence": float(insight.get("confidence", 0.7)),
                        "supporting_data": dict(insight.get("supporting_data", {})),
                        "action_items": list(insight.get("action_items", []))
                    })
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Failed to process insight: {str(e)}")
                    continue
                
            return structured_insights
        except json.JSONDecodeError:
            self.logger.error("Failed to parse LLM response")
            self.logger.error("Failed to parse LLM response")
            return []

    async def _analyze_positioning(
        self,
        competitor_data: Dict[str, Any],
        analysis_results: Dict[str, Any],
        insights: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[Dict[str, Any], float]:
        start_time = time.time()
        """Analyze competitive positioning based on data, analysis, and insights.
        
        Args:
            competitor_data: Raw competitor data
            analysis_results: Results from metric analysis
            insights: Generated insights categorized by type
            
        Returns:
            Tuple of (positioning_analysis, confidence_score)
        """
        try:
            self._add_reasoning_step(
                "Competitive Positioning Analysis",
                "Analyzing market positioning of competitors based on metrics and insights"
            )
            
            # Extract competitors and metrics
            competitors = list(competitor_data.keys())
            if not competitors:
                self.logger.warning("No competitor data available for positioning analysis")
                return {}, 0.0
            
            # Initialize positioning analysis structure
            positioning = {
                "market_quadrants": {
                    "leaders": [],
                    "challengers": [],
                    "visionaries": [],
                    "niche_players": []
                },
                "relative_strengths": {},
                "differentiation_factors": {},
                "positioning_map": {}
            }
            
            # Default confidence value
            confidence = 0.7
            
            # Assign competitors to quadrants based on performance metrics
            for competitor_id, metrics in analysis_results.get("metrics", {}).items():
                if not isinstance(metrics, dict):
                    continue
                
                # Calculate overall score using available metrics
                score = 0.0
                total_metrics = 0
                
                for metric_name, metric_value in metrics.items():
                    if isinstance(metric_value, (int, float)):
                        score += float(metric_value)
                        total_metrics += 1
                
                avg_score = score / max(total_metrics, 1)
                
                # Assign to quadrant based on score
                if avg_score >= 0.75:
                    positioning["market_quadrants"]["leaders"].append(competitor_id)
                elif avg_score >= 0.5:
                    positioning["market_quadrants"]["challengers"].append(competitor_id)
                elif avg_score >= 0.25:
                    positioning["market_quadrants"]["visionaries"].append(competitor_id)
                else:
                    positioning["market_quadrants"]["niche_players"].append(competitor_id)
                
                # Record relative strengths
                strengths = []
                for metric_name, metric_value in metrics.items():
                    if isinstance(metric_value, (int, float)) and metric_value >= 0.7:
                        strengths.append(metric_name)
                
                if strengths:
                    positioning["relative_strengths"][competitor_id] = strengths
            
            # Extract differentiation factors from insights
            for insight_type in ["trends", "opportunities", "threats"]:
                for insight in insights.get(insight_type, []):
                    if "competitor_id" in insight.get("supporting_data", {}):
                        competitor_id = insight["supporting_data"]["competitor_id"]
                        if competitor_id not in positioning["differentiation_factors"]:
                            positioning["differentiation_factors"][competitor_id] = []
                        
                        positioning["differentiation_factors"][competitor_id].append({
                            "type": insight_type,
                            "factor": insight["content"]
                        })
            
            # Create simplified positioning map
            for competitor_id in competitors:
                quadrant = "unknown"
                for q_name, q_competitors in positioning["market_quadrants"].items():
                    if competitor_id in q_competitors:
                        quadrant = q_name
                        break
                
                strengths = positioning["relative_strengths"].get(competitor_id, [])
                diff_factors = positioning["differentiation_factors"].get(competitor_id, [])
                
                positioning["positioning_map"][competitor_id] = {
                    "quadrant": quadrant,
                    "strengths": strengths,
                    "differentiation": [df["factor"] for df in diff_factors]
                }
            
            # Calculate confidence based on data completeness
            quadrant_coverage = sum(1 for q, comps in positioning["market_quadrants"].items() if comps)
            strength_coverage = len(positioning["relative_strengths"]) / max(len(competitors), 1)
            diff_coverage = len(positioning["differentiation_factors"]) / max(len(competitors), 1)
            
            # Weighted confidence calculation
            confidence = (
                (quadrant_coverage / 4.0) * 0.4 +  # Quadrant assignment weight
                strength_coverage * 0.3 +          # Strength identification weight
                diff_coverage * 0.3               # Differentiation factors weight
            )
            
            # Cap confidence at 0.95
            confidence = min(max(confidence, 0.0), 0.95)
            
            self._add_reasoning_step(
                "Positioning Result",
                f"Completed positioning analysis with confidence: {confidence:.2f}"
            )
            
            # Track processing time
            self.processing_times["positioning_analysis"] = time.time() - start_time
            
            return positioning, confidence
            
        except Exception as e:
            self.logger.error(f"Error in competitive positioning analysis: {str(e)}")
            return {}, 0.0
    
    def get_reasoning_chain(self) -> List[str]:
        """Get the chain of thought reasoning steps.
        
        Returns:
            List of reasoning steps with timestamps
        """
        return self.chain_of_thought_steps
        
    def get_processing_time(self) -> Dict[str, float]:
        """Get the processing time metrics for each analysis step.
        
        Returns:
            Dictionary with processing times in seconds for each step
        """
        return self.processing_times
    
    async def analyze(
        self,
        competitor_ids: List[int],
        metrics: List[str],
        timeframe: str,
        with_chain_of_thought: bool = True,
        confidence_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        # Track overall processing time
        total_start_time = time.time()
        """Analyze competitors using AI/ML capabilities.
        
        Args:
            competitor_ids: List of competitor IDs to analyze
            metrics: List of metrics to analyze
            timeframe: Time period for analysis
            with_chain_of_thought: Whether to include reasoning chain
            confidence_threshold: Minimum confidence score required
            
        Returns:
            Analysis results with confidence scores and reasoning chain
        """
        try:
            # Reset reasoning chain
            self.reset_chain_of_thought()
            
            # Create a report object for tracking
            report = Report(
                type="competitor_analysis",
                parameters={
                    "competitor_ids": competitor_ids,
                    "metrics": metrics,
                    "timeframe": timeframe
                }
            )
            
            # Fetch and validate data
            data, data_quality = await self._fetch_competitor_data(
                competitor_ids,
                metrics,
                timeframe
            )
            
            # Analyze metrics
            analysis_results, metric_confidence = await self._analyze_metrics(
                data,
                metrics
            )
            
            # Generate insights
            insights, insight_confidence = await self._generate_insights(
                analysis_results,
                report
            )
            
            # Calculate overall confidence
            confidence_score = (
                data_quality * 0.3 +
                metric_confidence * 0.3 +
                insight_confidence * 0.4
            )
            
            # Check confidence threshold
            if confidence_threshold and confidence_score < confidence_threshold:
                self.logger.warning(
                    f"Analysis confidence {confidence_score} below threshold "
                    f"{confidence_threshold}"
                )
            
            result = {
                "analysis": {
                    "competitors": len(competitor_ids),
                    "metrics_analyzed": metrics,
                    "timeframe": timeframe,
                    "insights": insights
                },
                "confidence_score": confidence_score,
                "confidence_metrics": {
                    "data_quality": data_quality,
                    "metric_confidence": metric_confidence,
                    "insight_confidence": insight_confidence
                }
            }
            
            # Include reasoning chain if requested
            if with_chain_of_thought:
                result["reasoning"] = self.get_reasoning_chain()
            
            # Calculate total processing time
            self.processing_times["total"] = time.time() - total_start_time
            result["processing_time"] = self.get_processing_time()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in competitor analysis: {str(e)}")
            raise
