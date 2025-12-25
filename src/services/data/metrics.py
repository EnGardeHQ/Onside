"""Metrics Service Module.

This module provides metrics processing and analysis functionality.
Following Semantic Seed coding standards with proper error handling,
logging, and type hints.
"""
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta

class MetricsService:
    """Service for processing and analyzing metrics data."""

    def __init__(self):
        """Initialize the metrics service."""
        self.logger = logging.getLogger(__name__)
    
    def calculate_growth_rate(
        self, 
        current_value: float, 
        previous_value: float
    ) -> float:
        """Calculate growth rate between two values.
        
        Args:
            current_value: Current metric value
            previous_value: Previous metric value
            
        Returns:
            Growth rate as a percentage
        """
        if previous_value == 0:
            return 100.0 if current_value > 0 else 0.0
        
        return ((current_value - previous_value) / previous_value) * 100.0
    
    def calculate_moving_average(
        self, 
        values: List[float], 
        window_size: int = 3
    ) -> List[float]:
        """Calculate moving average for a series of values.
        
        Args:
            values: List of metric values
            window_size: Size of the moving window
            
        Returns:
            List of moving averages
        """
        if not values or window_size <= 0:
            return []
        
        results = []
        for i in range(len(values)):
            if i < window_size - 1:
                # Not enough data points yet
                results.append(sum(values[:i+1]) / (i+1))
            else:
                # Calculate moving average
                window = values[i-(window_size-1):i+1]
                results.append(sum(window) / window_size)
        
        return results
    
    def detect_anomalies(
        self, 
        values: List[float], 
        threshold: float = 2.0
    ) -> List[bool]:
        """Detect anomalies in a series of values using z-score.
        
        Args:
            values: List of metric values
            threshold: Z-score threshold for anomaly detection
            
        Returns:
            List of booleans indicating anomalies
        """
        if not values or len(values) < 3:
            return [False] * len(values)
        
        # Calculate mean and standard deviation
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        # Avoid division by zero
        if std_dev == 0:
            return [False] * len(values)
        
        # Calculate z-scores and detect anomalies
        anomalies = []
        for value in values:
            z_score = abs((value - mean) / std_dev)
            anomalies.append(z_score > threshold)
        
        return anomalies
    
    def calculate_trend(
        self, 
        values: List[float]
    ) -> Dict[str, Any]:
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
    
    def calculate_correlation(
        self, 
        values_a: List[float], 
        values_b: List[float]
    ) -> float:
        """Calculate Pearson correlation coefficient between two series.
        
        Args:
            values_a: First series of values
            values_b: Second series of values
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        if not values_a or not values_b or len(values_a) != len(values_b):
            return 0.0
        
        n = len(values_a)
        
        # Calculate means
        mean_a = sum(values_a) / n
        mean_b = sum(values_b) / n
        
        # Calculate covariance and variances
        covariance = sum((values_a[i] - mean_a) * (values_b[i] - mean_b) for i in range(n))
        variance_a = sum((x - mean_a) ** 2 for x in values_a)
        variance_b = sum((x - mean_b) ** 2 for x in values_b)
        
        # Avoid division by zero
        if variance_a == 0 or variance_b == 0:
            return 0.0
        
        # Calculate correlation coefficient
        correlation = covariance / ((variance_a * variance_b) ** 0.5)
        
        # Ensure result is within valid range
        return max(-1.0, min(1.0, correlation))
    
    def calculate_data_quality(
        self,
        data: Dict[str, Any]
    ) -> float:
        """Calculate data quality score based on completeness and consistency.
        
        Args:
            data: Raw data to evaluate
            
        Returns:
            Quality score between 0 and 1
        """
        try:
            if not data:
                return 0.0
                
            scores = []
            
            # Check data completeness
            total_fields = 0
            non_null_fields = 0
            
            def count_fields(d: Dict[str, Any]) -> None:
                nonlocal total_fields, non_null_fields
                for k, v in d.items():
                    if isinstance(v, dict):
                        count_fields(v)
                    else:
                        total_fields += 1
                        if v is not None:
                            non_null_fields += 1
            
            count_fields(data)
            completeness = non_null_fields / total_fields if total_fields > 0 else 0
            scores.append(completeness)
            
            # Check data consistency
            consistency = 1.0
            for metric_data in data.values():
                if isinstance(metric_data, dict) and 'values' in metric_data:
                    values = metric_data['values']
                    if values:
                        # Check for outliers
                        anomalies = self.detect_anomalies(values)
                        consistency *= (1 - sum(anomalies) / len(anomalies))
            
            scores.append(consistency)
            
            # Calculate final quality score
            quality_score = sum(scores) / len(scores)
            
            self.logger.info(f"Data quality score: {quality_score:.2f}")
            return quality_score
            
        except Exception as e:
            self.logger.error(f"Error calculating data quality: {str(e)}")
            return 0.0

    def analyze_metric(
        self,
        data: Dict[str, Any],
        metric_name: str
    ) -> Dict[str, Any]:
        """Analyze a specific metric and calculate confidence.
        
        Args:
            data: Raw data containing the metric
            metric_name: Name of the metric to analyze
            
        Returns:
            Analysis results with confidence score
        """
        try:
            if metric_name not in data:
                return {
                    "trend": None,
                    "confidence": 0.0,
                    "analysis": "No data available"
                }
            
            metric_data = data[metric_name]
            values = metric_data.get('values', [])
            
            if not values:
                return {
                    "trend": None,
                    "confidence": 0.0,
                    "analysis": "No values available"
                }
            
            # Calculate trend
            trend = self.calculate_trend(values)
            
            # Calculate moving average
            ma = self.calculate_moving_average(values)
            
            # Detect anomalies
            anomalies = self.detect_anomalies(values)
            
            # Calculate confidence based on multiple factors
            confidence_factors = [
                0.8 if len(values) >= 5 else 0.4,  # Data points
                0.9 if not any(anomalies) else 0.5,  # Anomalies
                min(1.0, trend['strength'] / 50.0),  # Trend strength
                0.7 if ma[-1] > ma[0] else 0.3  # Moving average
            ]
            
            confidence = sum(confidence_factors) / len(confidence_factors)
            
            return {
                "trend": trend,
                "moving_average": ma,
                "anomalies": anomalies,
                "confidence": confidence,
                "analysis": f"Metric shows {trend['direction']} trend with {trend['strength']:.1f}% strength"
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing metric {metric_name}: {str(e)}")
            return {
                "trend": None,
                "confidence": 0.0,
                "analysis": f"Error analyzing metric: {str(e)}"
            }

    def analyze_metrics(
        self,
        metrics_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze metrics data and extract insights with confidence scoring.
        
        Args:
            metrics_data: Dictionary of metrics data
            
        Returns:
            Dictionary with analysis results
        """
        results = {}
        
        try:
            for metric_name, data_points in metrics_data.items():
                if not data_points:
                    results[metric_name] = {
                        "trend": {"direction": "unknown", "strength": 0.0, "is_accelerating": False},
                        "growth_rate": 0.0,
                        "has_anomalies": False,
                        "confidence": 0.5
                    }
                    continue
                
                # Extract values and dates
                values = [point.get("value", 0.0) for point in data_points]
                dates = [datetime.fromisoformat(point.get("date")) for point in data_points if "date" in point]
                
                # Calculate trend
                trend = self.calculate_trend(values)
                
                # Calculate growth rate (if enough data)
                growth_rate = 0.0
                if len(values) >= 2:
                    growth_rate = self.calculate_growth_rate(values[-1], values[0])
                
                # Detect anomalies
                anomalies = self.detect_anomalies(values)
                has_anomalies = any(anomalies)
                
                # Calculate confidence based on data quality
                confidence = 0.8  # Base confidence
                
                # Reduce confidence if data is sparse
                if dates and (max(dates) - min(dates)).days > 30 and len(values) < 10:
                    confidence *= 0.8
                
                # Reduce confidence if there are anomalies
                if has_anomalies:
                    confidence *= 0.9
                
                results[metric_name] = {
                    "trend": trend,
                    "growth_rate": growth_rate,
                    "has_anomalies": has_anomalies,
                    "confidence": confidence
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing metrics: {str(e)}")
            return {"error": str(e)}
