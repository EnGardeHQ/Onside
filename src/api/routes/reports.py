from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from src.database.config import get_db
from src.auth.security import get_current_user
from src.models.user import User
from src.models.content import Content
from src.models.engagement import EngagementMetrics
from src.services.analytics import AnalyticsService
from src.services.competitive_analysis import CompetitiveAnalysisService
from pydantic import BaseModel, constr
from collections import defaultdict

router = APIRouter(tags=["reports"])

class TimeframeEnum(str):
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"
    YEAR = "1y"

@router.get("/kpi", response_model=Dict[str, Any])
async def generate_kpi_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    platforms: str = Query(default=""),
    metrics: str = Query(default="engagement,reach,conversion"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Parse platforms and metrics
        platform_list = [p.strip() for p in platforms.split(",")] if platforms else []
        metric_list = [m.strip() for m in metrics.split(",")] if metrics else []

        # Parse dates if provided
        if start_date:
            parsed_start_date = datetime.fromisoformat(start_date)
            if not parsed_start_date.tzinfo:
                parsed_start_date = parsed_start_date.replace(tzinfo=timezone.utc)
        else:
            parsed_start_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        if end_date:
            parsed_end_date = datetime.fromisoformat(end_date)
            if not parsed_end_date.tzinfo:
                parsed_end_date = parsed_end_date.replace(tzinfo=timezone.utc)
        else:
            parsed_end_date = datetime.now(timezone.utc)

        # Validate date range
        if parsed_end_date < parsed_start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )

        # Generate KPI report
        report = {
            "metrics": {
                "engagement": {"total": 0, "average": 0.0, "trend": []},
                "reach": {"total": 0, "average": 0.0, "trend": []},
                "conversion": {"total": 0, "average": 0.0, "trend": []},
                "share_of_voice": {"total": 0, "average": 0.0, "trend": []}
            },
            "date_range": {
                "start": parsed_start_date.isoformat(),
                "end": parsed_end_date.isoformat()
            },
            "content_count": 0,
            "platforms": platform_list
        }

        # Query content items
        content_query = db.query(Content)
        if content_type:
            content_query = content_query.filter(Content.content_type == content_type)
        if platform_list:
            # Filter content based on platform in metadata
            content_items = [
                content for content in content_query.all()
                if content.content_metadata and
                content.content_metadata.get('platform') in platform_list
            ]
        else:
            content_items = content_query.all()
        
        report["content_count"] = len(content_items)

        # Query engagement metrics
        metrics_query = db.query(EngagementMetrics)
        if content_items:
            metrics_query = metrics_query.filter(
                EngagementMetrics.content_id.in_([c.id for c in content_items])
            )
        engagement_metrics = metrics_query.all()

        # Group metrics by type
        metrics_by_type = defaultdict(list)
        for metric in engagement_metrics:
            metrics_by_type[metric.metric_type].append(metric)

        # Calculate totals and averages
        for metric_type in metric_list:
            if metric_type in metrics_by_type:
                values = [m.metric_value for m in metrics_by_type[metric_type]]
                report["metrics"][metric_type]["total"] = sum(values)
                report["metrics"][metric_type]["average"] = sum(values) / len(values) if values else 0

                # Calculate trend (last 7 days)
                trend_data = []
                current_date = parsed_start_date
                while current_date <= parsed_end_date:
                    next_date = current_date + timedelta(days=1)
                    day_metrics = [
                        m for m in metrics_by_type[metric_type]
                        if m.created_at and (
                            current_date <= m.created_at.replace(tzinfo=timezone.utc) < next_date
                        )
                    ]
                    trend_data.append({
                        "date": current_date.isoformat(),
                        "value": sum(m.metric_value for m in day_metrics)
                    })
                    current_date = next_date
                report["metrics"][metric_type]["trend"] = trend_data

        return report

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating KPI report: {str(e)}"
        )

@router.get("/competitive", response_model=Dict[str, Any])
def generate_competitive_report(
    competitor_ids: List[int] = Query(...),
    metrics: List[str] = Query(default=["engagement", "reach", "share_of_voice"]),
    timeframe: str = Query(default="30d"),
    content_types: List[str] = Query(default=[]),
    platforms: List[str] = Query(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Convert timeframe to start_date
    timeframe_days = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "1y": 365
    }.get(timeframe, 30)
    
    start_date = datetime.now(timezone.utc) - timedelta(days=timeframe_days)
    end_date = datetime.now(timezone.utc)
    
    # Initialize competitive analysis service
    competitive_service = CompetitiveAnalysisService(db)
    
    try:
        report_data = competitive_service.generate_report(
            user_id=current_user.id,
            competitor_ids=competitor_ids,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            content_types=content_types,
            platforms=platforms
        )
        return report_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
