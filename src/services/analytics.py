from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from src.models.content import Content
from src.models.engagement import EngagementMetrics
from collections import defaultdict

class AnalyticsService:
    def __init__(self, db: Session = None):
        self.db = db

    def generate_kpi_report(
        self,
        metrics: List[str],
        start_date: datetime,
        end_date: datetime,
        platforms: Optional[List[str]] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a KPI report based on content and engagement metrics."""
        # Initialize metrics dictionary
        metrics_data = {
            "engagement": {"total": 0, "average": 0.0, "trend": []},
            "reach": {"total": 0, "average": 0.0, "trend": []},
            "conversion": {"total": 0, "average": 0.0, "trend": []},
            "share_of_voice": {"total": 0, "average": 0.0, "trend": []}
        }

        # Query content items
        query = self.db.query(Content)
        if content_type:
            query = query.filter(Content.content_type == content_type)
        content_items = query.all()

        # Query engagement metrics
        query = self.db.query(EngagementMetrics)
        if platforms:
            query = query.filter(EngagementMetrics.platform.in_(platforms))
        engagement_metrics = query.all()

        # Group metrics by type
        metrics_by_type = defaultdict(list)
        for metric in engagement_metrics:
            metrics_by_type[metric.metric_type].append(metric)

        # Calculate totals and averages
        for metric_type in metrics:
            if metric_type in metrics_by_type:
                values = [m.value for m in metrics_by_type[metric_type]]
                metrics_data[metric_type]["total"] = sum(values)
                metrics_data[metric_type]["average"] = sum(values) / len(values) if values else 0

                # Calculate trend (last 7 days)
                trend_data = self._calculate_trend(
                    metrics_by_type[metric_type],
                    start_date,
                    end_date
                )
                metrics_data[metric_type]["trend"] = trend_data

        return {
            "metrics": metrics_data,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "content_count": len(content_items),
            "platforms": platforms or []
        }

    def _calculate_trend(
        self,
        metrics: List[EngagementMetrics],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Calculate trend data for a set of metrics."""
        trend_data = []
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            day_metrics = [
                m for m in metrics
                if current_date <= m.timestamp < next_date
            ]
            trend_data.append({
                "date": current_date.isoformat(),
                "value": sum(m.value for m in day_metrics)
            })
            current_date = next_date
        return trend_data
