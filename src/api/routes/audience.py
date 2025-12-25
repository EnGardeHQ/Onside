from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from src.database.config import get_db
from src.auth.security import get_current_user
from src.models.user import User
from src.models.content import Content
from src.models.engagement import EngagementMetrics
from src.services.ai.audience_intelligence import AudienceIntelligenceService
import pytz

router = APIRouter(prefix="/api/audience", tags=["audience"])

@router.get("/insights", response_model=Dict[str, Any])
async def get_audience_insights(
    start_date: Optional[str] = Query(None, description="Start date in ISO format"),
    end_date: Optional[str] = Query(None, description="End date in ISO format"),
    content_type: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Default to last 30 days if no dates provided
    if not start_date:
        start_date_dt = datetime.now(timezone.utc) - timedelta(days=30)
    else:
        try:
            start_date_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)"
            )

    if not end_date:
        end_date_dt = datetime.now(timezone.utc)
    else:
        try:
            end_date_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)"
            )
        
    # Get user's content and engagement data
    content_query = db.query(Content).filter(
        Content.user_id == current_user.id,
        Content.created_at.between(start_date_dt, end_date_dt)
    )
    
    if content_type:
        content_query = content_query.filter(Content.content_type == content_type)
    
    content_items = content_query.all()
    content_ids = [content.id for content in content_items]
    
    # Get engagement metrics
    engagement_query = db.query(EngagementMetrics).filter(
        EngagementMetrics.content_id.in_(content_ids)
    )
    
    if platform:
        engagement_query = engagement_query.filter(EngagementMetrics.source == platform)
    
    engagement_metrics = engagement_query.all()
    
    # Generate insights using the service
    audience_service = AudienceIntelligenceService()
    insights = await audience_service.generate_insights(
        content_items,
        engagement_metrics,
        db
    )
    
    return {
        "time_period": {
            "start": start_date_dt,
            "end": end_date_dt
        },
        "insights": insights,
        "metadata": {
            "content_count": len(content_items),
            "platforms_analyzed": list(set(m.source for m in engagement_metrics)),
            "total_engagements": sum(m.value for m in engagement_metrics)
        }
    }

@router.get("/trends", response_model=Dict[str, Any])
async def get_audience_trends(
    lookback_days: int = Query(default=30, ge=1, le=365),
    content_type: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=lookback_days)
    
    print(f"Date range: {start_date} to {end_date}")
    
    # Get user's content and engagement data
    content_query = db.query(Content).filter(
        Content.user_id == current_user.id,
        Content.created_at.between(start_date, end_date)
    )
    
    if content_type:
        content_query = content_query.filter(Content.content_type == content_type)
    
    # Debug: Print the SQL query
    print(f"Content query: {content_query}")
    
    content_items = content_query.all()
    print(f"Found {len(content_items)} content items")
    for item in content_items:
        print(f"Content item: id={item.id}, created_at={item.created_at}")
    
    if not content_items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No audience data found for the specified time period"
        )
    
    content_ids = [content.id for content in content_items]
    
    # Get engagement metrics
    engagement_query = db.query(EngagementMetrics).filter(
        EngagementMetrics.content_id.in_(content_ids)
    )
    
    if platform:
        engagement_query = engagement_query.filter(EngagementMetrics.source == platform)
    
    engagement_metrics = engagement_query.all()
    print(f"Found {len(engagement_metrics)} engagement metrics")
    
    if not engagement_metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No audience data found for the specified time period"
        )
    
    # Analyze trends using the service
    audience_service = AudienceIntelligenceService()
    trends = await audience_service.analyze_trends(
        content_items,
        engagement_metrics,
        lookback_days,
        db
    )
    
    return {
        "time_period": {
            "start": start_date,
            "end": end_date
        },
        "trends": trends,
        "metadata": {
            "content_analyzed": len(content_items),
            "platforms": list(set(m.source for m in engagement_metrics)),
            "trend_confidence": trends.get("confidence", 0.0)
        }
    }
