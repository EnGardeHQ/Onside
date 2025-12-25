from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from src.models.content import Content
from src.models.engagement import EngagementMetrics
from src.models.user import User

class CompetitiveAnalysisService:
    async def generate_competitive_report(
        self,
        user_id: str,
        competitor_ids: List[int],
        metrics: List[str],
        start_date: datetime,
        end_date: datetime,
        content_types: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Generate a competitive analysis report."""
        # Get user's content and metrics
        user_content = self._get_user_content(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            content_types=content_types,
            db=db
        )
        user_metrics = self._get_metrics_for_content(
            content_ids=[c.id for c in user_content],
            platforms=platforms,
            db=db
        )

        # Get competitors' content and metrics
        competitor_data = {}
        for competitor_id in competitor_ids:
            competitor_content = self._get_user_content(
                user_id=competitor_id,
                start_date=start_date,
                end_date=end_date,
                content_types=content_types,
                db=db
            )
            competitor_metrics = self._get_metrics_for_content(
                content_ids=[c.id for c in competitor_content],
                platforms=platforms,
                db=db
            )
            competitor_data[str(competitor_id)] = {
                "content": competitor_content,
                "metrics": competitor_metrics
            }

        # Calculate competitive metrics
        competitive_metrics = {}
        for competitor_id, data in competitor_data.items():
            competitive_metrics[competitor_id] = self._calculate_competitive_metrics(
                user_metrics=user_metrics,
                competitor_metrics=data["metrics"],
                metrics=metrics
            )

        return {
            "user_metrics": self._calculate_metrics_summary(user_metrics, metrics),
            "competitor_metrics": competitive_metrics,
            "date_range": {
                "start": start_date,
                "end": end_date
            }
        }

    def _get_user_content(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        content_types: Optional[List[str]],
        db: AsyncSession
    ) -> List[Content]:
        """Get user's content within the specified date range."""
        query = db.query(Content).filter(
            Content.user_id == user_id,
            Content.created_at.between(start_date, end_date)
        )
        
        if content_types:
            query = query.filter(Content.content_type.in_(content_types))
        
        return query.all()

    def _get_metrics_for_content(
        self,
        content_ids: List[int],
        platforms: Optional[List[str]],
        db: AsyncSession
    ) -> List[EngagementMetrics]:
        """Get metrics for the specified content IDs."""
        query = db.query(EngagementMetrics).filter(
            EngagementMetrics.content_id.in_(content_ids)
        )
        
        if platforms:
            query = query.filter(EngagementMetrics.source.in_(platforms))
        
        return query.all()

    def _calculate_competitive_metrics(
        self,
        user_metrics: List[EngagementMetrics],
        competitor_metrics: List[EngagementMetrics],
        metrics: List[str]
    ) -> Dict[str, Any]:
        """Calculate competitive metrics comparison."""
        result = {}
        
        # Group metrics by type
        user_metrics_by_type = defaultdict(list)
        competitor_metrics_by_type = defaultdict(list)
        
        for metric in user_metrics:
            user_metrics_by_type[metric.metric_type].append(metric.value)
        
        for metric in competitor_metrics:
            competitor_metrics_by_type[metric.metric_type].append(metric.value)
        
        # Calculate metrics
        for metric_type in metrics:
            user_values = user_metrics_by_type.get(metric_type, [])
            competitor_values = competitor_metrics_by_type.get(metric_type, [])
            
            result[metric_type] = {
                "total": sum(competitor_values),
                "average": sum(competitor_values) / len(competitor_values) if competitor_values else 0,
                "comparison": {
                    "difference": (
                        sum(competitor_values) - sum(user_values)
                        if user_values and competitor_values else 0
                    ),
                    "percentage": (
                        ((sum(competitor_values) / sum(user_values)) - 1) * 100
                        if user_values and sum(user_values) > 0 else 0
                    )
                }
            }
        
        return result

    def _calculate_metrics_summary(
        self,
        metrics: List[EngagementMetrics],
        metric_types: List[str]
    ) -> Dict[str, Any]:
        """Calculate summary metrics for a list of engagement metrics."""
        summary = {}
        metrics_by_type = defaultdict(list)
        
        for metric in metrics:
            metrics_by_type[metric.metric_type].append(metric.value)
        
        for metric_type in metric_types:
            values = metrics_by_type.get(metric_type, [])
            summary[metric_type] = {
                "total": sum(values),
                "average": sum(values) / len(values) if values else 0
            }
        
        return summary
