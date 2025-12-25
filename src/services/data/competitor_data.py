"""Competitor Data Service.

This module provides access to competitor data for analysis.
"""
from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime, timedelta

from src.repositories.competitor_repository import CompetitorRepository
from src.repositories.competitor_metrics_repository import CompetitorMetricsRepository


class CompetitorDataService:
    """Service for fetching and processing competitor data."""

    def __init__(
        self,
        competitor_repository: CompetitorRepository,
        metrics_repository: CompetitorMetricsRepository,
    ):
        """Initialize the competitor data service.

        Args:
            competitor_repository: Repository for accessing competitor information
            metrics_repository: Repository for accessing competitor metrics
        """
        self.competitor_repository = competitor_repository
        self.metrics_repository = metrics_repository
        self.logger = logging.getLogger(__name__)

    async def get_bulk_data(
        self, competitor_ids: List[int], metrics: List[str], timeframe: str
    ) -> Dict[str, Any]:
        """Get bulk data for multiple competitors.

        Args:
            competitor_ids: List of competitor IDs to fetch data for
            metrics: List of metrics to include
            timeframe: Timeframe for the data (e.g., "last_quarter", "last_year")

        Returns:
            Dict containing competitor data and metrics
        """
        self.logger.info(
            f"Fetching bulk data for {len(competitor_ids)} competitors with {len(metrics)} metrics"
        )
        
        # Parse timeframe into start and end dates
        start_date, end_date = self._parse_timeframe(timeframe)
        
        # Fetch competitor information
        competitors = []
        for competitor_id in competitor_ids:
            competitor = await self.competitor_repository.get_by_id(competitor_id)
            if not competitor:
                self.logger.warning(f"Competitor with ID {competitor_id} not found")
                continue
                
            # Fetch metrics for this competitor
            competitor_metrics = await self.metrics_repository.get_metrics(
                competitor_id=competitor_id,
                metric_names=metrics,
                start_date=start_date,
                end_date=end_date
            )
            
            # Format competitor data
            competitor_data = {
                "id": competitor.id,
                "name": competitor.name,
                "domain": competitor.domain,
                "metrics": competitor_metrics
            }
            
            competitors.append(competitor_data)
        
        return {
            "competitors": competitors,
            "timeframe": f"{start_date.isoformat()} to {end_date.isoformat()}"
        }

    async def get_competitor_data(
        self, competitor_id: int, metrics: List[str], timeframe: str
    ) -> Dict[str, Any]:
        """Get data for a single competitor.

        Args:
            competitor_id: ID of the competitor to fetch data for
            metrics: List of metrics to include
            timeframe: Timeframe for the data (e.g., "last_quarter", "last_year")

        Returns:
            Dict containing competitor data and metrics
        """
        self.logger.info(
            f"Fetching data for competitor {competitor_id} with {len(metrics)} metrics"
        )
        
        # Use bulk data method for consistency
        data = await self.get_bulk_data(
            competitor_ids=[competitor_id],
            metrics=metrics,
            timeframe=timeframe
        )
        
        if not data["competitors"]:
            return {"competitor": None, "timeframe": data["timeframe"]}
            
        return {
            "competitor": data["competitors"][0],
            "timeframe": data["timeframe"]
        }

    def calculate_data_quality(self, data: Dict[str, Any]) -> float:
        """Calculate the quality score for the competitor data.

        Args:
            data: Competitor data to evaluate

        Returns:
            Quality score between 0 and 1
        """
        if not data or "competitors" not in data or not data["competitors"]:
            return 0.0
            
        # Factors that contribute to data quality:
        # 1. Completeness of competitor data
        # 2. Recency of data
        # 3. Coverage of requested metrics
        
        completeness_scores = []
        for competitor in data["competitors"]:
            # Check basic competitor data
            basic_data_score = 1.0
            if not competitor.get("name"):
                basic_data_score -= 0.3
            if not competitor.get("domain"):
                basic_data_score -= 0.2
                
            # Check metrics data
            metrics = competitor.get("metrics", {})
            metric_count = len(metrics)
            metric_score = min(1.0, metric_count / 5)  # Normalize to max of 5 metrics
            
            # Combine scores with weights
            competitor_score = (basic_data_score * 0.4) + (metric_score * 0.6)
            completeness_scores.append(competitor_score)
        
        # Average completeness across all competitors
        avg_completeness = sum(completeness_scores) / len(completeness_scores)
        
        # Overall quality score (can be expanded with more factors)
        quality_score = avg_completeness
        
        return min(1.0, max(0.0, quality_score))

    def _parse_timeframe(self, timeframe: Union[str, Dict[str, str]]) -> tuple[datetime, datetime]:
        """Parse a timeframe into start and end dates.

        Args:
            timeframe: Either a string representation (e.g., "last_quarter", "last_year")
                      or a dictionary with 'start' and 'end' datetime strings

        Returns:
            Tuple of (start_date, end_date)
        """
        now = datetime.now()
        
        # Handle dictionary timeframe format
        if isinstance(timeframe, dict):
            try:
                start_date = datetime.fromisoformat(timeframe['start'].replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(timeframe['end'].replace('Z', '+00:00'))
                return start_date, end_date
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Invalid timeframe dictionary format: {e}, defaulting to last 30 days")
        elif isinstance(timeframe, str):
            if timeframe == "last_week":
                # 7 days ago to today
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                start_date = start_date - timedelta(days=7)
                end_date = now
                return start_date, end_date
            elif timeframe == "last_month":
                # Previous month
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                start_date = start_date - timedelta(days=30)
                end_date = now
                return start_date, end_date
            elif timeframe == "last_quarter":
                # Previous 3 months
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                start_date = start_date - timedelta(days=90)
                end_date = now
                return start_date, end_date
            elif timeframe == "last_year":
                # Previous 12 months
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                start_date = start_date - timedelta(days=365)
                end_date = now
                return start_date, end_date
            elif timeframe == "ytd":
                # Year to date
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now
                return start_date, end_date
        
        # Default to last 30 days for unknown formats
        self.logger.warning(f"Unknown timeframe format: {timeframe}, defaulting to last 30 days")
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date - timedelta(days=30)
        end_date = now
        return start_date, end_date
