from typing import Dict, List
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
import logging

logger = logging.getLogger(__name__)

class TrendService:
    def __init__(self):
        self.semrush_client = None  # Initialize your SEMrush client here
        self.cache = {}
        self.cache_duration = timedelta(hours=24)

    async def get_trend_data(self, topic: str) -> Dict:
        """Get trend data for a topic"""
        try:
            cache_key = f"trend_{topic}"
            if cache_key in self.cache:
                cached_data, cache_time = self.cache[cache_key]
                if datetime.now() - cache_time < self.cache_duration:
                    return cached_data

            # Fetch historical data
            historical_data = await self._fetch_historical_data(topic)
            
            # Process trend data
            trend_data = self._process_trend_data(historical_data)
            
            # Cache the results
            self.cache[cache_key] = (trend_data, datetime.now())
            
            return trend_data
        except Exception as e:
            logger.error(f"Error getting trend data: {str(e)}")
            return None

    async def _fetch_historical_data(self, topic: str) -> pd.DataFrame:
        """Fetch historical data for trend analysis"""
        try:
            # Fetch 24 months of historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=730)
            
            raw_data = await self.semrush_client.get_historical_data(
                topic,
                start_date,
                end_date
            )
            
            df = pd.DataFrame(raw_data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return None

    def _process_trend_data(self, df: pd.DataFrame) -> Dict:
        """Process historical data to extract trend information"""
        try:
            if df is None or df.empty:
                return None

            # Decompose time series
            decomposition = seasonal_decompose(
                df['volume'],
                period=12,  # Monthly seasonality
                extrapolate_trend='freq'
            )

            # Calculate growth rate
            growth_rate = self._calculate_growth_rate(df['volume'])
            
            # Calculate momentum
            momentum = self._calculate_momentum(df['volume'])
            
            # Calculate seasonality strength
            seasonality_strength = self._calculate_seasonality_strength(
                decomposition.seasonal,
                decomposition.trend
            )

            return {
                "trend": decomposition.trend.tolist(),
                "seasonal": decomposition.seasonal.tolist(),
                "growth_rate": growth_rate,
                "momentum": momentum,
                "seasonality_strength": seasonality_strength,
                "current_phase": self._determine_trend_phase(decomposition.trend),
                "forecast": self._generate_forecast(df['volume'])
            }
        except Exception as e:
            logger.error(f"Error processing trend data: {str(e)}")
            return None

    def _calculate_growth_rate(self, series: pd.Series) -> float:
        """Calculate the growth rate of the trend"""
        try:
            # Use last 6 months for growth rate calculation
            recent_data = series.tail(6)
            start_value = recent_data.iloc[0]
            end_value = recent_data.iloc[-1]
            
            if start_value == 0:
                return 0.0
                
            return (end_value - start_value) / start_value
        except Exception as e:
            logger.error(f"Error calculating growth rate: {str(e)}")
            return 0.0

    def _calculate_momentum(self, series: pd.Series) -> float:
        """Calculate momentum score"""
        try:
            # Compare last 3 months vs previous 3 months
            recent_3m = series.tail(3).mean()
            previous_3m = series.tail(6).head(3).mean()
            
            if previous_3m == 0:
                return 0.0
                
            return (recent_3m - previous_3m) / previous_3m
        except Exception as e:
            logger.error(f"Error calculating momentum: {str(e)}")
            return 0.0

    def _calculate_seasonality_strength(self, seasonal: pd.Series, trend: pd.Series) -> float:
        """Calculate the strength of seasonality"""
        try:
            seasonal_strength = np.std(seasonal) / np.std(trend)
            return min(1.0, max(0.0, seasonal_strength))
        except Exception as e:
            logger.error(f"Error calculating seasonality strength: {str(e)}")
            return 0.0

    def _determine_trend_phase(self, trend: pd.Series) -> str:
        """Determine the current phase of the trend"""
        try:
            recent_trend = trend.tail(3)
            
            if recent_trend.is_monotonic_increasing:
                return "growth"
            elif recent_trend.is_monotonic_decreasing:
                return "decline"
            else:
                return "stable"
        except Exception as e:
            logger.error(f"Error determining trend phase: {str(e)}")
            return "unknown"

    def _generate_forecast(self, series: pd.Series, periods: int = 3) -> List[float]:
        """Generate a simple forecast for the next few periods"""
        try:
            # Use simple moving average for forecast
            # In production, this should be replaced with more sophisticated models
            ma = series.rolling(window=6).mean()
            last_ma = ma.iloc[-1]
            growth = self._calculate_growth_rate(series)
            
            forecast = [last_ma * (1 + growth * i) for i in range(1, periods + 1)]
            return forecast
        except Exception as e:
            logger.error(f"Error generating forecast: {str(e)}")
            return []
