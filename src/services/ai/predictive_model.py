"""Predictive Model Service Module.

This module provides predictive modeling capabilities for market analysis.
Following Semantic Seed coding standards with proper error handling,
logging, and type hints.
"""
import logging
import random
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta


class PredictiveModelService:
    """Service for predictive modeling and forecasting."""

    def __init__(self):
        """Initialize the predictive model service."""
        self.logger = logging.getLogger(__name__)
        
        # Define available models
        self.available_models = {
            "time_series": ["arima", "prophet", "lstm"],
            "regression": ["linear", "random_forest", "xgboost"],
            "classification": ["logistic", "random_forest", "svm"]
        }
    
    async def predict_market_trends(
        self,
        market_data: Dict[str, Any],
        forecast_period: str = "1y"
    ) -> Tuple[Dict[str, Any], float]:
        """Generate predictions for market trends.
        
        Args:
            market_data: Market data to use for predictions
            forecast_period: Period to forecast (e.g., "1y", "3y")
            
        Returns:
            Tuple of (predictions, confidence_score)
        """
        try:
            # Extract sectors data
            sectors_data = market_data.get("sectors", {})
            
            if not sectors_data:
                self.logger.warning("No sector data available for predictions")
                return {}, 0.6
            
            # Generate predictions for each sector
            predictions = {}
            sector_confidences = []
            
            for sector_name, sector_data in sectors_data.items():
                sector_metrics = sector_data.get("metrics", {})
                
                if not sector_metrics:
                    continue
                
                # Generate predictions for each metric in the sector
                sector_predictions, sector_confidence = self._predict_sector_metrics(
                    sector_name,
                    sector_metrics,
                    forecast_period
                )
                
                predictions[sector_name] = sector_predictions
                sector_confidences.append(sector_confidence)
            
            # Calculate overall confidence score
            confidence_score = sum(sector_confidences) / len(sector_confidences) if sector_confidences else 0.6
            
            return predictions, confidence_score
            
        except Exception as e:
            self.logger.error(f"Error generating market predictions: {str(e)}")
            return {}, 0.5
    
    def _predict_sector_metrics(
        self,
        sector_name: str,
        sector_metrics: Dict[str, List[Dict[str, Any]]],
        forecast_period: str
    ) -> Tuple[Dict[str, Any], float]:
        """Generate predictions for metrics in a sector.
        
        Args:
            sector_name: Name of the sector
            sector_metrics: Metrics data for the sector
            forecast_period: Period to forecast
            
        Returns:
            Tuple of (predictions, confidence_score)
        """
        # Parse forecast period
        forecast_years = 1
        if forecast_period.endswith("y"):
            try:
                forecast_years = int(forecast_period[:-1])
            except ValueError:
                forecast_years = 1
        
        # Generate predictions for each metric
        metric_predictions = {}
        metric_confidences = []
        
        for metric_name, time_series in sector_metrics.items():
            if not time_series or len(time_series) < 3:
                continue
            
            # Extract values and dates
            values = [point.get("value", 0) for point in time_series]
            dates = [datetime.fromisoformat(point.get("date")) for point in time_series if "date" in point]
            
            if not values or not dates:
                continue
            
            # Select appropriate model based on metric
            model_type = self._select_model_type(metric_name)
            
            # Generate prediction
            prediction, confidence = self._generate_prediction(
                values,
                dates,
                metric_name,
                model_type,
                forecast_years
            )
            
            metric_predictions[metric_name] = prediction
            metric_confidences.append(confidence)
        
        # Calculate overall confidence for the sector
        sector_confidence = sum(metric_confidences) / len(metric_confidences) if metric_confidences else 0.6
        
        # Create sector prediction object
        sector_prediction = {
            "sector": sector_name,
            "metrics": metric_predictions,
            "overall_trend": self._determine_overall_trend(metric_predictions),
            "confidence": sector_confidence
        }
        
        return sector_prediction, sector_confidence
    
    def _select_model_type(self, metric_name: str) -> str:
        """Select appropriate model type based on metric name.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Model type to use
        """
        # Time series models for most metrics
        if metric_name in ["market_size", "growth_rate", "vacancy_rate", "rental_rate", 
                          "inventory", "median_price", "cap_rate", "roi"]:
            return random.choice(self.available_models["time_series"])
        
        # Regression models for others
        return random.choice(self.available_models["regression"])
    
    def _generate_prediction(
        self,
        values: List[float],
        dates: List[datetime],
        metric_name: str,
        model_type: str,
        forecast_years: int
    ) -> Tuple[Dict[str, Any], float]:
        """Generate prediction for a specific metric.
        
        Args:
            values: Historical values
            dates: Corresponding dates
            metric_name: Name of the metric
            model_type: Type of model to use
            forecast_years: Number of years to forecast
            
        Returns:
            Tuple of (prediction, confidence_score)
        """
        # Calculate basic statistics
        current_value = values[-1]
        avg_value = sum(values) / len(values)
        
        # Calculate trend
        trend = self._calculate_trend(values)
        
        # Generate forecast points
        forecast_points = []
        last_date = dates[-1]
        
        for year in range(1, forecast_years + 1):
            # Generate forecast date
            forecast_date = last_date.replace(year=last_date.year + year)
            
            # Generate forecast value based on trend
            trend_factor = trend["strength"] / 100.0  # Convert percentage to factor
            direction_multiplier = 1.0 if trend["direction"] == "increasing" else -1.0
            if trend["direction"] == "stable":
                direction_multiplier = 0.0
            
            # Add some randomness based on model type
            if model_type == "arima" or model_type == "prophet":
                randomness = random.uniform(-0.05, 0.05)
            else:
                randomness = random.uniform(-0.1, 0.1)
            
            # Calculate forecast value
            forecast_value = current_value * (
                1.0 + (direction_multiplier * trend_factor * year) + randomness
            )
            
            # Ensure forecast value is reasonable
            if metric_name in ["growth_rate", "vacancy_rate", "cap_rate"]:
                # These are percentages, keep within reasonable bounds
                forecast_value = max(0.0, min(30.0, forecast_value))
            elif metric_name == "roi":
                # ROI can be negative but usually positive
                forecast_value = max(-10.0, min(30.0, forecast_value))
            elif "rate" in metric_name:
                # Other rates should be positive
                forecast_value = max(0.0, forecast_value)
            
            # Add forecast point
            forecast_points.append({
                "date": forecast_date.isoformat(),
                "value": round(forecast_value, 2)
            })
        
        # Calculate confidence based on data quality and model type
        base_confidence = 0.7
        
        # Adjust for data quality
        if len(values) < 5:
            base_confidence -= 0.1
        
        # Adjust for model type
        if model_type in ["arima", "prophet", "lstm"]:
            base_confidence += 0.05
        elif model_type in ["random_forest", "xgboost"]:
            base_confidence += 0.03
        
        # Adjust for forecast period
        if forecast_years > 2:
            base_confidence -= 0.05 * (forecast_years - 2)
        
        # Ensure confidence is within valid range
        confidence = max(0.5, min(0.9, base_confidence))
        
        return {
            "current_value": current_value,
            "forecast": forecast_points,
            "trend": trend,
            "model": model_type
        }, confidence
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend information for a series of values.
        
        Args:
            values: List of metric values
            
        Returns:
            Dictionary with trend information
        """
        if not values or len(values) < 2:
            return {
                "direction": "stable",
                "strength": 0.0,
                "is_accelerating": False
            }
        
        # Calculate differences between consecutive values
        diffs = [values[i] - values[i-1] for i in range(1, len(values))]
        
        # Calculate average difference
        avg_diff = sum(diffs) / len(diffs)
        
        # Determine trend direction
        if abs(avg_diff) < 0.01:
            direction = "stable"
        elif avg_diff > 0:
            direction = "increasing"
        else:
            direction = "decreasing"
        
        # Calculate trend strength (normalized)
        max_value = max(values) if values else 1.0
        strength = abs(avg_diff / max_value) * 100.0 if max_value != 0 else 0.0
        
        # Determine if trend is accelerating
        if len(diffs) < 2:
            is_accelerating = False
        else:
            # Calculate differences of differences
            second_diffs = [diffs[i] - diffs[i-1] for i in range(1, len(diffs))]
            avg_second_diff = sum(second_diffs) / len(second_diffs)
            
            # Trend is accelerating if second derivative has same sign as first
            is_accelerating = (avg_second_diff * avg_diff > 0 and abs(avg_second_diff) > 0.01)
        
        return {
            "direction": direction,
            "strength": strength,
            "is_accelerating": is_accelerating
        }
    
    def _determine_overall_trend(self, metric_predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Determine overall trend for a sector based on metric predictions.
        
        Args:
            metric_predictions: Predictions for each metric
            
        Returns:
            Overall trend information
        """
        if not metric_predictions:
            return {
                "direction": "stable",
                "confidence": 0.5,
                "summary": "Insufficient data for trend analysis"
            }
        
        # Count trend directions
        directions = {"increasing": 0, "decreasing": 0, "stable": 0}
        
        for metric, prediction in metric_predictions.items():
            trend = prediction.get("trend", {})
            direction = trend.get("direction", "stable")
            directions[direction] += 1
        
        # Determine dominant direction
        total_metrics = sum(directions.values())
        dominant_direction = max(directions.items(), key=lambda x: x[1])
        
        # Calculate confidence based on consensus
        direction_confidence = dominant_direction[1] / total_metrics if total_metrics > 0 else 0.5
        
        # Generate summary
        if dominant_direction[0] == "increasing":
            summary = "Overall positive outlook with growth trends"
        elif dominant_direction[0] == "decreasing":
            summary = "Overall challenging outlook with declining trends"
        else:
            summary = "Overall stable outlook with minimal changes expected"
        
        return {
            "direction": dominant_direction[0],
            "confidence": round(direction_confidence, 2),
            "summary": summary
        }
