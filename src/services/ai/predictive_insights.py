from prophet import Prophet
import pandas as pd
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import json
import logging

from src.models.content import Content
from src.models.ai import AIInsight, InsightType
from src.models.engagement import EngagementMetrics
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import func, select
import numpy as np

from src.services.ai.llm_service import LLMService, LLMProvider
from src.services.ai.chain_of_thought import ChainOfThoughtReasoning

logger = logging.getLogger(__name__)

class PredictiveInsightsService:
    def __init__(self):
        # Use lazy initialization for Prophet model to avoid import-time errors
        self._model = None

        # Initialize LLM service for enhanced insights and fallback mechanisms
        self.llm_service = LLMService()

    @property
    def model(self):
        """Lazy initialization of Prophet model"""
        if self._model is None:
            self._model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=True
            )
        return self._model
        
    async def predict_engagement_trends(
        self,
        content: Content,
        db: Union[Session, AsyncSession],
        days_ahead: int = 7,
        with_reasoning: bool = False
    ) -> AIInsight:
        """Predict future engagement trends for content with enhanced LLM insights and fallback"""
        # Initialize reasoning tracking if requested
        reasoning = ChainOfThoughtReasoning() if with_reasoning else None
        
        if reasoning:
            reasoning.add_step(
                "Initializing engagement prediction",
                {"content_id": content.id, "days_ahead": days_ahead},
                {"status": "initialized"}
            )
        
        try:
            # Get historical engagement data
            engagement_data = self._get_engagement_history(content.id, db)
            
            if reasoning:
                reasoning.add_step(
                    "Retrieved historical engagement data",
                    {"content_id": content.id},
                    {"data_points": len(engagement_data), "sample": engagement_data[:3] if engagement_data else []}
                )
            
            if len(engagement_data) < 3:  # Need minimum data points
                if reasoning:
                    reasoning.add_step(
                        "Insufficient data for prediction",
                        {"data_points": len(engagement_data), "minimum_required": 3},
                        {"status": "insufficient_data"}
                    )
                return await self._create_insufficient_data_insight(content.id, db, reasoning)
            
            # Primary approach: Use Prophet for time series prediction
            try:
                # Prepare data for Prophet
                df = pd.DataFrame(engagement_data)
                df.columns = ['ds', 'y']
                
                if reasoning:
                    reasoning.add_step(
                        "Prepared data for Prophet model",
                        {"dataframe_shape": df.shape},
                        {"status": "data_prepared"}
                    )
                
                # Fit model
                self.model.fit(df)
                
                # Make future predictions
                future_dates = self.model.make_future_dataframe(
                    periods=days_ahead,
                    freq='D'
                )
                forecast = self.model.predict(future_dates)
                
                if reasoning:
                    reasoning.add_step(
                        "Generated forecast with Prophet",
                        {"forecast_periods": days_ahead},
                        {"status": "forecast_generated", "prediction_columns": list(forecast.columns)}
                    )
                
                # Calculate trend metrics
                current_trend = self._calculate_trend_metrics(forecast)
                
                if reasoning:
                    reasoning.add_step(
                        "Calculated trend metrics",
                        {"method": "prophet"},
                        {"trend_metrics": current_trend}
                    )
            except Exception as e:
                # If Prophet fails, use LLM-enhanced fallback
                logger.warning(f"Prophet prediction failed, using LLM fallback: {str(e)}")
                
                if reasoning:
                    reasoning.add_step(
                        "Prophet prediction failed, using LLM fallback",
                        {"error": str(e)},
                        {"status": "prophet_failed_using_llm"}
                    )
                
                # Use LLM to generate insights based on historical data
                current_trend = await self._llm_generate_insights(
                    content, engagement_data, days_ahead, with_reasoning
                )
            
            # Create insight
            with db.begin():
                insight = AIInsight(
                    content_id=content.id,
                    insight_type="engagement_prediction",
                    score=current_trend["trend_score"],
                    confidence=current_trend["confidence"],
                    insight_metadata={
                        "days_ahead": days_ahead,
                        "trend_metrics": current_trend,
                        "forecast_values": forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
                        .tail(days_ahead)
                        .to_dict("records")
                    }
                )
                
                db.add(insight)
                db.commit()
                db.refresh(insight)
                
            return insight
            
        except Exception as e:
            db.rollback()
            raise e

    def _create_insufficient_data_insight(
        self,
        content_id: int,
        db: Session
    ) -> AIInsight:
        """Create an insight indicating insufficient data"""
        with db.begin():
            insight = AIInsight(
                content_id=content_id,
                insight_type="engagement_prediction",
                score=0.0,
                confidence=0.0,
                insight_metadata={
                    "error": "Insufficient data for prediction",
                    "required_points": 3
                }
            )
            
            db.add(insight)
            db.commit()
            db.refresh(insight)
            
        return insight

    def _get_engagement_history(
        self,
        content_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get historical engagement data for content"""
        with db.begin():
            metrics = db.query(
                EngagementMetrics.timestamp,
                func.sum(EngagementMetrics.value).label("total_engagement")
            ).filter(
                EngagementMetrics.content_id == content_id
            ).group_by(
                EngagementMetrics.timestamp
            ).order_by(
                EngagementMetrics.timestamp
            ).all()
            
        return [
            {"ds": m.timestamp, "y": float(m.total_engagement)}
            for m in metrics
        ]

    def _calculate_trend_metrics(self, forecast: pd.DataFrame) -> Dict[str, Any]:
        """Calculate trend metrics from forecast"""
        recent_values = forecast.tail(7)  # Last week of predictions
        
        trend_direction = np.mean(np.diff(recent_values["yhat"]))
        trend_volatility = np.std(recent_values["yhat"])
        
        # Normalize trend score between 0 and 1
        trend_score = 1 / (1 + np.exp(-trend_direction))  # Sigmoid function
        
        # Calculate confidence based on prediction intervals
        confidence = 1 - (
            np.mean(recent_values["yhat_upper"] - recent_values["yhat_lower"]) /
            np.mean(recent_values["yhat"])
        )
        
        return {
            "trend_score": float(trend_score),
            "confidence": float(max(0.0, min(1.0, confidence))),  # Clamp between 0 and 1
            "direction": float(trend_direction),
            "volatility": float(trend_volatility)
        }
        
    async def _llm_generate_insights(
        self,
        content: Content,
        engagement_data: List[Dict],
        days_ahead: int,
        with_reasoning: bool = False
    ) -> Dict[str, Any]:
        """Generate predictive insights using LLM when statistical methods fail
        
        This serves as a fallback when Prophet or other statistical methods fail.
        """
        # Initialize reasoning tracking if requested
        reasoning = ChainOfThoughtReasoning() if with_reasoning else None
        
        if reasoning:
            reasoning.add_step(
                "Starting LLM-based insight generation",
                {"content_id": content.id, "data_points": len(engagement_data)},
                {"status": "llm_insight_generation_started"}
            )
        
        # Prepare the prompt for LLM
        engagement_summary = "\n".join(
            [f"Date: {item['ds'].strftime('%Y-%m-%d')}, Engagements: {item['y']}" for item in engagement_data]
        )
        
        prompt = f"""
        Analyze the following engagement data for content and predict engagement trends for the next {days_ahead} days:
        
        Content Title: {content.title}
        Content Type: {content.content_type}
        Content Creation Date: {content.created_at.strftime('%Y-%m-%d')}
        
        Historical Engagement Data:
        {engagement_summary}
        
        Based on this data:
        1. Predict the trend direction for the next {days_ahead} days (increasing, decreasing, or stable)
        2. Estimate the confidence level of this prediction (0.0 to 1.0)
        3. Calculate a trend score between 0 and 1, where higher values indicate a more positive trend
        4. Estimate the volatility of the engagement
        
        Format your response as a JSON object with the following keys:
        "trend_score", "confidence", "direction", "volatility"
        """
        
        if reasoning:
            reasoning.add_step(
                "Prepared LLM prompt",
                {"prompt_length": len(prompt)},
                {"status": "prompt_prepared"}
            )
        
        try:
            # Call LLM service with the prompt
            llm_response = await self.llm_service.generate(
                prompt=prompt,
                provider=LLMProvider.OPENAI,  # Default provider
                temperature=0.1,  # Low temperature for more deterministic results
                response_format={"type": "json_object"},
                with_reasoning=with_reasoning
            )
            
            if reasoning:
                reasoning.add_step(
                    "Received LLM response",
                    {"response_length": len(llm_response)},
                    {"status": "llm_response_received"}
                )
            
            # Parse the JSON response
            try:
                trend_metrics = json.loads(llm_response)
                
                # Ensure all required keys are present
                required_keys = ["trend_score", "confidence", "direction", "volatility"]
                for key in required_keys:
                    if key not in trend_metrics:
                        trend_metrics[key] = 0.5  # Default value
                
                if reasoning:
                    reasoning.add_step(
                        "Processed LLM insights",
                        {"method": "llm_json_parsing"},
                        {"processed_metrics": trend_metrics}
                    )
                    
                return trend_metrics
                
            except json.JSONDecodeError:
                # Fallback to basic metrics if JSON parsing fails
                if reasoning:
                    reasoning.add_step(
                        "Failed to parse LLM JSON response",
                        {"error": "JSON parsing error"},
                        {"status": "parsing_failed_using_defaults"}
                    )
                return self._calculate_basic_metrics(engagement_data)
                
        except Exception as e:
            # If LLM fails, fall back to basic calculation
            logger.warning(f"LLM insight generation failed, using basic metrics: {str(e)}")
            
            if reasoning:
                reasoning.add_step(
                    "LLM insight generation failed",
                    {"error": str(e)},
                    {"status": "llm_failed_using_basic_metrics"}
                )
                
            return self._calculate_basic_metrics(engagement_data)
    
    def _calculate_basic_metrics(self, engagement_data: List[Dict]) -> Dict[str, Any]:
        """Calculate basic metrics when both Prophet and LLM fail"""
        if not engagement_data:
            return {
                "trend_score": 0.5,
                "confidence": 0.1,
                "direction": 0.0,
                "volatility": 0.0
            }
        
        # Extract engagement values
        values = [item['y'] for item in engagement_data]
        
        # Calculate trend direction using simple linear regression
        x = np.arange(len(values))
        if len(values) > 1:
            # Use numpy's polyfit for simple linear regression
            slope, _ = np.polyfit(x, values, 1)
            direction = slope
        else:
            direction = 0.0
        
        # Calculate volatility as standard deviation
        volatility = np.std(values) if len(values) > 1 else 0.0
        
        # Normalize trend score between 0 and 1
        # Using sigmoid function to normalize
        trend_score = 1 / (1 + np.exp(-direction))
        
        # Low confidence due to fallback method
        confidence = 0.4
        
        return {
            "trend_score": float(trend_score),
            "confidence": float(confidence),
            "direction": float(direction),
            "volatility": float(volatility)
        }
    
    async def _get_enhanced_insights(
        self,
        content: Content,
        trend_metrics: Dict[str, Any],
        with_reasoning: bool = False
    ) -> tuple[str, List[str]]:
        """Get enhanced interpretations and recommendations using LLM"""
        # Initialize reasoning tracking if requested
        reasoning = ChainOfThoughtReasoning() if with_reasoning else None
        
        if reasoning:
            reasoning.add_step(
                "Starting enhanced insights generation",
                {"content_id": content.id, "trend_metrics": trend_metrics},
                {"status": "enhanced_insights_started"}
            )
        
        # Prepare the prompt for interpretation and recommendations
        prompt = f"""
        Based on the following engagement trend metrics for content, provide:
        1. A concise interpretation of the trend
        2. Three actionable recommendations to optimize future engagement
        
        Content Title: {content.title}
        Content Type: {content.content_type}
        
        Engagement Trend Metrics:
        - Trend Score: {trend_metrics.get('trend_score', 0.5)} (0-1 scale, higher is more positive)
        - Trend Direction: {trend_metrics.get('direction', 0.0)} (positive values indicate increasing engagement)
        - Volatility: {trend_metrics.get('volatility', 0.0)} (higher values indicate more erratic engagement patterns)
        - Prediction Confidence: {trend_metrics.get('confidence', 0.5)} (0-1 scale)
        
        Format your response as a JSON object with the following keys:
        "interpretation": a string with your trend interpretation
        "recommendations": an array of strings with your recommendations
        """
        
        if reasoning:
            reasoning.add_step(
                "Prepared LLM prompt for enhanced insights",
                {"prompt_length": len(prompt)},
                {"status": "enhanced_insights_prompt_prepared"}
            )
        
        try:
            # Call LLM service with the prompt
            llm_response = await self.llm_service.generate(
                prompt=prompt,
                provider=LLMProvider.OPENAI,  # Default provider
                temperature=0.7,  # Higher temperature for more creative recommendations
                response_format={"type": "json_object"},
                with_reasoning=with_reasoning
            )
            
            if reasoning:
                reasoning.add_step(
                    "Received LLM enhanced insights",
                    {"response_length": len(llm_response)},
                    {"status": "enhanced_insights_received"}
                )
            
            # Parse the JSON response
            try:
                insights = json.loads(llm_response)
                interpretation = insights.get("interpretation", "")
                recommendations = insights.get("recommendations", [])
                
                if reasoning:
                    reasoning.add_step(
                        "Processed enhanced insights",
                        {"method": "llm_json_parsing"},
                        {
                            "interpretation_length": len(interpretation),
                            "recommendations_count": len(recommendations)
                        }
                    )
                    
                return interpretation, recommendations
                
            except json.JSONDecodeError:
                # Fallback to rule-based insights if JSON parsing fails
                if reasoning:
                    reasoning.add_step(
                        "Failed to parse LLM JSON response for insights",
                        {"error": "JSON parsing error"},
                        {"status": "insights_parsing_failed_using_rules"}
                    )
                return self._get_trend_interpretations(trend_metrics), self._get_content_recommendations(trend_metrics)
                
        except Exception as e:
            # If LLM fails, fall back to rule-based insights
            logger.warning(f"Enhanced insights generation failed, using rule-based fallback: {str(e)}")
            
            if reasoning:
                reasoning.add_step(
                    "Enhanced insights generation failed",
                    {"error": str(e)},
                    {"status": "enhanced_insights_failed_using_rules"}
                )
                
            return self._get_trend_interpretations(trend_metrics), self._get_content_recommendations(trend_metrics)
    
    def _get_trend_interpretations(self, trend_metrics: Dict[str, Any]) -> str:
        """Generate rule-based interpretations of trend metrics"""
        trend_score = trend_metrics.get('trend_score', 0.5)
        direction = trend_metrics.get('direction', 0.0)
        volatility = trend_metrics.get('volatility', 0.0)
        confidence = trend_metrics.get('confidence', 0.5)
        
        # Determine trend direction
        if direction > 0.05:
            direction_text = "increasing"
        elif direction < -0.05:
            direction_text = "decreasing"
        else:
            direction_text = "stable"
        
        # Determine volatility level
        if volatility > 0.5:
            volatility_text = "highly volatile"
        elif volatility > 0.2:
            volatility_text = "somewhat volatile"
        else:
            volatility_text = "stable"
        
        # Determine confidence level
        if confidence > 0.8:
            confidence_text = "high confidence"
        elif confidence > 0.5:
            confidence_text = "moderate confidence"
        else:
            confidence_text = "low confidence"
        
        # Generate interpretation
        interpretation = f"The engagement trend is {direction_text} with {volatility_text} patterns. "
        interpretation += f"Analysis shows a trend score of {trend_score:.2f} with {confidence_text}. "
        
        # Add additional context based on trend direction
        if direction_text == "increasing":
            interpretation += "Content is gaining traction and showing positive momentum."
        elif direction_text == "decreasing":
            interpretation += "Content is experiencing a decline in engagement that may require attention."
        else:
            interpretation += "Content is maintaining consistent engagement levels."
            
        return interpretation
    
    def _get_content_recommendations(self, trend_metrics: Dict[str, Any]) -> List[str]:
        """Generate rule-based recommendations based on trend metrics"""
        trend_score = trend_metrics.get('trend_score', 0.5)
        direction = trend_metrics.get('direction', 0.0)
        volatility = trend_metrics.get('volatility', 0.0)
        
        recommendations = []
        
        # Recommendations based on trend direction
        if direction > 0.05:  # Increasing trend
            recommendations.append("Capitalize on positive momentum by creating similar content to maintain growth.")
            recommendations.append("Analyze which aspects of this content resonated with your audience to replicate success.")
            recommendations.append("Consider promoting this content to wider audiences to maximize reach.")
            
        elif direction < -0.05:  # Decreasing trend
            recommendations.append("Review and refresh content with updated information to renew interest.")
            recommendations.append("Evaluate the positioning and distribution channels for this content.")
            recommendations.append("Consider A/B testing different headlines or formats to improve engagement.")
            
        else:  # Stable trend
            recommendations.append("Maintain consistent posting schedule to preserve current engagement levels.")
            recommendations.append("Introduce minor variations to test audience preferences without disrupting stability.")
            recommendations.append("Monitor competitors' similar content for opportunities to differentiate.")
        
        # Additional recommendations based on volatility
        if volatility > 0.3:
            recommendations.append("Develop a more consistent content strategy to reduce engagement volatility.")
            recommendations.append("Identify potential external factors causing engagement fluctuations.")
        
        # Return top 3 recommendations
        return recommendations[:3]
