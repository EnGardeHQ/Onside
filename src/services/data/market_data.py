"""Market Data Service Module.

This module provides market data retrieval and processing functionality.
Following Semantic Seed coding standards with proper error handling,
logging, and type hints.
"""
import logging
import random
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta

from src.repositories.company_repository import CompanyRepository


class MarketDataService:
    """Service for retrieving and processing market data."""

    def __init__(self, company_repository: CompanyRepository):
        """Initialize the market data service.
        
        Args:
            company_repository: Repository for company data
        """
        self.company_repo = company_repository
        self.logger = logging.getLogger(__name__)
        
        # Define market sectors for analysis
        self.sectors = {
            "commercial_real_estate": {
                "metrics": ["market_size", "growth_rate", "vacancy_rate", "rental_rate"],
                "competitors": ["CBRE", "Cushman & Wakefield", "Colliers", "Newmark"]
            },
            "residential_real_estate": {
                "metrics": ["market_size", "growth_rate", "inventory", "median_price"],
                "competitors": ["Redfin", "Zillow", "Compass", "eXp Realty"]
            },
            "property_management": {
                "metrics": ["market_size", "growth_rate", "client_retention", "revenue_per_property"],
                "competitors": ["FirstService Residential", "Greystar", "Lincoln Property Company"]
            },
            "real_estate_investment": {
                "metrics": ["market_size", "growth_rate", "cap_rate", "roi"],
                "competitors": ["Blackstone", "Brookfield", "Prologis", "Simon Property Group"]
            }
        }
    
    async def get_market_data(
        self,
        company_id: int,
        sectors: List[str],
        timeframe: str
    ) -> Tuple[Dict[str, Any], float]:
        """Get market data for specified sectors and timeframe.
        
        Args:
            company_id: ID of the company
            sectors: List of market sectors to analyze
            timeframe: Time range for analysis (e.g., "last_quarter")
            
        Returns:
            Tuple of (market_data, completeness_score)
        """
        try:
            # Get company information
            company = await self.company_repo.get_by_id(company_id)
            if not company:
                self.logger.error(f"Company with ID {company_id} not found")
                return {}, 0.5
            
            # Parse timeframe
            date_range = self._parse_timeframe(timeframe)
            if not date_range:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return {}, 0.5
            
            start_date, end_date = date_range
            
            # Initialize result structure
            market_data = {
                "company": {
                    "id": company.id,
                    "name": company.name,
                    "industry": company.industry
                },
                "timeframe": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "description": timeframe
                },
                "sectors": {}
            }
            
            # Generate data for each requested sector
            valid_sectors = 0
            for sector in sectors:
                if sector in self.sectors:
                    sector_data = await self._generate_sector_data(sector, start_date, end_date)
                    market_data["sectors"][sector] = sector_data
                    valid_sectors += 1
                else:
                    self.logger.warning(f"Unknown sector: {sector}")
            
            # Calculate completeness score
            completeness_score = valid_sectors / len(sectors) if sectors else 0.5
            
            return market_data, completeness_score
            
        except Exception as e:
            self.logger.error(f"Error retrieving market data: {str(e)}")
            return {}, 0.5
    
    def _parse_timeframe(self, timeframe: str) -> Optional[Tuple[datetime, datetime]]:
        """Parse timeframe string into start and end dates.
        
        Args:
            timeframe: Time range description (e.g., "last_quarter")
            
        Returns:
            Tuple of (start_date, end_date) or None if invalid
        """
        now = datetime.utcnow()
        
        if timeframe == "last_month":
            start_date = now - timedelta(days=30)
            end_date = now
        elif timeframe == "last_quarter":
            start_date = now - timedelta(days=90)
            end_date = now
        elif timeframe == "last_year":
            start_date = now - timedelta(days=365)
            end_date = now
        elif timeframe == "ytd":  # Year to date
            start_date = datetime(now.year, 1, 1)
            end_date = now
        else:
            return None
        
        return start_date, end_date
    
    async def _generate_sector_data(
        self,
        sector: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate market data for a specific sector.
        
        Args:
            sector: Market sector name
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            Dictionary with sector data
        """
        sector_info = self.sectors.get(sector, {})
        metrics = sector_info.get("metrics", [])
        competitors = sector_info.get("competitors", [])
        
        # Generate time series data
        days = (end_date - start_date).days
        data_points = max(5, days // 7)  # Weekly data points
        
        metrics_data = {}
        for metric in metrics:
            # Generate realistic time series data with trends
            base_value = self._get_base_value_for_metric(metric)
            trend_factor = random.uniform(-0.1, 0.2)  # Slight upward bias
            
            time_series = []
            for i in range(data_points):
                point_date = start_date + timedelta(days=(i * days // data_points))
                progress = i / (data_points - 1) if data_points > 1 else 0
                
                # Add trend and some noise
                value = base_value * (1 + trend_factor * progress + random.uniform(-0.05, 0.05))
                
                time_series.append({
                    "date": point_date.isoformat(),
                    "value": round(value, 2),
                    "confidence": round(random.uniform(0.7, 0.95), 2)
                })
            
            metrics_data[metric] = time_series
        
        # Generate competitor data
        competitor_data = {}
        for competitor in competitors:
            competitor_metrics = {}
            for metric in metrics:
                base_value = self._get_base_value_for_metric(metric)
                competitor_metrics[metric] = round(base_value * random.uniform(0.8, 1.2), 2)
            
            competitor_data[competitor] = competitor_metrics
        
        return {
            "overview": {
                "name": sector.replace("_", " ").title(),
                "description": f"Analysis of the {sector.replace('_', ' ')} sector",
                "key_trends": self._generate_key_trends(sector)
            },
            "metrics": metrics_data,
            "competitors": competitor_data,
            "forecast": self._generate_forecast(sector, metrics)
        }
    
    def _get_base_value_for_metric(self, metric: str) -> float:
        """Get a realistic base value for a metric.
        
        Args:
            metric: Metric name
            
        Returns:
            Base value for the metric
        """
        metric_ranges = {
            "market_size": (1000000000, 5000000000),  # $1B - $5B
            "growth_rate": (1.0, 8.0),                # 1% - 8%
            "vacancy_rate": (3.0, 12.0),              # 3% - 12%
            "rental_rate": (20.0, 50.0),              # $20 - $50 per sq ft
            "inventory": (10000, 50000),              # 10K - 50K units
            "median_price": (250000, 750000),         # $250K - $750K
            "client_retention": (70.0, 95.0),         # 70% - 95%
            "revenue_per_property": (5000, 15000),    # $5K - $15K
            "cap_rate": (3.0, 8.0),                   # 3% - 8%
            "roi": (5.0, 15.0)                        # 5% - 15%
        }
        
        min_val, max_val = metric_ranges.get(metric, (10, 100))
        return random.uniform(min_val, max_val)
    
    def _generate_key_trends(self, sector: str) -> List[str]:
        """Generate key trends for a sector.
        
        Args:
            sector: Market sector name
            
        Returns:
            List of trend descriptions
        """
        trends_by_sector = {
            "commercial_real_estate": [
                "Increasing demand for flexible office spaces",
                "Growing adoption of smart building technology",
                "Rising importance of ESG considerations",
                "Shift towards suburban office locations"
            ],
            "residential_real_estate": [
                "Rising demand for sustainable homes",
                "Increasing preference for larger living spaces",
                "Growing interest in suburban properties",
                "Adoption of virtual property tours"
            ],
            "property_management": [
                "Integration of AI for property maintenance",
                "Increasing focus on tenant experience",
                "Growing demand for contactless services",
                "Rising importance of data analytics"
            ],
            "real_estate_investment": [
                "Shift towards alternative property types",
                "Increasing interest in proptech investments",
                "Growing focus on resilient assets",
                "Rising importance of ESG criteria"
            ]
        }
        
        return trends_by_sector.get(sector, ["Increasing market competition", "Technology adoption"])
    
    def _generate_forecast(self, sector: str, metrics: List[str]) -> Dict[str, Any]:
        """Generate market forecast for a sector.
        
        Args:
            sector: Market sector name
            metrics: List of metrics to forecast
            
        Returns:
            Dictionary with forecast data
        """
        forecast = {
            "short_term": {
                "outlook": random.choice(["positive", "stable", "cautiously optimistic"]),
                "growth_projection": round(random.uniform(1.5, 5.0), 1),
                "confidence": round(random.uniform(0.7, 0.9), 2)
            },
            "long_term": {
                "outlook": random.choice(["positive", "stable", "cautiously optimistic"]),
                "growth_projection": round(random.uniform(2.0, 8.0), 1),
                "confidence": round(random.uniform(0.6, 0.8), 2)
            },
            "metrics": {}
        }
        
        for metric in metrics:
            forecast["metrics"][metric] = {
                "current": round(self._get_base_value_for_metric(metric), 2),
                "projected_1y": round(self._get_base_value_for_metric(metric) * random.uniform(1.0, 1.1), 2),
                "projected_3y": round(self._get_base_value_for_metric(metric) * random.uniform(1.05, 1.2), 2),
                "confidence": round(random.uniform(0.6, 0.8), 2)
            }
        
        return forecast
