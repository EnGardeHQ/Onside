"""Market Analysis Service with AI/ML capabilities.

This module implements Sprint 4's market analysis features with predictive
insights, chain-of-thought reasoning, and LLM fallback support.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
from src.services.llm_provider import FallbackManager, LLMProvider
from src.services.ai.llm_with_chain_of_thought import LLMWithChainOfThought
from src.models.report import Report
from src.services.data.market_data import MarketDataService
from src.services.ai.predictive_model import PredictiveModelService


class MarketAnalysisService(LLMWithChainOfThought):
    """Service for AI-powered market analysis and predictions."""
    
    def __init__(
        self,
        llm_manager: FallbackManager,
        market_data_service: MarketDataService,
        predictive_model_service: PredictiveModelService
    ):
        """Initialize the service with required dependencies.
        
        Args:
            llm_manager: Fallback manager for LLM operations
            market_data_service: Service for fetching market data
            predictive_model_service: Service for predictive analytics
        """
        super().__init__(llm_manager)
        self.llm_manager = llm_manager
        self.market_data = market_data_service
        self.predictive_models = predictive_model_service
        self.logger = logging.getLogger(__name__)

    async def _fetch_market_data(
        self,
        company_id: int,
        sectors: List[str],
        timeframe: str
    ) -> Tuple[Dict[str, Any], float]:
        """Fetch and validate market data.
        
        Args:
            company_id: ID of the company to analyze
            sectors: List of market sectors to analyze
            timeframe: Time period for analysis
            
        Returns:
            Tuple of (data, confidence_score)
        """
        try:
            # Log reasoning step
            self._add_reasoning_step(
                "Market Data Collection",
                f"Fetching market data for company ID: {company_id}, sectors: {sectors}, timeframe: {timeframe}"
            )
            
            # Fetch raw data
            raw_data = await self.market_data.get_sector_data(
                company_id,
                sectors,
                timeframe
            )
            
            # Calculate data completeness score
            completeness_score = self.market_data.calculate_completeness(raw_data)
            
            self._add_reasoning_step(
                "Data Validation",
                f"Raw data size: {len(raw_data)}, completeness score: {completeness_score}"
            )
            
            return raw_data, completeness_score
            
        except Exception as e:
            self.logger.error(f"Error fetching market data: {str(e)}")
            raise

    async def _analyze_trends(
        self,
        data: Dict[str, Any],
        sectors: List[str]
    ) -> Tuple[Dict[str, Any], float]:
        """Analyze market trends and patterns.
        
        Args:
            data: Raw market data
            sectors: List of sectors to analyze
            
        Returns:
            Tuple of (trend_analysis, confidence_score)
        """
        try:
            self._add_reasoning_step(
                "Trend Analysis",
                f"Analyzing market trends and patterns for sectors: {sectors}"
            )
            
            # Process each sector
            trend_analysis = {}
            confidence_scores = []
            
            for sector in sectors:
                sector_trends = self.market_data.analyze_sector_trends(
                    data,
                    sector
                )
                trend_analysis[sector] = sector_trends
                confidence_scores.append(sector_trends["confidence"])
            
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            
            self._add_reasoning_step(
                "Pattern Recognition",
                f"Trend analysis complete with confidence score: {avg_confidence}"
            )
            
            return trend_analysis, avg_confidence
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {str(e)}")
            raise

    async def _generate_predictions(
        self,
        trend_analysis: Dict[str, Any],
        report: Report
    ) -> Tuple[List[Dict[str, Any]], float]:
        """Generate market predictions using AI/ML models.
        
        Args:
            trend_analysis: Results from trend analysis
            report: Associated report object for tracking
            
        Returns:
            Tuple of (predictions, confidence_score)
        """
        try:
            self._add_reasoning_step(
                "Prediction Generation",
                "Generating market predictions using AI/ML based on trend analysis"
            )
            
            # Generate predictions using ML models
            ml_predictions = await self.predictive_models.generate_predictions(
                trend_analysis
            )
            
            # Enhance predictions with LLM insights
            prompt = self._prepare_prediction_prompt(trend_analysis, ml_predictions)
            llm_response = await self.llm_manager.execute_with_fallback(
                prompt,
                report,
                initial_provider=LLMProvider.OPENAI
            )
            
            enhanced_predictions = self._combine_predictions(
                ml_predictions,
                llm_response
            )
            
            self._add_reasoning_step(
                "Prediction Validation",
                f"Enhanced predictions generated with confidence score"
            )
            
            # Extract confidence score from LLM response
            confidence_score = 0.7  # Default if not available
            if isinstance(llm_response, dict) and "confidence_score" in llm_response:
                confidence_score = llm_response["confidence_score"]
            
            return enhanced_predictions, confidence_score
            
        except Exception as e:
            self.logger.error(f"Error generating predictions: {str(e)}")
            raise

    def _prepare_prediction_prompt(self, trend_analysis: Dict[str, Any], ml_predictions: Dict[str, Any]) -> str:
        """Prepare prompt for LLM prediction enhancement."""
        return json.dumps({
            "task": "market_prediction_enhancement",
            "data": {
                "trends": trend_analysis,
                "ml_predictions": ml_predictions
            },
            "requirements": {
                "format": "structured_predictions",
                "focus_areas": [
                    "market_opportunities",
                    "potential_risks",
                    "growth_areas",
                    "competitive_dynamics"
                ]
            }
        })

    def _combine_predictions(
        self,
        ml_predictions: Dict[str, Any],
        llm_response: Any
    ) -> List[Dict[str, Any]]:
        """Combine ML predictions with LLM insights."""
        try:
            llm_insights = json.loads(llm_response.content)
            
            # Merge ML predictions with LLM insights
            enhanced_predictions = []
            for prediction in ml_predictions["predictions"]:
                matching_insight = next(
                    (i for i in llm_insights.get("insights", [])
                     if i["sector"] == prediction["sector"]),
                    None
                )
                
                if matching_insight:
                    prediction.update({
                        "qualitative_analysis": matching_insight["analysis"],
                        "recommendations": matching_insight["recommendations"]
                    })
                
                enhanced_predictions.append(prediction)
            
            return enhanced_predictions
            
        except json.JSONDecodeError:
            self.logger.error("Failed to parse LLM response")
            return ml_predictions["predictions"]

    async def analyze(
        self,
        company_id: int,
        sectors: List[str],
        timeframe: str,
        with_chain_of_thought: bool = True,
        include_predictions: bool = True
    ) -> Dict[str, Any]:
        """Analyze market trends and generate predictions.
        
        Args:
            company_id: ID of the company to analyze
            sectors: List of market sectors to analyze
            timeframe: Time period for analysis
            with_chain_of_thought: Whether to include reasoning chain
            include_predictions: Whether to include predictive analysis
            
        Returns:
            Analysis results with predictions and confidence scores
        """
        try:
            # Reset reasoning chain
            self.reset_reasoning()
            
            # Create a report object for tracking
            report = Report(
                type="market_analysis",
                parameters={
                    "company_id": company_id,
                    "sectors": sectors,
                    "timeframe": timeframe
                }
            )
            
            # Fetch and validate data
            data, completeness_score = await self._fetch_market_data(
                company_id,
                sectors,
                timeframe
            )
            
            # Analyze trends
            trend_analysis, trend_confidence = await self._analyze_trends(
                data,
                sectors
            )
            
            # Initialize result structure
            result = {
                "analysis": {
                    "company_id": company_id,
                    "sectors_analyzed": sectors,
                    "timeframe": timeframe,
                    "market_trends": trend_analysis
                },
                "confidence_metrics": {
                    "data_completeness": completeness_score,
                    "trend_accuracy": trend_confidence
                }
            }
            
            # Generate predictions if requested
            if include_predictions:
                predictions, prediction_confidence = await self._generate_predictions(
                    trend_analysis,
                    report
                )
                result["analysis"]["predictions"] = predictions
                result["confidence_metrics"]["prediction_confidence"] = prediction_confidence
            else:
                result["analysis"]["predictions"] = None
            
            # Calculate overall confidence
            confidence_weights = [
                (completeness_score, 0.3),
                (trend_confidence, 0.4)
            ]
            
            if include_predictions:
                confidence_weights.append((prediction_confidence, 0.3))
            
            result["confidence_score"] = sum(
                score * weight for score, weight in confidence_weights
            )
            
            # Include reasoning chain if requested
            if with_chain_of_thought:
                result["reasoning"] = self.get_reasoning()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in market analysis: {str(e)}")
            raise
