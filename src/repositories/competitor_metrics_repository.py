"""Competitor Metrics Repository Module.

This module provides database operations for competitor metrics.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.competitor_metrics import CompetitorMetrics


class CompetitorMetricsRepository:
    """Repository for competitor metrics database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize the repository with a database session.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def get_metrics(
        self,
        competitor_id: int,
        metric_names: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get metrics for a competitor within a date range.
        
        Args:
            competitor_id: ID of the competitor
            metric_names: List of metric names to retrieve
            start_date: Start date for metrics
            end_date: End date for metrics
            
        Returns:
            Dictionary of metrics data
        """
        result = await self.db.execute(
            select(CompetitorMetrics).where(
                and_(
                    CompetitorMetrics.competitor_id == competitor_id,
                    CompetitorMetrics.metric_type.in_(metric_names),
                    CompetitorMetrics.start_date >= start_date,
                    CompetitorMetrics.end_date <= end_date
                )
            ).order_by(CompetitorMetrics.metric_date)
        )
        
        metrics = result.scalars().all()
        
        # Group metrics by type
        grouped_metrics = {}
        for metric in metrics:
            if metric.metric_type not in grouped_metrics:
                grouped_metrics[metric.metric_type] = []
            
            grouped_metrics[metric.metric_type].append({
                "date": metric.metric_date.isoformat(),
                "value": metric.value,
                "confidence": metric.confidence_score
            })
        
        # Add empty arrays for missing metrics
        for name in metric_names:
            if name not in grouped_metrics:
                grouped_metrics[name] = []
        
        return grouped_metrics
    
    async def create_metric(self, metric: CompetitorMetrics) -> CompetitorMetrics:
        """Create a new competitor metric.
        
        Args:
            metric: Metric to create
            
        Returns:
            Created metric
        """
        self.db.add(metric)
        await self.db.commit()
        await self.db.refresh(metric)
        return metric
    
    async def create_metrics_batch(self, metrics: List[CompetitorMetrics]) -> List[CompetitorMetrics]:
        """Create multiple competitor metrics in batch.
        
        Args:
            metrics: List of metrics to create
            
        Returns:
            List of created metrics
        """
        self.db.add_all(metrics)
        await self.db.commit()
        
        for metric in metrics:
            await self.db.refresh(metric)
        
        return metrics
    
    async def get_latest_metric(
        self,
        competitor_id: int,
        metric_name: str
    ) -> Optional[CompetitorMetrics]:
        """Get the latest metric for a competitor.
        
        Args:
            competitor_id: ID of the competitor
            metric_name: Name of the metric
            
        Returns:
            Latest metric if found, None otherwise
        """
        result = await self.db.execute(
            select(CompetitorMetrics)
            .where(
                and_(
                    CompetitorMetrics.competitor_id == competitor_id,
                    CompetitorMetrics.metric_type == metric_name
                )
            )
            .order_by(CompetitorMetrics.metric_date.desc())
            .limit(1)
        )
        
        return result.scalar_one_or_none()
